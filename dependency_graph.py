# dependency_graph.py
from typing import Dict, List, Set, Tuple, Optional
import json
from nuget_fetcher import NuGetFetcher  # для online-режима


class DependencyGraphBuilder:
    def __init__(
        self,
        fetcher,
        filter_substring: Optional[str] = None
    ):
        self.fetcher = fetcher
        self.filter_substring = filter_substring.lower() if filter_substring else None
        self.graph: Dict[str, List[str]] = {}
        self._visited: Set[str] = set()
        self._rec_stack: Set[str] = set()
        self.cycles: List[List[str]] = []

    def should_skip(self, package: str) -> bool:
        if not self.filter_substring:
            return False
        return self.filter_substring in package.lower()

    def get_dependencies(self, package: str) -> List[str]:
        """Абстрактный интерфейс — в реализациях будет online/offline."""
        return self.fetcher.get_direct_dependencies(package)

    def dfs(self, package: str) -> None:
        if package in self._rec_stack:
            # Цикл обнаружен! Восстанавливаем путь
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
            deps = self.get_dependencies(package)
        except Exception as e:
            print(f"Не удалось получить зависимости для {package}: {e}")
            deps = []

        self.graph[package] = []

        for dep in deps:
            dep_id = dep if isinstance(dep, str) else dep[0]  # offline даёт str, online — (id, version)
            if self.should_skip(dep_id):
                continue
            self.graph[package].append(dep_id)
            self.dfs(dep_id)

        self._rec_stack.discard(package)

    def build(self, root_package: str) -> Dict[str, List[str]]:
        self._visited.clear()
        self._rec_stack.clear()
        self.cycles.clear()
        self.graph.clear()

        self.dfs(root_package)
        return self.graph

    def get_cycles(self) -> List[List[str]]:
        return self.cycles