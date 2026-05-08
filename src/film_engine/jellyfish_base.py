from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


JELLYFISH_UPSTREAM_URL = "https://github.com/Forget-C/Jellyfish"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JELLYFISH_BASE_PATH = REPO_ROOT / "vendor" / "jellyfish"
JELLYFISH_FRONTEND_URL = "http://localhost:7788"
JELLYFISH_LOCAL_BACKEND_URL = "http://localhost:8011"
JELLYFISH_DOCKER_BACKEND_URL = "http://localhost:8000"


@dataclass
class JellyfishRunCommand:
    id: str
    label: str
    cwd: str
    command: str
    ports: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "cwd": self.cwd,
            "command": self.command,
            "ports": dict(self.ports),
            "notes": list(self.notes),
        }


@dataclass
class JellyfishBaseStatus:
    path: str
    upstream_url: str
    available: bool
    initialized: bool
    commit: str | None = None
    branch: str | None = None
    remote_url: str | None = None
    docker_compose_file: str | None = None
    backend_dir: str | None = None
    frontend_dir: str | None = None
    site_dir: str | None = None
    ports: dict[str, str] = field(default_factory=dict)
    run_commands: list[JellyfishRunCommand] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def compose_ready(self) -> bool:
        return self.docker_compose_file is not None and not self.missing

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "upstream_url": self.upstream_url,
            "available": self.available,
            "initialized": self.initialized,
            "commit": self.commit,
            "branch": self.branch,
            "remote_url": self.remote_url,
            "docker_compose_file": self.docker_compose_file,
            "backend_dir": self.backend_dir,
            "frontend_dir": self.frontend_dir,
            "site_dir": self.site_dir,
            "compose_ready": self.compose_ready,
            "ports": dict(self.ports),
            "run_commands": [command.as_dict() for command in self.run_commands],
            "missing": list(self.missing),
            "notes": list(self.notes),
        }


def inspect_jellyfish_base(
    base_path: str | Path | None = None,
) -> JellyfishBaseStatus:
    path = Path(base_path) if base_path is not None else DEFAULT_JELLYFISH_BASE_PATH
    rel_path = _relative_to_repo(path)

    expected = {
        "deploy/compose/docker-compose.yml": path / "deploy" / "compose" / "docker-compose.yml",
        "deploy/compose/.env.example": path / "deploy" / "compose" / ".env.example",
        "backend/pyproject.toml": path / "backend" / "pyproject.toml",
        "front/package.json": path / "front" / "package.json",
    }
    missing = [name for name, item_path in expected.items() if not item_path.exists()]
    available = path.exists() and not missing
    initialized = path.exists() and (_git(path, "rev-parse", "--is-inside-work-tree") == "true")

    docker_compose_file = _optional_rel(expected["deploy/compose/docker-compose.yml"])
    backend_dir = _optional_rel(path / "backend")
    frontend_dir = _optional_rel(path / "front")
    site_dir = _optional_rel(path / "site")

    ports = {
        "frontend": JELLYFISH_FRONTEND_URL,
        "backend": JELLYFISH_LOCAL_BACKEND_URL,
        "backend_docs": f"{JELLYFISH_LOCAL_BACKEND_URL}/docs",
        "docker_backend": JELLYFISH_DOCKER_BACKEND_URL,
        "docker_backend_docs": f"{JELLYFISH_DOCKER_BACKEND_URL}/docs",
        "mysql": "localhost:${MYSQL_PORT:-3306}",
        "redis": "localhost:${REDIS_PORT:-6379}",
        "rustfs": "http://localhost:${RUSTFS_PORT:-9000}",
    }
    run_commands = _run_commands(rel_path)
    notes = [
        "Jellyfish is tracked as the studio OS base. LuminAI stays runtime-neutral below the platform boundary.",
        "Local dev uses backend port 8011 so an existing service on 8000 does not shadow the Film Core API.",
        "Use port overrides if local Redis or MySQL is already bound on default ports.",
    ]
    if missing:
        notes.append("Initialize submodules before running Jellyfish: git submodule update --init --recursive.")

    return JellyfishBaseStatus(
        path=rel_path,
        upstream_url=JELLYFISH_UPSTREAM_URL,
        available=available,
        initialized=initialized,
        commit=_git(path, "rev-parse", "--short", "HEAD") if path.exists() else None,
        branch=_git(path, "rev-parse", "--abbrev-ref", "HEAD") if path.exists() else None,
        remote_url=_git(path, "config", "--get", "remote.origin.url") if path.exists() else None,
        docker_compose_file=docker_compose_file,
        backend_dir=backend_dir,
        frontend_dir=frontend_dir,
        site_dir=site_dir,
        ports=ports,
        run_commands=run_commands,
        missing=missing,
        notes=notes,
    )


def _run_commands(rel_path: str) -> list[JellyfishRunCommand]:
    return [
        JellyfishRunCommand(
            id="docker_compose",
            label="Docker Compose studio stack",
            cwd=rel_path,
            command=(
                "MYSQL_PORT=3337 REDIS_PORT=6384 RUSTFS_PORT=9010 "
                "RUSTFS_CONSOLE_PORT=9011 docker compose --env-file "
                "deploy/compose/.env.example -f deploy/compose/docker-compose.yml "
                "up -d --build"
            ),
            ports={
                "frontend": JELLYFISH_FRONTEND_URL,
                "backend": JELLYFISH_DOCKER_BACKEND_URL,
                "backend_docs": f"{JELLYFISH_DOCKER_BACKEND_URL}/docs",
            },
            notes=[
                "This starts Jellyfish frontend, backend, MySQL, Redis, RustFS, and worker services.",
                "The command uses alternate infra ports to avoid common local conflicts.",
            ],
        ),
        JellyfishRunCommand(
            id="backend_dev",
            label="Backend local dev",
            cwd=f"{rel_path}/backend",
            command=(
                "cp .env.example .env && uv sync && "
                "uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8011"
            ),
            ports={"backend": JELLYFISH_LOCAL_BACKEND_URL, "backend_docs": f"{JELLYFISH_LOCAL_BACKEND_URL}/docs"},
        ),
        JellyfishRunCommand(
            id="frontend_dev",
            label="Frontend local dev",
            cwd=f"{rel_path}/front",
            command="pnpm install && pnpm dev --host 0.0.0.0",
            ports={"frontend": JELLYFISH_FRONTEND_URL},
        ),
    ]


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _optional_rel(path: Path) -> str | None:
    if path.exists():
        return _relative_to_repo(path)
    return None


def _relative_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the Jellyfish studio base checkout.")
    parser.add_argument("--base-path", default=None)
    args = parser.parse_args(argv)
    status = inspect_jellyfish_base(args.base_path)
    print(json.dumps(status.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
