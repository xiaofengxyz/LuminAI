from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.api.v1.routes.film.industrial import (
    FilmTextToDramaRequest,
    FilmWorkflowRegenerateRequest,
    FilmWorkflowStageCompleteRequest,
    FilmWorkflowStatePatchRequest,
    complete_workflow_stage,
    create_text_to_drama,
    edit_workflow_state,
    get_workflow_state,
    regenerate_workflow_stage,
)
from app.core.db import Base
from app.models.industrial import CineForgeWorkflowState
from app.models.studio import Chapter, Project, ProjectStyle, ProjectVisualStyle, Shot, ShotStatus
from app.models.task import GenerationTask
from app.models.task_links import GenerationTaskLink


async def _build_session() -> tuple[AsyncSession, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return session_local(), engine


async def _seed_project(db: AsyncSession) -> None:
    db.add_all(
        [
            Project(
                id="project-1",
                name="Neon Trial",
                description="Pilot",
                style=ProjectStyle.real_people_city,
                visual_style=ProjectVisualStyle.live_action,
                seed=42,
                unify_style=True,
            ),
            Chapter(
                id="chapter-1",
                project_id="project-1",
                index=1,
                title="Pilot",
                raw_text="Ari enters the rain alley and notices the missing envelope.",
                condensed_text="Ari finds the envelope is missing.",
            ),
            Shot(
                id="shot-1",
                chapter_id="chapter-1",
                index=1,
                title="Rain alley reveal",
                status=ShotStatus.ready,
                script_excerpt="Ari stops under the neon sign.",
            ),
        ]
    )
    await db.commit()


async def test_workflow_state_initializes_and_persists_cineforge_stages():
    db, engine = await _build_session()
    try:
        await _seed_project(db)

        response = await get_workflow_state("project-1", chapter_id=None, db=db)

        assert response.data is not None
        assert response.data.workflow_key == "cineforge_ai_drama_os"
        assert response.data.stage_count == 9
        assert [stage.key for stage in response.data.stages] == [
            "workflow_architecture",
            "novel_engine",
            "asset_pipeline",
            "image_runtime",
            "video_runtime",
            "qa_retry_engine",
            "studio_ui",
            "data_schema",
            "final_integration",
        ]
        assert response.data.stages[1].data["world_bible"]["title"] == "Neon Trial"

        rows = (await db.execute(select(CineForgeWorkflowState))).scalars().all()
        assert len(rows) == 1
        assert rows[0].project_id == "project-1"
    finally:
        await db.close()
        await engine.dispose()


async def test_workflow_state_edit_and_regenerate_are_versioned_task_ledger_events():
    db, engine = await _build_session()
    try:
        await _seed_project(db)

        edit_response = await edit_workflow_state(
            "project-1",
            "novel_engine",
            FilmWorkflowStatePatchRequest(
                actor="tester",
                note="lock cliffhanger",
                patch={"cliffhanger_engine": {"policy": "end on the unanswered envelope clue"}},
            ),
            db=db,
        )
        assert edit_response.data is not None
        assert edit_response.data.workflow.version == 2
        assert edit_response.data.workflow.stages[1].status["state"] == "edited"
        assert edit_response.data.task is not None
        assert edit_response.data.task.task_kind == "cineforge_workflow_edit"
        assert edit_response.data.task.status == "succeeded"

        regenerate_response = await regenerate_workflow_stage(
            "project-1",
            "asset_pipeline",
            FilmWorkflowRegenerateRequest(
                actor="tester",
                reason="refresh storyboard after new prop lock",
                patch={"preserve_approved_outputs": True},
            ),
            db=db,
        )

        assert regenerate_response.data is not None
        assert regenerate_response.data.workflow.version == 3
        assert regenerate_response.data.workflow.stage_status["asset_pipeline"]["state"] == "regeneration_queued"
        assert regenerate_response.data.task is not None
        assert regenerate_response.data.task.task_kind == "cineforge_stage_regenerate"
        assert regenerate_response.data.task.status == "pending"

        tasks = (await db.execute(select(GenerationTask).order_by(GenerationTask.created_at))).scalars().all()
        links = (await db.execute(select(GenerationTaskLink))).scalars().all()
        assert [task.task_kind for task in tasks] == [
            "cineforge_workflow_edit",
            "cineforge_stage_regenerate",
        ]
        assert {link.resource_type for link in links} == {"workflow"}
        assert {link.relation_type for link in links} == {"cineforge_workflow_stage"}
    finally:
        await db.close()
        await engine.dispose()


async def test_workflow_stage_complete_uses_automatic_or_manual_gate():
    db, engine = await _build_session()
    try:
        await _seed_project(db)

        auto_response = await complete_workflow_stage(
            "project-1",
            "asset_pipeline",
            FilmWorkflowStageCompleteRequest(
                actor="tester",
                result={"summary": "asset bible generated"},
            ),
            db=db,
        )

        assert auto_response.data is not None
        assert auto_response.data.workflow.stage_status["asset_pipeline"]["state"] == "completed"
        assert auto_response.data.workflow.stage_status["image_runtime"]["state"] == "active"
        assert auto_response.data.task is not None
        assert auto_response.data.task.task_kind == "cineforge_stage_auto_advance"
        assert auto_response.data.task.status == "pending"

        manual_response = await complete_workflow_stage(
            "project-1",
            "studio_ui",
            FilmWorkflowStageCompleteRequest(
                actor="tester",
                result={"summary": "operator reviewed UI gate"},
            ),
            db=db,
        )

        assert manual_response.data is not None
        assert manual_response.data.workflow.status == "waiting_operator"
        assert manual_response.data.workflow.stage_status["studio_ui"]["state"] == "waiting_operator"
        assert manual_response.data.task is not None
        assert manual_response.data.task.task_kind == "cineforge_stage_manual_gate"
        assert manual_response.data.task.status == "succeeded"
    finally:
        await db.close()
        await engine.dispose()


async def test_text_to_drama_creates_project_episodes_shots_and_workflow_tasks():
    db, engine = await _build_session()
    try:
        response = await create_text_to_drama(
            FilmTextToDramaRequest(
                source_text="少女在雨夜发现会发光的剧本，剧本每翻一页就改写城市记忆。",
                project_name="雨夜发光剧本",
                episode_count=2,
                shots_per_episode=3,
            ),
            db=db,
        )

        assert response.data is not None
        assert response.data.project.name == "雨夜发光剧本"
        assert len(response.data.chapters) == 2
        assert response.data.created_shot_count == 6
        assert response.data.workflow.workflow_key == "cineforge_ai_drama_os"
        assert response.data.workflow.stages[1].automation.mode == "automatic"
        assert [task.task_kind for task in response.data.tasks] == [
            "cineforge_text_to_drama_intake",
            "cineforge_text_to_drama_auto_pipeline",
        ]

        chapters = (await db.execute(select(Chapter))).scalars().all()
        shots = (await db.execute(select(Shot))).scalars().all()
        tasks = (await db.execute(select(GenerationTask).order_by(GenerationTask.created_at))).scalars().all()
        assert len(chapters) == 2
        assert len(shots) == 6
        assert [task.task_kind for task in tasks] == [
            "cineforge_text_to_drama_intake",
            "cineforge_text_to_drama_auto_pipeline",
        ]
    finally:
        await db.close()
        await engine.dispose()
