# main.py (этап 3)
import sys
import argparse
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from nuget_fetcher import NuGetFetcher
from offline_provider import OfflineTestProvider
from dependency_graph.py import DependencyGraphBuilder


def load_config(path: Path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def validate_config(cfg):
    required = ["package_name", "repository_url", "repo_mode"]
    for key in required:
        if key not in cfg:
            raise ValueError(f"Отсутствует '{key}' в конфигурации")
    if cfg["repo_mode"] not in ("online", "offline"):
        raise ValueError("repo_mode должен быть 'online' или 'offline'")
    return cfg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    cfg = validate_config(load_config(Path(args.config)))

    package = cfg["package_name"]
    repo_mode = cfg["repo_mode"]
    repo_url = cfg["repository_url"]
    filter_substring = cfg.get("filter_substring")

    print(f"Целевой пакет: {package}")
    print(f"Режим: {repo_mode}")
    if filter_substring:
        print(f"Фильтр: '{filter_substring}'")

    # Выбор провайдера
    if repo_mode == "online":
        print("Используется онлайн-репозиторий NuGet")
        fetcher = NuGetFetcher(repo_url)
    elif repo_mode == "offline":
        print(f"Используется тестовый репозиторий: {repo_url}")
        fetcher = OfflineTestProvider(repo_url)
    else:
        raise RuntimeError("Недопустимый режим")

    # Построение графа
    builder = DependencyGraphBuilder(fetcher, filter_substring)
    graph = builder.build(package)

    # Вывод графа
    print("\n✅ Построен граф зависимостей:")
    for pkg, deps in graph.items():
        if deps:
            print(f"  {pkg} → {', '.join(deps)}")
        else:
            print(f"  {pkg} → (лист)")

    # Циклы
    cycles = builder.get_cycles()
    if cycles:
        print(f"\n⚠️  Обнаружены циклические зависимости ({len(cycles)}):")
        for i, cycle in enumerate(cycles, 1):
            print(f"  {i}. {' → '.join(cycle)}")
    else:
        print("\n✅ Циклических зависимостей не обнаружено.")

    total_nodes = len(graph)
    total_edges = sum(len(deps) for deps in graph.values())
    print(f"\nСтатистика: {total_nodes} узлов, {total_edges} рёбер")


if __name__ == "__main__":
    main()