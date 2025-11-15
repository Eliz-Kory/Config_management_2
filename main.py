import sys
import argparse
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from dependency_graph import DependencyGraphBuilder
from offline_provider import OfflineTestProvider
from nuget_fetcher import NuGetFetcher


def load_config(path: Path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ValueError(f"Файл конфигурации не найден: {path}")
    except Exception as e:
        raise ValueError(f"Ошибка чтения конфигурации: {e}")


def main():
    parser = argparse.ArgumentParser(description="Визуализатор зависимостей пакетов")
    parser.add_argument("-c", "--config", default="config.toml", help="Путь к config.toml")
    parser.add_argument("--install-order", action="store_true", help="Вывести порядок установки")
    parser.add_argument("--tree", action="store_true", help="Вывести ASCII-дерево (игнорирует ascii_tree в конфиге)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    package = cfg["package_name"]
    repo_mode = cfg["repo_mode"]
    repo_url = cfg["repository_url"]
    filter_substring = cfg.get("filter_substring")
    output_image = cfg.get("output_image", "graph.svg")
    ascii_tree_enabled = cfg.get("ascii_tree", False)

    # Выбор провайдера
    if repo_mode == "online":
        fetcher = NuGetFetcher(repo_url)
    elif repo_mode == "offline":
        fetcher = OfflineTestProvider(repo_url)
    else:
        print(f"❌ Недопустимый repo_mode: {repo_mode}", file=sys.stderr)
        sys.exit(1)

    builder = DependencyGraphBuilder(fetcher, filter_substring, package)

    print(f"Целевой пакет: {package}")
    print(f"Режим: {repo_mode}")
    if filter_substring:
        print(f"Фильтр: '{filter_substring}'")

    graph = builder.build()

    # Вывод графа
    print("\n✅ Граф зависимостей:")
    for pkg in sorted(graph.keys()):
        deps = graph[pkg]
        print(f"  {pkg} → [{', '.join(deps) if deps else ''}]")

    # Циклы
    cycles = builder.get_cycles()
    if cycles:
        print(f"\n⚠️  Обнаружены циклы ({len(cycles)}):")
        for i, cycle in enumerate(cycles, 1):
            print(f"  {i}. {' → '.join(cycle)}")
    else:
        print("\n✅ Циклов нет.")

    # Порядок установки
    if args.install_order:
        order = builder.get_install_order()
        print(f"\nПорядок установки (DFS-postorder, всего {len(order)} пакетов):")
        for i, p in enumerate(order, 1):
            print(f"{i:2}. {p}")

    # ASCII-дерево
    show_tree = args.tree or ascii_tree_enabled
    if show_tree:
        print("\nASCII-дерево:")
        lines = builder.ascii_tree()
        for line in lines:
            print(line)

    # Mermaid
    mermaid = builder.to_mermaid()
    print("\nMermaid-код:")
    print(mermaid)

    # SVG
    try:
        builder.export_svg(output_image)
        print(f"\n✅ SVG сохранён: {output_image}")
    except Exception as e:
        print(f"\n❌ Не удалось сохранить SVG: {e}", file=sys.stderr)

    print("\nЭтапы 1–5 завершены.")


if __name__ == "__main__":
    main()