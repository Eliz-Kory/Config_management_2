from typing import Dict, List, Set, Optional
import json


class DependencyGraphBuilder:
    def __init__(self, fetcher, filter_substring: Optional[str], root_package: str):
        self.fetcher = fetcher
        self.filter_substring = filter_substring.lower() if filter_substring else None
        self.root_package = root_package
        self.graph: Dict[str, List[str]] = {}
        self._visited: Set[str] = set()
        self._rec_stack: Set[str] = set()
        self.cycles: List[List[str]] = []

    def should_skip(self, package: str) -> bool:
        if not self.filter_substring:
            return False
        return self.filter_substring in package.lower()

    def dfs_build(self, package: str):
        if package in self._rec_stack:
            cycle = list(self._rec_stack) + [package]
            self.cycles.append(cycle)
            return
        if package in self._visited:
            return
        if self.should_skip(package):
            return

        self._visited.add(package)
        self._rec_stack.add(package)

        try:
            deps = self.fetcher.get_direct_dependencies(package)
        except Exception as e:
            print(f"⚠️  Ошибка получения зависимостей для {package}: {e}", file=sys.stderr)
            deps = []

        self.graph[package] = []
        for dep in deps:
            if self.should_skip(dep):
                continue
            self.graph[package].append(dep)
            self.dfs_build(dep)

        self._rec_stack.discard(package)

    def build(self) -> Dict[str, List[str]]:
        self._visited.clear()
        self._rec_stack.clear()
        self.cycles.clear()
        self.graph.clear()
        self.dfs_build(self.root_package)
        return self.graph

    def get_cycles(self) -> List[List[str]]:
        return self.cycles

    def dfs_postorder(self, package: str, visited: set, order: list):
        if package in visited or self.should_skip(package):
            return
        visited.add(package)
        for dep in self.graph.get(package, []):
            self.dfs_postorder(dep, visited, order)
        order.append(package)

    def get_install_order(self) -> List[str]:
        visited = set()
        order = []
        self.dfs_postorder(self.root_package, visited, order)
        return order

    def ascii_tree(self, package: str = None, prefix: str = "", is_last: bool = True, seen: set = None) -> List[str]:
        if seen is None:
            seen = set()
        if package is None:
            package = self.root_package
            lines = [f"{package}"]
            seen.add(package)
        else:
            connector = "└─ " if is_last else "├─ "
            lines = [f"{prefix}{connector}{package}"]
            seen.add(package)

        deps = self.graph.get(package, [])
        for i, dep in enumerate(deps):
            is_last_dep = (i == len(deps) - 1)
            new_prefix = prefix + ("   " if is_last else "│  ")
            if dep in seen:
                lines.append(f"{new_prefix}{'└─ ' if is_last_dep else '├─ '}{dep} (цикл)")
            else:
                lines.extend(self.ascii_tree(dep, new_prefix, is_last_dep, seen.copy()))
        return lines

    def to_mermaid(self) -> str:
        lines = ["graph TD"]
        edges = set()
        for pkg, deps in self.graph.items():
            for dep in deps:
                edge = (pkg, dep)
                if edge not in edges:
                    lines.append(f"    {pkg} --> {dep}")
                    edges.add(edge)
        return "\n".join(lines)

    def export_svg(self, path: str):
        from collections import deque
        levels = {}
        queue = deque([(self.root_package, 0)])
        visited = {self.root_package}
        while queue:
            pkg, lvl = queue.popleft()
            levels.setdefault(lvl, []).append(pkg)
            for dep in self.graph.get(pkg, []):
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, lvl + 1))
        coords = {}
        for lvl, pkgs in levels.items():
            y = 60 + lvl * 100
            for i, pkg in enumerate(pkgs):
                x = 100 + i * 180
                coords[pkg] = (x, y)
        svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600">',
            '<style>.node{fill:#4a90e2;stroke:#205090;stroke-width:2;} .label{fill:white;font:14px sans-serif;text-anchor:middle;}</style>',
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="10" refY="3" orient="auto">',
            '<path d="M0,0 L0,6 L9,3 z" fill="#555" /></marker></defs>'
        ]
        for pkg, deps in self.graph.items():
            x1, y1 = coords.get(pkg, (50, 50))
            for dep in deps:
                x2, y2 = coords.get(dep, (x1 + 100, y1 + 80))
                svg.append(f'<line x1="{x1}" y1="{y1+25}" x2="{x2}" y2="{y2-25}" '
                           'stroke="#555" marker-end="url(#arrow)" />')
        for pkg, (x, y) in coords.items():
            svg.append(f'<circle class="node" cx="{x}" cy="{y}" r="30"/>')
            svg.append(f'<text class="label" x="{x}" y="{y+5}">{pkg}</text>')
        svg.append('</svg>')
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))