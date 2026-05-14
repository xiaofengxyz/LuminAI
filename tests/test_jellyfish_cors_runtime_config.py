from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "vendor" / "jellyfish" / "backend"
FRONT_DIR = REPO_ROOT / "vendor" / "jellyfish" / "front"


def test_backend_cors_config_allows_local_jellyfish_frontend_ports() -> None:
    config_source = (BACKEND_DIR / "app" / "config.py").read_text(encoding="utf-8")
    main_source = (BACKEND_DIR / "app" / "main.py").read_text(encoding="utf-8")
    env_example = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")
    compose_source = (REPO_ROOT / "vendor" / "jellyfish" / "deploy" / "compose" / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "http://localhost:24732" in config_source
    assert "cors_origin_regex" in config_source
    assert "allow_origin_regex=settings.cors_origin_regex_value" in main_source
    assert "CORS_ORIGIN_REGEX" in env_example
    assert "http://localhost:24732" in compose_source


def test_frontend_runtime_config_defaults_to_jellyfish_backend_24731() -> None:
    runtime_config = (FRONT_DIR / "src" / "services" / "runtimeConfig.ts").read_text(encoding="utf-8")
    openapi_config = (FRONT_DIR / "src" / "services" / "openapi.ts").read_text(encoding="utf-8")
    http_config = (FRONT_DIR / "src" / "services" / "http.ts").read_text(encoding="utf-8")
    env_js = (FRONT_DIR / "public" / "env.js").read_text(encoding="utf-8")
    package_json = json.loads((FRONT_DIR / "package.json").read_text(encoding="utf-8"))

    assert "DEFAULT_BACKEND_URL = 'http://127.0.0.1:24731'" in runtime_config
    assert "getBackendBaseUrl" in openapi_config
    assert "getApiBaseUrl" in http_config
    assert "http://127.0.0.1:24731" in env_js
    assert "http://127.0.0.1:24731" in package_json["scripts"]["openapi:fetch"]
    assert "NO_PROXY=localhost,127.0.0.1,::1" in package_json["scripts"]["openapi:fetch"]
    assert package_json["scripts"]["dev:film-core"] == "vite --host 0.0.0.0 --port 24732"


def test_jellyfish_film_core_start_script_bypasses_local_proxy() -> None:
    script_source = (REPO_ROOT / "scripts" / "start_jellyfish_film_core.sh").read_text(encoding="utf-8")

    assert "NO_PROXY" in script_source
    assert "curl --noproxy" in script_source
    assert "BACKEND_PORT=\"${BACKEND_PORT:-24731}\"" in script_source
    assert "FRONT_PORT=\"${FRONT_PORT:-24732}\"" in script_source
    assert "source \"$ROOT_DIR/.env\"" in script_source


def test_project_lobby_keeps_film_core_discoverable_without_projects() -> None:
    lobby_source = (FRONT_DIR / "src" / "pages" / "aiStudio" / "project" / "ProjectLobby.tsx").read_text(
        encoding="utf-8"
    )

    assert "handleOpenFilmCoreEntry" in lobby_source
    assert "handleOpenCreate" in lobby_source
    assert "创建 AI 漫剧" in lobby_source
    assert "上传小说文件" in lobby_source
    assert "creation_mode" in lobby_source
    assert "Film Core 是项目级 overview" in lobby_source
    assert "disabled={!selectedProject}" not in lobby_source
