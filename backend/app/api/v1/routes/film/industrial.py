from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_manager import DeliveryMode, SqlAlchemyTaskStore
from app.dependencies import get_db
from app.models.studio import (
    Actor,
    ActorImage,
    AssetQualityLevel,
    AssetViewAngle,
    Chapter,
    Character,
    CharacterImage,
    CharacterPropLink,
    Costume,
    CostumeImage,
    Project,
    ProjectActorLink,
    ProjectCostumeLink,
    ProjectPropLink,
    ProjectSceneLink,
    Prop,
    PropImage,
    Scene,
    SceneImage,
    ProjectStyle,
    ProjectVisualStyle,
    Shot,
    ShotCandidateStatus,
    ShotCandidateType,
    ShotCharacterLink,
    ShotDetail,
    ShotDialogLine,
    ShotDialogueCandidateStatus,
    ShotExtractedCandidate,
    ShotExtractedDialogueCandidate,
    ShotFrameImage,
    ShotFrameType,
    ShotStatus,
    CameraAngle,
    CameraMovement,
    CameraShotType,
    ChapterStatus,
    DialogueLineMode,
    VFXType,
)
from app.models.industrial import CineForgeWorkflowState
from app.models.task import GenerationTask, GenerationTaskStatus
from app.models.task_links import GenerationTaskLink, GenerationTaskLinkStatus
from app.schemas.common import ApiResponse, success_response
from app.services.common import entity_already_exists, entity_not_found
from app.services.industrial_film_core import (
    CINEFORGE_WORKFLOW_STAGES,
    IndustrialProjectSnapshot,
    build_cineforge_regenerate_payload,
    build_cineforge_workflow_state,
    build_closed_loop_plan,
    build_industrial_overview,
    build_writeback_summary,
    complete_cineforge_stage,
    ensure_cineforge_stage,
    mark_cineforge_regeneration_queued,
    patch_cineforge_stage_data,
)
from app.services.film.text_to_drama import (
    TextToDramaBlueprint,
    build_text_to_drama_blueprint,
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


class FilmProductionModuleRead(BaseModel):
    key: str
    title: str
    status: str
    progress: int
    summary: str
    tasks: list[str]
    next_action: str
    route_hint: str
    can_return: bool
    blockers: list[str]


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


class FilmCreationEntryRead(BaseModel):
    key: str
    title: str
    purpose: str
    when_to_use: str
    route_hint: str
    output: str


class FilmShootingGateRead(BaseModel):
    ready: bool
    state: str
    message: str
    blockers: list[str]
    required_before_shooting: list[str]
    allowed_runtime_models: list[str]


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
    production_modules: list[FilmProductionModuleRead]
    asset_health: FilmAssetHealthRead
    qa_retry: FilmQaRetryRead
    pain_points: list[FilmPainPointRead]
    reference_projects: list[FilmReferenceProjectRead]
    creation_entries: list[FilmCreationEntryRead]
    shooting_gate: FilmShootingGateRead
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


class FilmWorkflowAutomationRead(BaseModel):
    mode: Literal["automatic", "manual"]
    auto_advance: bool
    stop_after_stage: bool
    manual_allowed: bool = True
    next_stage_key: str | None = None


class FilmWorkflowStageRead(BaseModel):
    key: str
    title: str
    owner: str
    prompt_file: str
    editable: bool
    regeneratable: bool
    qa_gate: str
    default_execution_mode: Literal["automatic", "manual"]
    automation: FilmWorkflowAutomationRead
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
    automation_contract: dict[str, Any]


class FilmWorkflowStatePatchRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时编辑项目级工作流")
    actor: str = Field("operator", description="编辑者标识")
    note: str = Field("", description="本次编辑说明")
    patch: dict[str, Any] = Field(default_factory=dict, description="结构化阶段补丁")
    execution_mode: Literal["automatic", "manual"] | None = Field(
        None,
        description="阶段执行开关；automatic 自动进入下一阶段，manual 阶段结束后停等人工",
    )
    auto_advance: bool | None = Field(None, description="automatic 模式下是否自动推进下一阶段")


class FilmWorkflowRegenerateRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时重生成项目级工作流阶段")
    actor: str = Field("operator", description="操作者标识")
    reason: str = Field("operator_requested", description="重生成原因")
    patch: dict[str, Any] = Field(default_factory=dict, description="重生成时附加的结构化约束")
    provider: str = Field("runtime_adapter", description="重生成任务供应商逻辑名")
    model: str = Field("project_default_model", description="重生成任务模型逻辑名")


class FilmWorkflowStageCompleteRequest(BaseModel):
    chapter_id: str | None = Field(None, description="可选章节 ID；为空时推进项目级工作流")
    actor: str = Field("operator", description="操作者标识")
    result: dict[str, Any] = Field(default_factory=dict, description="阶段执行结果摘要")
    execution_mode: Literal["automatic", "manual"] | None = Field(
        None,
        description="本次完成时临时覆盖阶段执行开关",
    )


class FilmWorkflowMutationRead(BaseModel):
    workflow: FilmWorkflowStateRead
    task: FilmQueuedTaskRead | None = None
    event: dict[str, Any]


class FilmTextToDramaRequest(BaseModel):
    source_text: str = Field(..., min_length=1, description="用户输入的一段创意、梗概或原始文本")
    project_id: str | None = Field(None, description="可选项目 ID；为空则自动生成")
    project_name: str | None = Field(None, description="可选项目名称；为空从文本生成")
    episode_count: int = Field(3, ge=1, le=50, description="生成多集漫剧的集数")
    shots_per_episode: int = Field(6, ge=1, le=30, description="每集初始镜头数")
    style: ProjectStyle = Field(ProjectStyle.guoman, description="项目题材/风格")
    visual_style: ProjectVisualStyle = Field(ProjectVisualStyle.anime, description="画面表现形式")
    default_video_ratio: str = Field("9:16", description="默认视频比例")
    automation_mode: Literal["automatic", "manual"] = Field(
        "automatic",
        description="全流程默认开关；automatic 进入自动任务账本，manual 创建后停等人工",
    )
    reference_harvest_enabled: bool = Field(
        True,
        description="是否为每个角色创建网络图片/视频参考采集任务；默认只采集候选 URL 与授权线索",
    )
    provider: str = Field("project_default_video_provider", description="生产计划使用的供应商逻辑名")
    model: str = Field("project_default_video_model", description="生产计划使用的模型逻辑名")


class FilmTextToDramaRead(BaseModel):
    project: FilmProjectBriefRead
    chapters: list[FilmChapterBriefRead]
    created_shot_count: int
    created_character_count: int
    created_scene_count: int
    created_prop_count: int
    created_costume_count: int
    reference_harvest_task_count: int
    shooting_gate: FilmShootingGateRead
    workflow: FilmWorkflowStateRead
    tasks: list[FilmQueuedTaskRead]
    next_url: str
    usage: dict[str, Any]


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
    "/text-to-drama",
    response_model=ApiResponse[FilmTextToDramaRead],
    summary="从一段文字创建多集 AI 漫剧生产入口",
    operation_id="createTextToDrama",
)
async def create_text_to_drama(
    body: FilmTextToDramaRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmTextToDramaRead]:
    """Create a recoverable project/chapter/shot/workflow ledger from source text."""

    project_id = body.project_id or f"cfproj-{uuid4().hex[:12]}"
    if await db.get(Project, project_id) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=entity_already_exists("Project"))
    await _cleanup_stale_text_to_drama_scope(db, project_id)

    source_text = body.source_text.strip()
    project_name = (body.project_name or _title_from_source_text(source_text)).strip()
    blueprint = build_text_to_drama_blueprint(
        source_text=source_text,
        project_name=project_name,
        episode_count=body.episode_count,
        shots_per_episode=body.shots_per_episode,
        style=_value(body.style),
        visual_style=_value(body.visual_style),
        reference_harvest_enabled=body.reference_harvest_enabled,
    )
    project = Project(
        id=project_id,
        name=project_name,
        description=blueprint.series_logline[:240],
        style=body.style,
        visual_style=body.visual_style,
        seed=_stable_seed_from_text(source_text),
        unify_style=True,
        progress=20 if body.automation_mode == "automatic" else 10,
        default_video_ratio=body.default_video_ratio,
        stats={
            "chapters": body.episode_count,
            "shots": body.episode_count * body.shots_per_episode,
            "roles": len(blueprint.characters),
            "scenes": len(blueprint.scenes),
            "props": len(blueprint.props),
            "costumes": len(blueprint.characters),
            "source": "text_to_drama",
            "source_pipeline": "text_to_novel_to_assets_to_storyboard",
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
    )
    db.add(project)

    asset_ids = _persist_text_to_drama_assets(
        db,
        project_id=project_id,
        project_name=project_name,
        blueprint=blueprint,
        style=body.style,
        visual_style=body.visual_style,
    )
    created_chapters: list[Chapter] = []
    created_shot_count = 0
    for episode in blueprint.episodes:
        chapter_id = f"{project_id}-ep-{episode.index:02d}"
        chapter = Chapter(
            id=chapter_id,
            project_id=project_id,
            index=episode.index,
            title=episode.title,
            summary=episode.summary,
            raw_text=episode.novel_text,
            condensed_text="\n".join(episode.script_outline),
            storyboard_count=len(episode.shots),
            status=ChapterStatus.shooting if body.automation_mode == "automatic" else ChapterStatus.draft,
        )
        db.add(chapter)
        created_chapters.append(chapter)
        for shot_index, shot_seed in enumerate(episode.shots, start=1):
            shot_id = f"{chapter_id}-s{shot_index:03d}"
            db.add(
                Shot(
                    id=shot_id,
                    chapter_id=chapter_id,
                    index=shot_index,
                    title=shot_seed.title,
                    status=ShotStatus.ready if body.automation_mode == "automatic" else ShotStatus.pending,
                    script_excerpt=shot_seed.script_excerpt,
                    skip_extraction=body.automation_mode == "automatic",
                    last_extracted_at=datetime.now(timezone.utc),
                )
            )
            db.add(
                ShotDetail(
                    id=shot_id,
                    camera_shot=CameraShotType(shot_seed.camera_shot),
                    angle=CameraAngle(shot_seed.camera_angle),
                    movement=CameraMovement(shot_seed.camera_movement),
                    scene_id=asset_ids["scenes"].get(shot_seed.scene_key),
                    duration=shot_seed.duration,
                    override_video_ratio=body.default_video_ratio,
                    mood_tags=["generated_novel", "auto_storyboard", "film_core_gate"],
                    atmosphere=shot_seed.storyboard,
                    has_bgm=True,
                    vfx_type=VFXType(shot_seed.vfx_type),
                    vfx_note=shot_seed.vfx_note,
                    description=shot_seed.storyboard,
                    action_beats=[shot_seed.script_excerpt, shot_seed.storyboard],
                    first_frame_prompt=f"{shot_seed.storyboard}；首帧锁定场景、角色站位和服装。",
                    key_frame_prompt=f"{shot_seed.storyboard}；关键帧突出动作拍点和{shot_seed.vfx_note}。",
                    last_frame_prompt=f"{shot_seed.storyboard}；尾帧承接下一镜头连续性。",
                )
            )
            _persist_shot_story_assets(
                db,
                project_id=project_id,
                chapter_id=chapter_id,
                shot_id=shot_id,
                shot_seed=shot_seed,
                asset_ids=asset_ids,
            )
            created_shot_count += 1

    await db.flush()
    snapshot = await load_industrial_snapshot(db, project_id=project_id)
    row = await _load_or_create_workflow_state(db, snapshot)
    automation_patch = _workflow_automation_patch(body.automation_mode)
    row.stage_data = _with_stage_data(
        row.stage_data or {},
        {
            "novel_engine": {
                "source_text_seed": source_text[:2000],
                "target_episode_count": body.episode_count,
                "goal": "expand source text into a serialized novel, then into AI drama episodes",
                "series_logline": blueprint.series_logline,
                "generated_novel": blueprint.generated_novel_text[:6000],
                "world_bible": blueprint.world_bible,
                "relationship_graph": blueprint.relationship_graph,
                "episodes": [
                    {
                        "index": episode.index,
                        "title": episode.title,
                        "summary": episode.summary,
                        "script_outline": episode.script_outline,
                        "cliffhanger": episode.cliffhanger,
                    }
                    for episode in blueprint.episodes
                ],
            },
            "asset_pipeline": {
                "character_bible": [
                    {
                        "key": item.key,
                        "name": item.name,
                        "description": item.description,
                        "costume": item.costume,
                        "traits": item.traits,
                    }
                    for item in blueprint.characters
                ],
                "scene_bible": [item.__dict__ for item in blueprint.scenes],
                "prop_bible": [item.__dict__ for item in blueprint.props],
                "vfx_notes": blueprint.vfx_notes,
                "storyboard": [
                    {
                        "episode": episode.index,
                        "shots": [
                            {
                                "key": shot.key,
                                "title": shot.title,
                                "storyboard": shot.storyboard,
                                "characters": shot.character_keys,
                                "props": shot.prop_keys,
                                "vfx": shot.vfx_note,
                            }
                            for shot in episode.shots
                        ],
                    }
                    for episode in blueprint.episodes
                ],
            },
            "image_runtime": {
                "reference_harvest": blueprint.reference_harvest,
                "reference_policy": ["web metadata candidates", "identity lock", "costume lock", "scene keyframe"],
            },
            "video_runtime": {
                "shooting_gate": build_industrial_overview(snapshot)["shooting_gate"],
                "provider": body.provider,
                "model": body.model,
            },
            "final_integration": {
                "user_goal": "输入一段文字 -> 自动生成小说 -> 自动生成多集 AI 漫剧",
                "default_provider": body.provider,
                "default_model": body.model,
                "created_assets": {
                    "characters": len(blueprint.characters),
                    "scenes": len(blueprint.scenes),
                    "props": len(blueprint.props),
                    "costumes": len(blueprint.characters),
                    "shots": created_shot_count,
                },
            },
        },
        automation_patch=automation_patch,
    )
    row.stage_status = _with_stage_status(row.stage_status or {}, automation_patch=automation_patch)
    row.status = "running" if body.automation_mode == "automatic" else "waiting_operator"
    row.version = int(row.version or 1) + 1

    intake_task = await _record_workflow_task(
        db,
        workflow_id=row.id,
        task_kind="cineforge_text_to_drama_intake",
        payload={
            "project_id": project_id,
            "workflow_id": row.id,
            "episode_count": body.episode_count,
            "shots_per_episode": body.shots_per_episode,
            "automation_mode": body.automation_mode,
        },
        terminal=True,
        purpose="create project, episodes, shot graph seeds, and CineForge workflow from user text",
    )
    tasks = [intake_task]
    if body.reference_harvest_enabled:
        tasks.extend(
            await _record_reference_harvest_tasks(
                db,
                workflow_id=row.id,
                project_id=project_id,
                reference_harvest=blueprint.reference_harvest,
            )
        )
    if body.automation_mode == "automatic":
        tasks.append(
            await _record_workflow_task(
                db,
                workflow_id=row.id,
                task_kind="cineforge_text_to_drama_auto_pipeline",
                payload={
                    "project_id": project_id,
                    "workflow_id": row.id,
                    "provider": body.provider,
                    "model": body.model,
                    "entry_stage": "novel_engine",
                    "target": "novel_to_ai_drama",
                },
                terminal=False,
                purpose="auto-run CineForge stages until a manual stage switch is encountered",
            )
        )
    row.last_task_id = tasks[-1]["task_id"]
    row.edit_log = [
        *(row.edit_log or []),
        {
            "stage_key": "novel_engine",
            "actor": "text_to_drama",
            "note": "created from source text",
            "automation_mode": body.automation_mode,
            "version": row.version,
            "task_id": row.last_task_id,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
    ]
    await db.flush()
    await db.refresh(row)

    payload = FilmTextToDramaRead.model_validate(
        {
            "project": {
                "id": project.id,
                "name": project.name,
                "style": _value(project.style),
                "visual_style": _value(project.visual_style),
                "seed": int(project.seed or 0),
                "unify_style": bool(project.unify_style),
            },
            "chapters": [
                {"id": c.id, "title": c.title, "index": c.index}
                for c in created_chapters
            ],
            "created_shot_count": created_shot_count,
            "created_character_count": len(blueprint.characters),
            "created_scene_count": len(blueprint.scenes),
            "created_prop_count": len(blueprint.props),
            "created_costume_count": len(blueprint.characters),
            "reference_harvest_task_count": sum(
                1 for task in tasks if task["task_kind"] == "cineforge_reference_harvest"
            ),
            "shooting_gate": build_industrial_overview(snapshot)["shooting_gate"],
            "workflow": _workflow_state_payload(snapshot, row),
            "tasks": tasks,
            "next_url": f"/projects/{project_id}?tab=filmCore",
            "usage": {
                "source_text_chars": len(source_text),
                "generated_novel_chars": len(blueprint.generated_novel_text),
                "episode_count": body.episode_count,
                "shots_per_episode": body.shots_per_episode,
                "automation_mode": body.automation_mode,
                "reference_harvest_enabled": body.reference_harvest_enabled,
            },
        }
    )
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
        execution_mode=body.execution_mode,
        auto_advance=body.auto_advance,
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
    "/projects/{project_id}/workflow-state/{stage_key}/complete",
    response_model=ApiResponse[FilmWorkflowMutationRead],
    summary="完成 CineForge 工作流阶段并按开关推进",
    operation_id="completeWorkflowStage",
)
async def complete_workflow_stage(
    project_id: str,
    stage_key: str,
    body: FilmWorkflowStageCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FilmWorkflowMutationRead]:
    """Complete a stage; automatic stages activate the next stage, manual stages halt."""

    try:
        ensure_cineforge_stage(stage_key)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    snapshot = await load_industrial_snapshot(db, project_id=project_id, chapter_id=body.chapter_id)
    row = await _load_or_create_workflow_state(db, snapshot)
    next_version = int(row.version or 1) + 1
    current_payload = _workflow_state_payload(snapshot, row)
    current_stage = next((item for item in current_payload["stages"] if item["key"] == stage_key), None)
    current_mode = body.execution_mode or (
        current_stage.get("automation", {}).get("mode") if isinstance(current_stage, dict) else None
    )
    is_automatic = current_mode == "automatic"
    task = await _record_workflow_task(
        db,
        workflow_id=row.id,
        task_kind="cineforge_stage_auto_advance" if is_automatic else "cineforge_stage_manual_gate",
        payload={
            "workflow_id": row.id,
            "stage_key": stage_key,
            "actor": body.actor,
            "result": body.result,
            "execution_mode": current_mode,
            "version": next_version,
        },
        terminal=not is_automatic,
        purpose="complete CineForge stage and apply automatic/manual gate",
    )
    try:
        stage_data, stage_status, complete_entry = complete_cineforge_stage(
            current_stage_data=row.stage_data or {},
            current_stage_status=row.stage_status or {},
            stage_key=stage_key,
            task_id=task["task_id"],
            actor=body.actor,
            result=body.result,
            next_version=next_version,
            execution_mode=body.execution_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    row.version = next_version
    row.status = "running" if is_automatic else "waiting_operator"
    row.stage_data = stage_data
    row.stage_status = stage_status
    row.regenerate_log = [*(row.regenerate_log or []), complete_entry]
    row.last_task_id = task["task_id"]
    await db.flush()
    await db.refresh(row)

    payload = FilmWorkflowMutationRead.model_validate(
        {
            "workflow": _workflow_state_payload(snapshot, row),
            "task": task,
            "event": complete_entry,
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


async def _cleanup_stale_text_to_drama_scope(db: AsyncSession, project_id: str) -> None:
    """Remove orphan rows left by interrupted local text-to-drama creation."""

    chapter_rows = await db.execute(select(Chapter.id).where(Chapter.project_id == project_id))
    chapter_ids = [str(item) for item in chapter_rows.scalars().all()]
    shot_ids: list[str] = []
    if chapter_ids:
        shot_rows = await db.execute(select(Shot.id).where(Shot.chapter_id.in_(chapter_ids)))
        shot_ids = [str(item) for item in shot_rows.scalars().all()]

    character_rows = await db.execute(select(Character.id).where(Character.project_id == project_id))
    character_ids = [str(item) for item in character_rows.scalars().all()]
    scoped_prefix = f"{project_id[:42]}-%"

    if shot_ids:
        await db.execute(delete(ShotDialogLine).where(ShotDialogLine.shot_detail_id.in_(shot_ids)))
        await db.execute(delete(ShotFrameImage).where(ShotFrameImage.shot_detail_id.in_(shot_ids)))
        await db.execute(delete(ShotExtractedCandidate).where(ShotExtractedCandidate.shot_id.in_(shot_ids)))
        await db.execute(delete(ShotExtractedDialogueCandidate).where(ShotExtractedDialogueCandidate.shot_id.in_(shot_ids)))
        await db.execute(delete(ShotCharacterLink).where(ShotCharacterLink.shot_id.in_(shot_ids)))
        await db.execute(delete(ShotDetail).where(ShotDetail.id.in_(shot_ids)))
        await db.execute(delete(Shot).where(Shot.id.in_(shot_ids)))
        await db.execute(delete(GenerationTaskLink).where(GenerationTaskLink.relation_entity_id.in_(shot_ids)))

    if character_ids:
        await db.execute(delete(CharacterPropLink).where(CharacterPropLink.character_id.in_(character_ids)))
        await db.execute(delete(CharacterImage).where(CharacterImage.character_id.in_(character_ids)))

    await db.execute(delete(ProjectActorLink).where(ProjectActorLink.project_id == project_id))
    await db.execute(delete(ProjectSceneLink).where(ProjectSceneLink.project_id == project_id))
    await db.execute(delete(ProjectPropLink).where(ProjectPropLink.project_id == project_id))
    await db.execute(delete(ProjectCostumeLink).where(ProjectCostumeLink.project_id == project_id))
    await db.execute(delete(Character).where(Character.project_id == project_id))
    await db.execute(delete(Chapter).where(Chapter.project_id == project_id))
    await db.execute(delete(CineForgeWorkflowState).where(CineForgeWorkflowState.project_id == project_id))

    # Asset tables have global names, so stale scoped assets must be removed too.
    actor_rows = await db.execute(select(Actor.id).where(Actor.id.like(scoped_prefix)))
    actor_ids = [str(item) for item in actor_rows.scalars().all()]
    costume_rows = await db.execute(select(Costume.id).where(Costume.id.like(scoped_prefix)))
    costume_ids = [str(item) for item in costume_rows.scalars().all()]
    scene_rows = await db.execute(select(Scene.id).where(Scene.id.like(scoped_prefix)))
    scene_ids = [str(item) for item in scene_rows.scalars().all()]
    prop_rows = await db.execute(select(Prop.id).where(Prop.id.like(scoped_prefix)))
    prop_ids = [str(item) for item in prop_rows.scalars().all()]

    if actor_ids:
        await db.execute(delete(ActorImage).where(ActorImage.actor_id.in_(actor_ids)))
        await db.execute(delete(Actor).where(Actor.id.in_(actor_ids)))
    if costume_ids:
        await db.execute(delete(CostumeImage).where(CostumeImage.costume_id.in_(costume_ids)))
        await db.execute(delete(Costume).where(Costume.id.in_(costume_ids)))
    if scene_ids:
        await db.execute(delete(SceneImage).where(SceneImage.scene_id.in_(scene_ids)))
        await db.execute(delete(Scene).where(Scene.id.in_(scene_ids)))
    if prop_ids:
        await db.execute(delete(PropImage).where(PropImage.prop_id.in_(prop_ids)))
        await db.execute(delete(Prop).where(Prop.id.in_(prop_ids)))


def _persist_text_to_drama_assets(
    db: AsyncSession,
    *,
    project_id: str,
    project_name: str,
    blueprint: TextToDramaBlueprint,
    style: ProjectStyle,
    visual_style: ProjectVisualStyle,
) -> dict[str, dict[str, str]]:
    """Persist the generated asset bible before any shot can enter production."""

    ids: dict[str, dict[str, str]] = {
        "characters": {},
        "actors": {},
        "costumes": {},
        "scenes": {},
        "props": {},
    }

    for index, scene_seed in enumerate(blueprint.scenes, start=1):
        scene_id = _scoped_id(project_id, "scene", index)
        ids["scenes"][scene_seed.key] = scene_id
        db.add(
            Scene(
                id=scene_id,
                name=_scoped_name(project_name, scene_seed.name, project_id),
                description=scene_seed.description,
                style=style,
                visual_style=visual_style,
                view_count=2,
                tags=["text_to_drama", "scene_bible"],
            )
        )
        db.add(ProjectSceneLink(project_id=project_id, chapter_id=None, shot_id=None, scene_id=scene_id))
        db.add(SceneImage(scene_id=scene_id, quality_level=AssetQualityLevel.low, view_angle=AssetViewAngle.front))

    for index, prop_seed in enumerate(blueprint.props, start=1):
        prop_id = _scoped_id(project_id, "prop", index)
        ids["props"][prop_seed.key] = prop_id
        db.add(
            Prop(
                id=prop_id,
                name=_scoped_name(project_name, prop_seed.name, project_id),
                description=prop_seed.description,
                style=style,
                visual_style=visual_style,
                view_count=2,
                tags=["text_to_drama", "prop_bible"],
            )
        )
        db.add(ProjectPropLink(project_id=project_id, chapter_id=None, shot_id=None, prop_id=prop_id))
        db.add(PropImage(prop_id=prop_id, quality_level=AssetQualityLevel.low, view_angle=AssetViewAngle.front))

    for index, character_seed in enumerate(blueprint.characters, start=1):
        actor_id = _scoped_id(project_id, "actor", index)
        costume_id = _scoped_id(project_id, "costume", index)
        character_id = _scoped_id(project_id, "char", index)
        ids["actors"][character_seed.key] = actor_id
        ids["costumes"][character_seed.key] = costume_id
        ids["characters"][character_seed.key] = character_id
        db.add(
            Actor(
                id=actor_id,
                name=_scoped_name(project_name, f"{character_seed.name}形象", project_id),
                description=character_seed.description,
                style=style,
                visual_style=visual_style,
                view_count=4,
                tags=["text_to_drama", "identity_lock", *character_seed.traits],
            )
        )
        db.add(
            Costume(
                id=costume_id,
                name=_scoped_name(project_name, f"{character_seed.name}基准服装", project_id),
                description=character_seed.costume,
                style=style,
                visual_style=visual_style,
                view_count=2,
                tags=["text_to_drama", "costume_lock"],
            )
        )
        db.add(
            Character(
                id=character_id,
                project_id=project_id,
                name=character_seed.name,
                description=f"{character_seed.description}\n服装锁定：{character_seed.costume}",
                style=style,
                visual_style=visual_style,
                actor_id=actor_id,
                costume_id=costume_id,
            )
        )
        db.add(ProjectActorLink(project_id=project_id, chapter_id=None, shot_id=None, actor_id=actor_id))
        db.add(ProjectCostumeLink(project_id=project_id, chapter_id=None, shot_id=None, costume_id=costume_id))
        db.add(ActorImage(actor_id=actor_id, quality_level=AssetQualityLevel.low, view_angle=AssetViewAngle.front))
        db.add(
            CharacterImage(
                character_id=character_id,
                quality_level=AssetQualityLevel.low,
                view_angle=AssetViewAngle.front,
                is_primary=True,
            )
        )
        db.add(CostumeImage(costume_id=costume_id, quality_level=AssetQualityLevel.low, view_angle=AssetViewAngle.front))

    for prop_index, prop_seed in enumerate(blueprint.props):
        owner_key = prop_seed.owner_character_key or (blueprint.characters[0].key if blueprint.characters else "")
        owner_id = ids["characters"].get(owner_key)
        prop_id = ids["props"].get(prop_seed.key)
        if owner_id and prop_id:
            db.add(
                CharacterPropLink(
                    character_id=owner_id,
                    prop_id=prop_id,
                    index=prop_index,
                    note="text-to-drama auto asset bible",
                )
            )

    return ids


def _persist_shot_story_assets(
    db: AsyncSession,
    *,
    project_id: str,
    chapter_id: str,
    shot_id: str,
    shot_seed: Any,
    asset_ids: dict[str, dict[str, str]],
) -> None:
    """Attach generated storyboard assets to a shot so shooting has hard prerequisites."""

    scene_id = asset_ids["scenes"].get(shot_seed.scene_key)
    if scene_id:
        db.add(ProjectSceneLink(project_id=project_id, chapter_id=chapter_id, shot_id=shot_id, scene_id=scene_id))
        db.add(
            ShotExtractedCandidate(
                shot_id=shot_id,
                candidate_type=ShotCandidateType.scene,
                candidate_name=shot_seed.scene_key,
                candidate_status=ShotCandidateStatus.linked,
                linked_entity_id=scene_id,
                source="text_to_drama",
            )
        )

    for index, character_key in enumerate(shot_seed.character_keys):
        character_id = asset_ids["characters"].get(character_key)
        actor_id = asset_ids["actors"].get(character_key)
        costume_id = asset_ids["costumes"].get(character_key)
        if character_id:
            db.add(ShotCharacterLink(shot_id=shot_id, character_id=character_id, index=index, note="auto storyboard cast"))
            db.add(
                ShotExtractedCandidate(
                    shot_id=shot_id,
                    candidate_type=ShotCandidateType.character,
                    candidate_name=character_key,
                    candidate_status=ShotCandidateStatus.linked,
                    linked_entity_id=character_id,
                    source="text_to_drama",
                )
            )
        if actor_id:
            db.add(ProjectActorLink(project_id=project_id, chapter_id=chapter_id, shot_id=shot_id, actor_id=actor_id))
        if costume_id:
            db.add(ProjectCostumeLink(project_id=project_id, chapter_id=chapter_id, shot_id=shot_id, costume_id=costume_id))

    for prop_key in shot_seed.prop_keys:
        prop_id = asset_ids["props"].get(prop_key)
        if not prop_id:
            continue
        db.add(ProjectPropLink(project_id=project_id, chapter_id=chapter_id, shot_id=shot_id, prop_id=prop_id))
        db.add(
            ShotExtractedCandidate(
                shot_id=shot_id,
                candidate_type=ShotCandidateType.prop,
                candidate_name=prop_key,
                candidate_status=ShotCandidateStatus.linked,
                linked_entity_id=prop_id,
                source="text_to_drama",
            )
        )

    for frame_type in (ShotFrameType.first, ShotFrameType.key, ShotFrameType.last):
        db.add(ShotFrameImage(shot_detail_id=shot_id, frame_type=frame_type, format="png"))

    for line_index, line in enumerate(shot_seed.dialogue):
        speaker_key = line.get("speaker_key")
        db.add(
            ShotDialogLine(
                shot_detail_id=shot_id,
                index=line_index,
                text=line.get("text") or "",
                line_mode=DialogueLineMode.dialogue,
                speaker_character_id=asset_ids["characters"].get(speaker_key or ""),
                speaker_name=line.get("speaker_name"),
            )
        )


async def _record_reference_harvest_tasks(
    db: AsyncSession,
    *,
    workflow_id: str,
    project_id: str,
    reference_harvest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Queue per-character web reference harvesting without downloading media blindly."""

    items = reference_harvest.get("items") if isinstance(reference_harvest, dict) else []
    if not isinstance(items, list):
        return []

    tasks: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tasks.append(
            await _record_workflow_task(
                db,
                workflow_id=workflow_id,
                task_kind="cineforge_reference_harvest",
                payload={
                    "project_id": project_id,
                    "workflow_id": workflow_id,
                    "stage": "asset_pipeline.reference_harvest",
                    "policy": reference_harvest.get("policy"),
                    **item,
                },
                terminal=False,
                purpose="collect candidate web image/video references and licensing metadata for one character",
            )
        )
    return tasks


def _scoped_id(project_id: str, prefix: str, index: int) -> str:
    return f"{project_id[:42]}-{prefix}-{index:03d}"[:64]


def _scoped_name(project_name: str, name: str, project_id: str) -> str:
    return f"{project_name} · {name} · {project_id[-6:]}"[:255]


def _title_from_source_text(source_text: str) -> str:
    first_line = next((line.strip() for line in source_text.splitlines() if line.strip()), "")
    if not first_line:
        return "AI 漫剧项目"
    return first_line[:32]


def _stable_seed_from_text(source_text: str) -> int:
    seed = 0
    for index, char in enumerate(source_text[:4000], start=1):
        seed = (seed + index * ord(char)) % 100000
    return seed


def _summary_from_text(text: str, limit: int = 120) -> str:
    normalized = " ".join(text.strip().split())
    return normalized[:limit] if normalized else "待生成剧情摘要"


def _split_source_text(source_text: str, episode_count: int) -> list[str]:
    normalized = source_text.strip()
    if episode_count <= 1:
        return [normalized]
    paragraphs = [part.strip() for part in normalized.splitlines() if part.strip()]
    if len(paragraphs) >= episode_count:
        groups = [[] for _ in range(episode_count)]
        for index, paragraph in enumerate(paragraphs):
            groups[index % episode_count].append(paragraph)
        return ["\n".join(group).strip() or normalized for group in groups]

    chunk_size = max(1, (len(normalized) + episode_count - 1) // episode_count)
    return [
        normalized[index * chunk_size : (index + 1) * chunk_size].strip() or normalized
        for index in range(episode_count)
    ]


def _shot_excerpts(chapter_text: str, shot_count: int) -> list[str]:
    compact = " ".join(chapter_text.strip().split())
    if not compact:
        return ["待生成镜头内容" for _ in range(shot_count)]
    chunk_size = max(1, (len(compact) + shot_count - 1) // shot_count)
    excerpts = [
        compact[index * chunk_size : (index + 1) * chunk_size].strip()
        for index in range(shot_count)
    ]
    return [excerpt or compact[:120] for excerpt in excerpts]


def _workflow_automation_patch(mode: str) -> dict[str, dict[str, Any]]:
    is_auto = mode == "automatic"
    return {
        str(stage["key"]): {
            "mode": mode,
            "auto_advance": is_auto,
            "stop_after_stage": not is_auto,
            "manual_allowed": True,
        }
        for stage in CINEFORGE_WORKFLOW_STAGES
    }


def _with_stage_data(
    current: dict[str, Any],
    patches: dict[str, dict[str, Any]],
    *,
    automation_patch: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    data = dict(current or {})
    for stage in CINEFORGE_WORKFLOW_STAGES:
        key = str(stage["key"])
        stage_data = dict(data.get(key) or {})
        stage_data.update(patches.get(key, {}))
        stage_data["automation"] = automation_patch[key]
        data[key] = stage_data
    return data


def _with_stage_status(
    current: dict[str, Any],
    *,
    automation_patch: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    status_data = dict(current or {})
    for stage in CINEFORGE_WORKFLOW_STAGES:
        key = str(stage["key"])
        stage_status = dict(status_data.get(key) or {})
        stage_status["automation"] = automation_patch[key]
        if key == "workflow_architecture":
            stage_status.setdefault("state", "active")
        status_data[key] = stage_status
    return status_data


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
