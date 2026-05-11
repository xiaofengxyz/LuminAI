from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_manager import DeliveryMode, SqlAlchemyTaskStore
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
from app.models.industrial import CineForgeWorkflowState
from app.models.task import GenerationTask, GenerationTaskStatus
from app.models.task_links import GenerationTaskLink, GenerationTaskLinkStatus
from app.schemas.common import ApiResponse, success_response
from app.services.common import entity_not_found
from app.services.industrial_film_core import (
    IndustrialProjectSnapshot,
    build_cineforge_regenerate_payload,
    build_cineforge_workflow_state,
    build_closed_loop_plan,
    build_industrial_overview,
    build_writeback_summary,
    ensure_cineforge_stage,
    mark_cineforge_regeneration_queued,
    patch_cineforge_stage_data,
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


class FilmIndustrialRunRequest(FilmIndustrialPlanRequest):
    mode: str = Field("queue_only", description="queue_only=只创建任务账本，由现有 worker/人工配置继续执行")


class FilmQueuedTaskRead(BaseModel):
    task_id: str
    task_kind: str
    resource_type: str
    relation_type: str
    relation_entity_id: str
    status: str
    progress: int
    purpose: str


class FilmIndustrialRunRead(BaseModel):
    run_id: str
    mode: str
    plan_id: str
    created_task_count: int
    render_task_count: int
    qa_task_count: int
    retry_task_count: int
    post_task_count: int
    tasks: list[FilmQueuedTaskRead]
    write_back_summary: dict[str, Any]
    overview: FilmIndustrialOverviewRead


class FilmWorkflowStageRead(BaseModel):
    key: str
    title: str
    owner: str
    prompt_file: str
    editable: bool
    regeneratable: bool
    qa_gate: str
    status: dict[str, Any]
    data: dict[str, Any]


class FilmWorkflowStateRead(BaseModel):
    id: str
    workflow_key: str
    version: int
    status: str
    scope: dict[str, Any]
    persisted: bool
    stage_count: int
    stages: list[FilmWorkflowStageRead]
    stage_data: dict[str, Any]
    stage_status: dict[str, Any]
    edit_log: list[dict[str, Any]]
    regenerate_log: list[dict[str, Any]]
    last_task_id: str | None = None
    edit_contract: dict[str, Any]
    regenerate_contract: dict[str, Any]


class FilmWorkflowStatePatchRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时编辑项目级工作流")
    actor: str = Field("operator", description="编辑者标识")
    note: str = Field("", description="本次编辑说明")
    patch: dict[str, Any] = Field(default_factory=dict, description="结构化阶段补丁")


class FilmWorkflowRegenerateRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时重生成项目级工作流阶段")
    actor: str = Field("operator", description="操作者标识")
    reason: str = Field("operator_requested", description="重生成原因")
    patch: dict[str, Any] = Field(default_factory=dict, description="重生成时附加的结构化约束")
    provider: str = Field("runtime_adapter", description="重生成任务供应商逻辑名")
    model: str = Field("project_default_model", description="重生成任务模型逻辑名")


class FilmWorkflowMutationRead(BaseModel):
    workflow: FilmWorkflowStateRead
    task: FilmQueuedTaskRead | None = None
    event: dict[str, Any]


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


@router.get(
    "/projects/{project_id}/workflow-state",
    response_model=ApiResponse[FilmWorkflowStateRead],
    summary="读取 CineForge 可编辑工作流状态",
    operation_id="loadWorkflowState",
)
async def get_workflow_state(
    project_id: str,
    chapter_id: str | None = Query(None, description="可选章节 ID；为空时按项目聚合"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmWorkflowStateRead]:
    """Load or initialize the persisted CineForge workflow state for this scope."""

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=chapter_id)
    row = await _load_or_create_workflow_state(db, snapshot)
    payload = FilmWorkflowStateRead.model_validate(_workflow_state_payload(snapshot, row))
    return success_response(payload)


@router.patch(
    "/projects/{project_id}/workflow-state/{stage_key}",
    response_model=ApiResponse[FilmWorkflowMutationRead],
    summary="编辑 CineForge 工作流阶段",
    operation_id="editWorkflowState",
)
async def edit_workflow_state(
    project_id: str,
    stage_key: str,
    body: FilmWorkflowStatePatchRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmWorkflowMutationRead]:
    """Merge an operator patch into one persisted workflow stage and ledger it."""

    try:
        ensure_cineforge_stage(stage_key)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=body.chapter_id)
    row = await _load_or_create_workflow_state(db, snapshot)
    next_version = int(row.version or 1) + 1
    stage_data, stage_status, edit_entry = patch_cineforge_stage_data(
        current_stage_data=row.stage_data or {},
        current_stage_status=row.stage_status or {},
        stage_key=stage_key,
        patch=body.patch,
        actor=body.actor,
        note=body.note,
        next_version=next_version,
    )
    task = await _record_workflow_task(
        db,
        workflow_id=row.id,
        task_kind="cineforge_workflow_edit",
        payload={
            "workflow_id": row.id,
            "stage_key": stage_key,
            "actor": body.actor,
            "note": body.note,
            "patch": body.patch,
            "version": next_version,
        },
        terminal=True,
        purpose="persist operator edit for a CineForge workflow stage",
    )
    row.version = next_version
    row.status = "edited"
    row.stage_data = stage_data
    row.stage_status = stage_status
    row.edit_log = [*(row.edit_log or []), {**edit_entry, "task_id": task["task_id"]}]
    row.last_task_id = task["task_id"]
    await db.flush()
    await db.refresh(row)

    payload = FilmWorkflowMutationRead.model_validate(
        {
            "workflow": _workflow_state_payload(snapshot, row),
            "task": task,
            "event": row.edit_log[-1],
        }
    )
    return success_response(payload)


