from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.studio import (
    Chapter,
    Character,
    Project,
    ProjectActorLink,
    ProjectCostumeLink,
    ProjectPropLink,
    ProjectSceneLink,
    Shot,
    ShotCandidateStatus,
    ShotDetail,
    ShotDialogLine,
    ShotDialogueCandidateStatus,
    ShotExtractedCandidate,
    ShotExtractedDialogueCandidate,
    ShotFrameImage,
    ShotStatus,
)
from app.models.task_links import GenerationTaskLink, GenerationTaskLinkStatus
from app.schemas.common import ApiResponse, success_response
from app.services.common import entity_not_found
from app.services.industrial_film_core import (
    IndustrialProjectSnapshot,
    build_closed_loop_plan,
    build_industrial_overview,
)

router = APIRouter(prefix="/industrial")


class FilmProjectBriefRead(BaseModel):
    id: str
    name: str
    style: str
    visual_style: str
    seed: int
    unify_style: bool


class FilmChapterBriefRead(BaseModel):
    id: str | None = None
    title: str | None = None
    index: int | None = None


class FilmPipelineStageRead(BaseModel):
    key: str
    title: str
    owner: str
    description: str
    status: str
    evidence: str
    next_action: str


class FilmAssetHealthRead(BaseModel):
    identity_score: int
    scene_score: int
    prop_score: int
    costume_score: int
    pending_candidate_count: int
    pending_dialogue_count: int
    summary: str


class FilmQaRetryRead(BaseModel):
    qa_ready: bool
    generated_or_accepted_videos: int
    planned_retry_candidates: int
    risk_level: str
    automatic_retry_enabled: bool
    post_production_ready: bool


class FilmPainPointRead(BaseModel):
    key: str
    title: str
    severity: str
    diagnosis: str
    solution: str


class FilmReferenceProjectRead(BaseModel):
    name: str
    url: str
    adopted_layer: str
    rule: str


class FilmNextActionRead(BaseModel):
    severity: str
    action: str


class FilmImplementationStatusRead(BaseModel):
    total_phases: int
    completed_phases: int
    status: str
    label: str
    evidence: str


class FilmImplementationPhaseRead(BaseModel):
    key: str
    phase: str
    title: str
    owner: str
    status: str
    evidence: str
    surface: str


class FilmIndustrialOverviewRead(BaseModel):
    workflow_mode: str
    project: FilmProjectBriefRead
    chapter: FilmChapterBriefRead | None = None
    industrial_score: int
    pipeline: list[FilmPipelineStageRead]
    asset_health: FilmAssetHealthRead
    qa_retry: FilmQaRetryRead
    pain_points: list[FilmPainPointRead]
    reference_projects: list[FilmReferenceProjectRead]
    operator_next_actions: list[FilmNextActionRead]
    implementation_status: FilmImplementationStatusRead
    implementation_phases: list[FilmImplementationPhaseRead]


class FilmCompiledPromptContractRead(BaseModel):
    source: str
    must_include: list[str]


class FilmRenderQueueItemRead(BaseModel):
    slot: int
    shot_ref: str
    provider: str
    model: str
    output_path: str
    references_required: list[str]
    compiled_prompt_contract: FilmCompiledPromptContractRead


class FilmQaPolicyRead(BaseModel):
    face_similarity_min: float
    outfit_similarity_min: float
    clip_score_min: float
    continuity_checks: list[str]


class FilmRetryPolicyRead(BaseModel):
    max_attempts: int
    planned_retry_candidates: int
    repair_patch_contract: list[str]


class FilmPostProductionRead(BaseModel):
    enabled: bool
    steps: list[str]
    write_back_targets: list[str]


class FilmIndustrialPlanRead(BaseModel):
    plan_id: str
    workflow: list[str]
    overview: FilmIndustrialOverviewRead
    render_queue: list[FilmRenderQueueItemRead]
    qa_policy: FilmQaPolicyRead
    retry_policy: FilmRetryPolicyRead
    post_production: FilmPostProductionRead
    blockers: list[FilmNextActionRead]


class FilmIndustrialPlanRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时按项目聚合规划")
    provider: str = Field("runtime_adapter", description="运行时供应商逻辑名")
    model: str = Field("project_default_video_model", description="视频模型逻辑名")
    output_dir: str = Field("output/jellyfish-industrial", description="计划输出目录")


@router.get(
    "/projects/{project_id}/overview",
    response_model=ApiResponse[FilmIndustrialOverviewRead],
    summary="工业电影级 Film Core 总览",
    operation_id="loadIndustrialOverview",
)
async def get_industrial_overview(
    project_id: str,
    chapter_id: str | None = Query(None, description="可选章节 ID；为空时按项目聚合"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmIndustrialOverviewRead]:
    """Return Film Core readiness, pipeline state, and nine-phase delivery evidence."""

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=chapter_id)
    payload = FilmIndustrialOverviewRead.model_validate(build_industrial_overview(snapshot))
    return success_response(payload)


@router.post(
    "/projects/{project_id}/plan",
    response_model=ApiResponse[FilmIndustrialPlanRead],
    summary="生成工业闭环生产计划预览",
    operation_id="createIndustrialPlan",
)
async def create_industrial_plan(
    project_id: str,
    body: FilmIndustrialPlanRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmIndustrialPlanRead]:
    """Return a render, QA, retry, and post-production plan without executing runtime work."""

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=body.chapter_id)
    payload = FilmIndustrialPlanRead.model_validate(
        build_closed_loop_plan(
            snapshot,
            provider=body.provider,
            model=body.model,
            output_dir=body.output_dir,
        )
    )
    return success_response(payload)


