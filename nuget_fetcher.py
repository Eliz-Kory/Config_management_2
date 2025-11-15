import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
from typing import List, Tuple, Optional


class NuGetFetcher:
    def __init__(self, service_index_url: str):
        self.service_index_url = service_index_url
        self._service_endpoints = None

    def _fetch_json(self, url: str):
        try:
            req = Request(url, headers={"User-Agent": "PackageDepVisualizer/1.0"})
            with urlopen(req, timeout=10) as response:
                return json.load(response)
        except (URLError, HTTPError, ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Ошибка загрузки JSON: {url} → {e}")

    def _get_service_endpoint(self, resource_type: str) -> str:
        if self._service_endpoints is None:
            data = self._fetch_json(self.service_index_url)
            self._service_endpoints = {
                res["@type"]: res["@id"] for res in data.get("resources", [])
            }
        if resource_type == "RegistrationsBaseUrl":
            return self._service_endpoints.get("RegistrationsBaseUrl")
        return self._service_endpoints.get(resource_type)

    def get_package_metadata(self, package_id: str) -> dict:
        reg_base = self._get_service_endpoint("RegistrationsBaseUrl")
        if not reg_base:
            raise RuntimeError("RegistrationsBaseUrl не найден в index.json")
        reg_url = f"{reg_base.rstrip('/')}/{package_id.lower()}/index.json"
        return self._fetch_json(reg_url)

    def get_latest_stable_version(self, package_id: str) -> str:
        meta = self.get_package_metadata(package_id)
        versions = []
        for page in meta.get("items", []):
            for item in page.get("items", []):
                cat = item.get("catalogEntry", {})
                version = cat.get("version")
                is_prerelease = cat.get("isPrerelease", False)
                if version and not is_prerelease:
                    versions.append(version)
        if not versions:
            raise RuntimeError(f"Нет стабильных версий для {package_id}")
        return max(versions, key=lambda v: [int(x) if x.isdigit() else 0 for x in v.split(".")[:3]])

    def download_nupkg(self, package_id: str, version: str, output_path: str):
        pkg_base = self._get_service_endpoint("PackageBaseAddress/3.0.0")
        if not pkg_base:
            raise RuntimeError("PackageBaseAddress/3.0.0 не найден")
        url = f"{pkg_base.rstrip('/')}/{package_id.lower()}/{version.lower()}/{package_id.lower()}.{version.lower()}.nupkg"
        try:
            req = Request(url, headers={"User-Agent": "PackageDepVisualizer/1.0"})
            with urlopen(req, timeout=20) as response, open(output_path, "wb") as f:
                f.write(response.read())
        except (URLError, HTTPError) as e:
            raise RuntimeError(f"Ошибка скачивания {url}: {e}")

    def extract_dependencies_from_nuspec(self, nuspec_path: str) -> List[str]:
        try:
            tree = ET.parse(nuspec_path)
            root = tree.getroot()
            ns = {"ns": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"}
            deps = []
            for dep in root.findall(".//ns:dependency", ns):
                dep_id = dep.get("id")
                if dep_id:
                    deps.append(dep_id)
            return deps
        except ET.ParseError as e:
            raise RuntimeError(f"Ошибка парсинга XML: {e}")

    def get_direct_dependencies(self, package_id: str) -> List[str]:
        version = self.get_latest_stable_version(package_id)
        with tempfile.TemporaryDirectory() as tmpdir:
            nupkg_path = os.path.join(tmpdir, f"{package_id}.{version}.nupkg")
            self.download_nupkg(package_id, version, nupkg_path)
            with zipfile.ZipFile(nupkg_path, "r") as zf:
                nuspec_files = [f for f in zf.namelist() if f.endswith(".nuspec")]
                if not nuspec_files:
                    raise RuntimeError("Файл .nuspec не найден в .nupkg")
                nuspec_name = nuspec_files[0]
                zf.extract(nuspec_name, tmpdir)
                return self.extract_dependencies_from_nuspec(os.path.join(tmpdir, nuspec_name))