@router.post(
    "/projects/{project_id}/workflow-state/{stage_key}/regenerate",
    response_model=ApiResponse[FilmWorkflowMutationRead],
    summary="重生成 CineForge 工作流阶段",
    operation_id="regenerateWorkflowStage",
)
async def regenerate_workflow_stage(
    project_id: str,
    stage_key: str,
    body: FilmWorkflowRegenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmWorkflowMutationRead]:
    """Queue a targeted regeneration task while preserving approved workflow state."""

    try:
        ensure_cineforge_stage(stage_key)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=body.chapter_id)
    row = await _load_or_create_workflow_state(db, snapshot)
    next_version = int(row.version or 1) + 1
    task_payload = build_cineforge_regenerate_payload(
        snapshot=snapshot,
        workflow_id=row.id,
        stage_key=stage_key,
        reason=body.reason,
        patch=body.patch,
        provider=body.provider,
        model=body.model,
        next_version=next_version,
    )
    task = await _record_workflow_task(
        db,
        workflow_id=row.id,
        task_kind="cineforge_stage_regenerate",
        payload=task_payload,
        terminal=False,
        purpose="queue targeted CineForge stage regeneration",
    )
    stage_status, regenerate_entry = mark_cineforge_regeneration_queued(
        current_stage_status=row.stage_status or {},
        stage_key=stage_key,
        task_id=task["task_id"],
        actor=body.actor,
        reason=body.reason,
        next_version=next_version,
    )
    row.version = next_version
    row.status = "regenerating"
    row.stage_status = stage_status
    row.regenerate_log = [*(row.regenerate_log or []), regenerate_entry]
    row.last_task_id = task["task_id"]
    await db.flush()
    await db.refresh(row)

    payload = FilmWorkflowMutationRead.model_validate(
        {
            "workflow": _workflow_state_payload(snapshot, row),
            "task": task,
            "event": row.regenerate_log[-1],
        }
    )
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


