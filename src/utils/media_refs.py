from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse


def _project_root(project_root: str | Path | None = None) -> Path:
    return Path(project_root).resolve() if project_root else Path.cwd().resolve()


def is_remote_media_ref(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "blob"}


def is_data_uri(value: str | None) -> bool:
    return bool(value and value.startswith("data:"))


def is_stable_project_media_ref(value: str | None) -> bool:
    return classify_media_ref(value) in {"local_path", "object_key"}


def classify_media_ref(value: str | None) -> str:
    if not value:
        return "empty"
    if is_data_uri(value):
        return "data_uri"
    if is_remote_media_ref(value):
        return "remote_url"
    if value.startswith("oss://"):
        return "object_key"

    oss_base = os.getenv("OSS_BASE_PATH", "").strip("/")
    if oss_base and value.strip("/").startswith(f"{oss_base}/"):
        return "object_key"
    if value.startswith(("lumenx/", "dashscope-temp/")):
        return "object_key"

    return "local_path"


def resolve_local_media_path(value: str, project_root: str | Path | None = None) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path.resolve())
    root = _project_root(project_root)
    if path.parts and path.parts[0] == "output":
        return str((root / path).resolve())
    return str((root / "output" / path).resolve())
