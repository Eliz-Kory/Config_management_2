import json
from pathlib import Path
from typing import List, Tuple


class OfflineTestProvider:
    def __init__(self, repo_path: str):
        repo_path = Path(repo_path)
        if not repo_path.is_file():
            raise ValueError(f"Тестовый репозиторий не найден: {repo_path}")
        with open(repo_path, "r", encoding="utf-8") as f:
            self.repo = json.load(f)

    def get_direct_dependencies(self, package_id: str) -> List[str]:
        if package_id not in self.repo:
            raise RuntimeError(f"Пакет '{package_id}' отсутствует в тестовом репозитории")
        return self.repo[package_id]  # возвращает список строк, например: ["B", "C"]