@router.post(
    "/projects/{project_id}/run",
    response_model=ApiResponse[FilmIndustrialRunRead],
    summary="创建工业闭环生产任务账本",
    operation_id="createIndustrialRun",
)
async def create_industrial_run(
    project_id: str,
    body: FilmIndustrialRunRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmIndustrialRunRead]:
    """Create Jellyfish task/link records for render, QA, retry, and post-production work."""

    if body.mode != "queue_only":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only queue_only mode is supported")

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=body.chapter_id)
    plan = build_closed_loop_plan(
        snapshot,
        provider=body.provider,
        model=body.model,
        output_dir=body.output_dir,
    )
    run_id = f"industrial-run-{uuid4().hex[:12]}"
    created_tasks = await _create_run_tasks(
        db,
        run_id=run_id,
        snapshot=snapshot,
        plan=plan,
        mode=body.mode,
    )
    await db.commit()

    render_count = sum(1 for item in created_tasks if item["task_kind"] == "industrial_video_render")
    qa_count = sum(1 for item in created_tasks if item["task_kind"] == "industrial_qa")
    retry_count = sum(1 for item in created_tasks if item["task_kind"] == "industrial_retry_plan")
    post_count = sum(1 for item in created_tasks if item["task_kind"] == "industrial_post_production")

    payload = FilmIndustrialRunRead.model_validate(
        {
            "run_id": run_id,
            "mode": body.mode,
            "plan_id": plan["plan_id"],
            "created_task_count": len(created_tasks),
            "render_task_count": render_count,
            "qa_task_count": qa_count,
            "retry_task_count": retry_count,
            "post_task_count": post_count,
            "tasks": created_tasks,
            "write_back_summary": build_writeback_summary(snapshot),
            "overview": plan["overview"],
        }
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
    ready_shot_ids = [shot.id for shot in shots if _value(shot.status) == ShotStatus.ready.value]
    generated_video_shot_ids = [shot.id for shot in shots if bool(shot.generated_video_file_id)]

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
        ready_shot_count=len(ready_shot_ids),
        generating_shot_count=sum(1 for shot in shots if _value(shot.status) == ShotStatus.generating.value),
        generated_video_count=len(generated_video_shot_ids),
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
        shot_ids=tuple(shot_ids),
        ready_shot_ids=tuple(ready_shot_ids),
        generated_video_shot_ids=tuple(generated_video_shot_ids),
    )


