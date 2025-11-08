import sys
import os
import argparse
from pathlib import Path

try:
    import tomllib  
except ImportError:
    import tomli as tomllib


def load_config(config_path: str):
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ValueError(f"Конфигурационный файл не найден: {config_path}")
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Ошибка разбора TOML: {e}")


def validate_config(cfg):
    errors = []

    if not isinstance(cfg.get("package_name"), str) or not cfg["package_name"].strip():
        errors.append("❌ 'package_name' должен быть непустой строкой")

    url = cfg.get("repository_url")
    if not isinstance(url, str) or not url.strip():
        errors.append("❌ 'repository_url' должен быть непустой строкой")

    mode = cfg.get("repo_mode")
    if mode not in ("online", "offline"):
        errors.append("❌ 'repo_mode' должен быть 'online' или 'offline'")

    out_img = cfg.get("output_image")
    if not isinstance(out_img, str) or not out_img.strip():
        errors.append("❌ 'output_image' должен быть непустой строкой")
    elif not any(out_img.endswith(ext) for ext in (".png", ".svg", ".pdf", ".jpg")):
        print("⚠️  'output_image' не имеет типичного графического расширения — продолжаем, но проверьте.")

    if not isinstance(cfg.get("ascii_tree"), bool):
        errors.append("❌ 'ascii_tree' должен быть логическим значением (true/false)")

    filt = cfg.get("filter_substring")
    if filt is not None and not isinstance(filt, str):
        errors.append("❌ 'filter_substring' должен быть строкой или отсутствовать")

    if errors:
        raise ValueError("Ошибки в конфигурации:\n" + "\n".join(errors))


def print_config(cfg):
    print("✅ Параметры конфигурации:")
    for key, value in cfg.items():
        print(f"  {key} = {repr(value)}")


def main():
    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей пакетов")
    parser.add_argument(
        "--config",
        "-c",
        default="config.toml",
        help="Путь к конфигурационному файлу (по умолчанию: config.toml)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"Ошибка: файл {config_path} не существует.", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_config(config_path)
        validate_config(config)
        print_config(config)
        print("\n🎉 Этап 1: конфигурация загружена и проверена успешно.")
    except ValueError as e:
        print(f"❌ Ошибка конфигурации:\n{e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()