"""CORS regression tests for the local Jellyfish/LuminAI dev topology."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient

from app.api.v1.routes.film import task_status as task_status_route
from app.api.v1.routes.studio import projects as projects_route
from app.config import settings
from app.dependencies import get_db
from app.main import app


async def _empty_db() -> AsyncGenerator[object, None]:
    yield object()


def _cors_headers(origin: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }


def test_backend_cors_allows_local_jellyfish_frontend_ports(client: TestClient) -> None:
    assert "http://localhost:24732" in settings.cors_origins_list
    assert settings.cors_origin_regex_value is not None

    response = client.options(
        "/api/v1/studio/projects",
        headers=_cors_headers("http://localhost:24732"),
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:24732"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_reported_studio_projects_request_keeps_cors_header(
    client: TestClient,
    monkeypatch,
) -> None:
    async def _empty_paginate(*_args, **_kwargs):
        return [], 0

    monkeypatch.setattr(projects_route, "paginate", _empty_paginate)
    app.dependency_overrides[get_db] = _empty_db
    try:
        response = client.get(
            "/api/v1/studio/projects",
            headers={"Origin": "http://localhost:24732"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:24732"
    assert response.json()["data"]["items"] == []


def test_reported_film_tasks_request_keeps_cors_header(
    client: TestClient,
    monkeypatch,
) -> None:
    class _EmptyTaskStore:
        def __init__(self, _db: object) -> None:
            pass

        async def list_task_views(self, **_kwargs):
            return [], 0

    monkeypatch.setattr(task_status_route, "SqlAlchemyTaskStore", _EmptyTaskStore)
    app.dependency_overrides[get_db] = _empty_db
    try:
        response = client.get(
            "/api/v1/film/tasks?recent_seconds=15&page=1&page_size=50",
            headers={"Origin": "http://localhost:24732"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:24732"
    assert response.json()["data"]["items"] == []