async def _load_or_create_workflow_state(
    db: AsyncSession,
    snapshot: IndustrialProjectSnapshot,
) -> CineForgeWorkflowState:
    await _ensure_workflow_state_table(db)
    stmt = select(CineForgeWorkflowState).where(
        CineForgeWorkflowState.project_id == snapshot.project_id,
        CineForgeWorkflowState.workflow_key == "cineforge_ai_drama_os",
    )
    if snapshot.chapter_id is None:
        stmt = stmt.where(CineForgeWorkflowState.chapter_id.is_(None))
    else:
        stmt = stmt.where(CineForgeWorkflowState.chapter_id == snapshot.chapter_id)

    row = (await db.execute(stmt.limit(1))).scalars().first()
    if row is not None:
        return row

    # The first read persists a recoverable baseline so later edits are diffs.
    row = CineForgeWorkflowState(
        id=f"cfwf-{uuid4().hex[:12]}",
        project_id=snapshot.project_id,
        chapter_id=snapshot.chapter_id,
        workflow_key="cineforge_ai_drama_os",
        status="draft",
        version=1,
        stage_data={},
        stage_status={},
        edit_log=[],
        regenerate_log=[],
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _ensure_workflow_state_table(db: AsyncSession) -> None:
    # Existing local Jellyfish databases may predate this Film Core table.
    connection = await db.connection()
    await connection.run_sync(lambda sync_conn: CineForgeWorkflowState.__table__.create(sync_conn, checkfirst=True))


def _workflow_state_payload(
    snapshot: IndustrialProjectSnapshot,
    row: CineForgeWorkflowState,
) -> dict[str, Any]:
    return build_cineforge_workflow_state(
        snapshot,
        workflow_id=row.id,
        status=row.status,
        version=int(row.version or 1),
        stage_data=row.stage_data or {},
        stage_status=row.stage_status or {},
        edit_log=row.edit_log or [],
        regenerate_log=row.regenerate_log or [],
        last_task_id=row.last_task_id,
    )


async def _record_workflow_task(
    db: AsyncSession,
    *,
    workflow_id: str,
    task_kind: str,
    payload: dict[str, Any],
    terminal: bool,
    purpose: str,
) -> dict[str, Any]:
    store = SqlAlchemyTaskStore(db)
    task = await store.create(
        payload=payload,
        mode=DeliveryMode.async_polling,
        task_kind=task_kind,
    )
    status_value = GenerationTaskStatus.pending.value
    progress = 0
    link_status = GenerationTaskLinkStatus.todo
    if terminal:
        row = await db.get(GenerationTask, task.id)
        if row is not None:
            row.status = GenerationTaskStatus.succeeded
            row.progress = 100
            row.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            row.result = {"message": purpose, "workflow_id": workflow_id}
        status_value = GenerationTaskStatus.succeeded.value
        progress = 100
        link_status = GenerationTaskLinkStatus.accepted

    db.add(
        GenerationTaskLink(
            task_id=task.id,
            resource_type="workflow",
            relation_type="cineforge_workflow_stage",
            relation_entity_id=workflow_id,
            status=link_status,
        )
    )
    return _queued_task(
        task_id=task.id,
        task_kind=task_kind,
        resource_type="workflow",
        relation_type="cineforge_workflow_stage",
        relation_entity_id=workflow_id,
        status_value=status_value,
        progress=progress,
        purpose=purpose,
    )


async def _create_run_tasks(
    db: AsyncSession,
    *,
    run_id: str,
    snapshot: IndustrialProjectSnapshot,
    plan: dict[str, Any],
    mode: str,
) -> list[dict[str, Any]]:
    store = SqlAlchemyTaskStore(db)
    created: list[dict[str, Any]] = []

    render_queue = plan.get("render_queue") if isinstance(plan, dict) else []
    ready_shot_ids = set(snapshot.ready_shot_ids)
    if isinstance(render_queue, list):
        for item in render_queue:
            if not isinstance(item, dict):
                continue
            shot_ref = str(item.get("shot_ref") or "")
            if not shot_ref or shot_ref not in ready_shot_ids:
                continue
            task_payload = {
                "run_id": run_id,
                "mode": mode,
                "plan_id": plan.get("plan_id"),
                "stage": "render_runtime",
                "shot_id": shot_ref,
                "provider": item.get("provider"),
                "model": item.get("model"),
                "output_path": item.get("output_path"),
                "references_required": item.get("references_required") or [],
                "compiled_prompt_contract": item.get("compiled_prompt_contract") or {},
            }
            task = await store.create(
                payload=task_payload,
                mode=DeliveryMode.async_polling,
                task_kind="industrial_video_render",
            )
            db.add(
                GenerationTaskLink(
                    task_id=task.id,
                    resource_type="video",
                    relation_type="video",
                    relation_entity_id=shot_ref,
                    status=GenerationTaskLinkStatus.todo,
                )
            )
            created.append(
                _queued_task(
                    task_id=task.id,
                    task_kind="industrial_video_render",
                    resource_type="video",
                    relation_type="video",
                    relation_entity_id=shot_ref,
                    purpose="queue structured video generation through runtime adapter",
                )
            )

    for shot_id in snapshot.generated_video_shot_ids:
        task = await store.create(
            payload={
                "run_id": run_id,
                "mode": mode,
                "plan_id": plan.get("plan_id"),
                "stage": "qa_engine",
                "shot_id": shot_id,
                "qa_policy": plan.get("qa_policy") or {},
            },
            mode=DeliveryMode.async_polling,
            task_kind="industrial_qa",
        )
        db.add(
            GenerationTaskLink(
                task_id=task.id,
                resource_type="qa",
                relation_type="industrial_qa",
                relation_entity_id=shot_id,
                status=GenerationTaskLinkStatus.todo,
            )
        )
        created.append(
            _queued_task(
                task_id=task.id,
                task_kind="industrial_qa",
                resource_type="qa",
                relation_type="industrial_qa",
                relation_entity_id=shot_id,
                purpose="score identity, costume, prompt, motion, and continuity",
            )
        )

    retry_targets = [shot_id for shot_id in snapshot.ready_shot_ids if shot_id not in snapshot.generated_video_shot_ids]
    for shot_id in retry_targets:
        task = await store.create(
            payload={
                "run_id": run_id,
                "mode": mode,
                "plan_id": plan.get("plan_id"),
                "stage": "retry_engine",
                "shot_id": shot_id,
                "retry_policy": plan.get("retry_policy") or {},
            },
            mode=DeliveryMode.async_polling,
            task_kind="industrial_retry_plan",
        )
        db.add(
            GenerationTaskLink(
                task_id=task.id,
                resource_type="retry",
                relation_type="industrial_retry",
                relation_entity_id=shot_id,
                status=GenerationTaskLinkStatus.todo,
            )
        )
        created.append(
            _queued_task(
                task_id=task.id,
                task_kind="industrial_retry_plan",
                resource_type="retry",
                relation_type="industrial_retry",
                relation_entity_id=shot_id,
                purpose="prepare repair patches for shots missing accepted video",
            )
        )

    post_production = plan.get("post_production") if isinstance(plan, dict) else {}
    if isinstance(post_production, dict) and post_production.get("enabled"):
        task = await store.create(
            payload={
                "run_id": run_id,
                "mode": mode,
                "plan_id": plan.get("plan_id"),
                "stage": "final_editing",
                "project_id": snapshot.project_id,
                "chapter_id": snapshot.chapter_id,
                "post_production": post_production,
            },
            mode=DeliveryMode.async_polling,
            task_kind="industrial_post_production",
        )
        db.add(
            GenerationTaskLink(
                task_id=task.id,
                resource_type="video",
                relation_type="industrial_post_production",
                relation_entity_id=snapshot.chapter_id or snapshot.project_id,
                status=GenerationTaskLinkStatus.todo,
            )
        )
        created.append(
            _queued_task(
                task_id=task.id,
                task_kind="industrial_post_production",
                resource_type="video",
                relation_type="industrial_post_production",
                relation_entity_id=snapshot.chapter_id or snapshot.project_id,
                purpose="assemble accepted clips, subtitles, audio, transitions, and export",
            )
        )

    if not created:
        task = await store.create(
            payload={
                "run_id": run_id,
                "mode": mode,
                "plan_id": plan.get("plan_id"),
                "stage": "industrial_gate",
                "project_id": snapshot.project_id,
                "blockers": plan.get("blockers") or [],
            },
            mode=DeliveryMode.async_polling,
            task_kind="industrial_gate",
        )
        row = await db.get(GenerationTask, task.id)
        if row is not None:
            row.status = GenerationTaskStatus.succeeded
            row.progress = 100
            row.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            row.result = {"message": "No renderable shots yet; resolve Film Core blockers first."}
        db.add(
            GenerationTaskLink(
                task_id=task.id,
                resource_type="plan",
                relation_type="industrial_project",
                relation_entity_id=snapshot.project_id,
                status=GenerationTaskLinkStatus.accepted,
            )
        )
        created.append(
            _queued_task(
                task_id=task.id,
                task_kind="industrial_gate",
                resource_type="plan",
                relation_type="industrial_project",
                relation_entity_id=snapshot.project_id,
                status_value=GenerationTaskStatus.succeeded.value,
                progress=100,
                purpose="record blockers because no shots are ready for production",
            )
        )

    return created


def _queued_task(
    *,
    task_id: str,
    task_kind: str,
    resource_type: str,
    relation_type: str,
    relation_entity_id: str,
    purpose: str,
    status_value: str = GenerationTaskStatus.pending.value,
    progress: int = 0,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_kind": task_kind,
        "resource_type": resource_type,
        "relation_type": relation_type,
        "relation_entity_id": relation_entity_id,
        "status": status_value,
        "progress": progress,
        "purpose": purpose,
    }


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