async def load_industrial_snapshot(
    db: AsyncSession,
    *,
    project_id: str,
    chapter_id: str | None = None,
) -> IndustrialProjectSnapshot:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=entity_not_found("Project"))

    chapters = await _load_chapters(db, project_id)
    focus_chapter = None
    if chapter_id is not None:
        focus_chapter = next((chapter for chapter in chapters if chapter.id == chapter_id), None)
        if focus_chapter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=entity_not_found("Chapter"))

    selected_chapters = [focus_chapter] if focus_chapter is not None else chapters
    chapter_ids = [chapter.id for chapter in selected_chapters]
    shots = await _load_shots(db, chapter_ids)
    shot_ids = [shot.id for shot in shots]

    return IndustrialProjectSnapshot(
        project_id=project.id,
        project_name=project.name,
        project_style=_value(project.style),
        visual_style=_value(project.visual_style),
        seed=int(project.seed or 0),
        unify_style=bool(project.unify_style),
        chapter_id=focus_chapter.id if focus_chapter is not None else None,
        chapter_title=focus_chapter.title if focus_chapter is not None else None,
        chapter_index=focus_chapter.index if focus_chapter is not None else None,
        script_text_length=sum(len(chapter.raw_text or "") for chapter in selected_chapters),
        condensed_text_length=sum(len(chapter.condensed_text or "") for chapter in selected_chapters),
        chapter_count=len(chapters),
        shot_count=len(shots),
        ready_shot_count=sum(1 for shot in shots if _value(shot.status) == ShotStatus.ready.value),
        generating_shot_count=sum(1 for shot in shots if _value(shot.status) == ShotStatus.generating.value),
        generated_video_count=sum(1 for shot in shots if bool(shot.generated_video_file_id)),
        detail_count=await _count_for_shots(db, ShotDetail.id, shot_ids),
        frame_image_count=await _count_for_shots(db, ShotFrameImage.shot_detail_id, shot_ids),
        dialogue_line_count=await _count_for_shots(db, ShotDialogLine.shot_detail_id, shot_ids),
        character_count=await _count(db, select(func.count(Character.id)).where(Character.project_id == project_id)),
        actor_link_count=await _count(db, select(func.count(ProjectActorLink.id)).where(ProjectActorLink.project_id == project_id)),
        scene_link_count=await _count(db, select(func.count(ProjectSceneLink.id)).where(ProjectSceneLink.project_id == project_id)),
        prop_link_count=await _count(db, select(func.count(ProjectPropLink.id)).where(ProjectPropLink.project_id == project_id)),
        costume_link_count=await _count(db, select(func.count(ProjectCostumeLink.id)).where(ProjectCostumeLink.project_id == project_id)),
        pending_candidate_count=await _count_pending_candidates(db, shot_ids),
        pending_dialogue_count=await _count_pending_dialogues(db, shot_ids),
        task_link_count=await _count_task_links(db, shot_ids),
        accepted_video_task_count=await _count_accepted_video_task_links(db, shot_ids),
    )


async def _load_chapters(db: AsyncSession, project_id: str) -> list[Chapter]:
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.index)
    )
    return list(result.scalars().all())


async def _load_shots(db: AsyncSession, chapter_ids: list[str]) -> list[Shot]:
    if not chapter_ids:
        return []
    result = await db.execute(
        select(Shot)
        .where(Shot.chapter_id.in_(chapter_ids))
        .order_by(Shot.chapter_id, Shot.index)
    )
    return list(result.scalars().all())


async def _count(db: AsyncSession, stmt: Any) -> int:
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def _count_for_shots(db: AsyncSession, column: Any, shot_ids: list[str]) -> int:
    if not shot_ids:
        return 0
    return await _count(db, select(func.count()).where(column.in_(shot_ids)))


async def _count_pending_candidates(db: AsyncSession, shot_ids: list[str]) -> int:
    if not shot_ids:
        return 0
    return await _count(
        db,
        select(func.count(ShotExtractedCandidate.id)).where(
            ShotExtractedCandidate.shot_id.in_(shot_ids),
            ShotExtractedCandidate.candidate_status == ShotCandidateStatus.pending,
        ),
    )


async def _count_pending_dialogues(db: AsyncSession, shot_ids: list[str]) -> int:
    if not shot_ids:
        return 0
    return await _count(
        db,
        select(func.count(ShotExtractedDialogueCandidate.id)).where(
            ShotExtractedDialogueCandidate.shot_id.in_(shot_ids),
            ShotExtractedDialogueCandidate.candidate_status == ShotDialogueCandidateStatus.pending,
        ),
    )


async def _count_task_links(db: AsyncSession, shot_ids: list[str]) -> int:
    if not shot_ids:
        return 0
    return await _count(
        db,
        select(func.count(GenerationTaskLink.id)).where(GenerationTaskLink.relation_entity_id.in_(shot_ids)),
    )


async def _count_accepted_video_task_links(db: AsyncSession, shot_ids: list[str]) -> int:
    if not shot_ids:
        return 0
    return await _count(
        db,
        select(func.count(GenerationTaskLink.id)).where(
            GenerationTaskLink.relation_entity_id.in_(shot_ids),
            GenerationTaskLink.resource_type == "video",
            GenerationTaskLink.status == GenerationTaskLinkStatus.accepted,
        ),
    )


def _value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)
