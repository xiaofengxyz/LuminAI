"""统一 Celery 执行入口。

职责：
- Celery 统一只接收业务 task_id；
- 通过 GenerationTask.task_kind + registry 找到具体 WorkerTaskExecutor；
- 回写 executor_type / executor_task_id，便于排障。
"""

from __future__ import annotations

import logging
from threading import Thread
from types import SimpleNamespace
from typing import Any

from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.db_sync import sync_session_maker
from app.models.task import GenerationTask
from app.services.worker.task_registry import task_executor_registry

logger = logging.getLogger(__name__)


def _record_executor_dispatch(task_id: str, *, executor_type: str, executor_task_id: str | None) -> None:
    """Persist the execution backend chosen for a task.

    This small helper is shared by Celery dispatch, local fallback, and
    external-runtime handoff paths so task-center diagnostics stay consistent.
    """

    with sync_session_maker() as db:
        row = db.get(GenerationTask, task_id)
        if row is None:
            return
        row.executor_type = executor_type
        row.executor_task_id = executor_task_id
        db.commit()


def enqueue_task_execution(task_id: str) -> AsyncResult:
    async_result = run_task_celery.delay(task_id)
    _record_executor_dispatch(
        task_id,
        executor_type="celery",
        executor_task_id=async_result.id,
    )
    return async_result


def _run_inline_fallback(task_id: str) -> None:
    """Execute a task in the current backend process after broker dispatch fails."""

    try:
        run_task_celery(task_id)
    except Exception:  # noqa: BLE001
        logger.exception("inline fallback task execution failed: task_id=%s", task_id)


def enqueue_task_execution_best_effort(
    task_id: str,
    *,
    inline_fallback: bool = False,
) -> Any:
    """Dispatch through Celery, but keep local development recoverable.

    Redis/Celery is the production execution path.  In a single-process local
    run, however, Redis is often absent; failing the HTTP request at dispatch
    time makes storyboard extraction and Motion submit look broken.  This
    wrapper records the failed dispatch and either starts an inline background
    fallback or leaves the task pending for a worker/external runtime.
    """

    try:
        return enqueue_task_execution(task_id)
    except Exception as exc:  # noqa: BLE001
        executor_type = "inline_fallback" if inline_fallback else "pending_worker"
        _record_executor_dispatch(task_id, executor_type=executor_type, executor_task_id=None)
        logger.warning(
            "celery dispatch failed; task kept recoverable: task_id=%s executor_type=%s error=%s",
            task_id,
            executor_type,
            exc,
        )
        if inline_fallback:
            Thread(target=_run_inline_fallback, args=(task_id,), daemon=True).start()
        return SimpleNamespace(id=f"{executor_type}:{task_id}", fallback=True)


def mark_task_external_runtime(task_id: str, *, provider: str) -> None:
    """Record that a task is waiting for a provider-specific runtime worker."""

    executor_task_id = provider.strip() or None
    _record_executor_dispatch(
        task_id,
        executor_type="external_runtime",
        executor_task_id=executor_task_id,
    )


def revoke_task_execution(task_id: str, *, terminate: bool = True, signal: str = "SIGTERM") -> bool:
    with sync_session_maker() as db:
        row = db.get(GenerationTask, task_id)
        if row is None:
            return False
        if (row.executor_type or "").strip() != "celery":
            return False
        executor_task_id = (row.executor_task_id or "").strip()
        if not executor_task_id:
            return False

    try:
        AsyncResult(executor_task_id, app=celery_app).revoke(terminate=terminate, signal=signal)
    except Exception:  # noqa: BLE001
        logger.exception("failed to revoke celery task: task_id=%s executor_task_id=%s", task_id, executor_task_id)
        return False
    return True


@celery_app.task(name="task.execute")
def run_task_celery(task_id: str) -> None:
    with sync_session_maker() as db:
        row = db.get(GenerationTask, task_id)
        if row is None:
            return
        task_kind = (row.task_kind or "").strip() or str((row.payload or {}).get("task_kind") or "").strip()
    executor = task_executor_registry.resolve(task_kind)
    executor.run(task_id)
