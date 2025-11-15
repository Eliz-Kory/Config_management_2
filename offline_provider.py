import json
from pathlib import Path
from typing import List


class OfflineTestProvider:
    def __init__(self, repo_path: str):
        p = Path(repo_path)
        if not p.is_file():
            raise ValueError(f"Тестовый репозиторий не найден: {p}")
        with open(p, "r", encoding="utf-8") as f:
            self.repo = json.load(f)

    def get_direct_dependencies(self, package_id: str) -> List[str]:
        if package_id not in self.repo:
            raise RuntimeError(f"Пакет '{package_id}' отсутствует в тестовом репозитории")
        return self.repo[package_id]