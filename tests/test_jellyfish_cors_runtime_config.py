from __future__ import annotations

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

    assert "http://localhost:7790" in config_source
    assert "cors_origin_regex" in config_source
    assert "allow_origin_regex=settings.cors_origin_regex_value" in main_source
    assert "CORS_ORIGIN_REGEX" in env_example
    assert "http://localhost:7790" in compose_source


def test_frontend_runtime_config_defaults_to_jellyfish_backend_8011() -> None:
    runtime_config = (FRONT_DIR / "src" / "services" / "runtimeConfig.ts").read_text(encoding="utf-8")
    openapi_config = (FRONT_DIR / "src" / "services" / "openapi.ts").read_text(encoding="utf-8")
    http_config = (FRONT_DIR / "src" / "services" / "http.ts").read_text(encoding="utf-8")
    env_js = (FRONT_DIR / "public" / "env.js").read_text(encoding="utf-8")
    package_json = (FRONT_DIR / "package.json").read_text(encoding="utf-8")

    assert "DEFAULT_BACKEND_URL = 'http://localhost:8011'" in runtime_config
    assert "getBackendBaseUrl" in openapi_config
    assert "getApiBaseUrl" in http_config
    assert "http://localhost:8011" in env_js
    assert "http://127.0.0.1:8011" in package_json
