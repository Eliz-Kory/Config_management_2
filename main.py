import sys
import argparse
from pathlib import Path

try:
    import tomllib  
except ImportError:
    import tomli as tomllib

from nuget_fetcher import NuGetFetcher


def load_and_validate_config(path: Path):
    try:
        with open(path, "rb") as f:
            cfg = tomllib.load(f)
    except FileNotFoundError:
        raise ValueError(f"Файл конфигурации не найден: {path}")

    required = ["package_name", "repository_url", "repo_mode"]
    for key in required:
        if key not in cfg:
            raise ValueError(f"Отсутствует обязательный параметр: {key}")
   
    if not isinstance(cfg["package_name"], str) or not cfg["package_name"].strip():
        raise ValueError("package_name должен быть непустой строкой")
    if cfg["repo_mode"] not in ("online", "offline"):
        raise ValueError("repo_mode должен быть 'online' или 'offline'")

    return cfg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_and_validate_config(config_path)

    package = config["package_name"]
    repo_url = config["repository_url"]
    mode = config["repo_mode"]

    if mode != "online":
        print("Этап 2 поддерживает пока только режим 'online'", file=sys.stderr)
        sys.exit(1)

    print(f"Сбор прямых зависимостей для пакета: {package}")
    print(f"Репозиторий: {repo_url}")

    try:
        fetcher = NuGetFetcher(repo_url)
        deps = fetcher.get_direct_dependencies(package)

        if not deps:
            print("Прямых зависимостей не найдено.")
        else:
            print(f"\n✅ Прямые зависимости ({len(deps)}):")
            for i, (dep_id, version) in enumerate(deps, 1):
                print(f"{i:2}. {dep_id} = {version}")

    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(2)



if __name__ == "__main__":
    main()