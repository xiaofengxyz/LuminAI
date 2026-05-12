from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


PIPELINE_STAGES: list[dict[str, str]] = [
    {
        "key": "novel_script",
        "title": "Novel / Script",
        "owner": "Jellyfish Script Workspace",
        "description": "章节原文、精简文本和剧本理解是整个工业链路的源头。",
    },
    {
        "key": "story_graph",
        "title": "Story Graph",
        "owner": "Jellyfish Shot System",
        "description": "将章节拆成有顺序、可追踪的分镜图谱，避免长剧情丢状态。",
    },
    {
        "key": "director_planner",
        "title": "Director Planner",
        "owner": "Director DSL Layer",
        "description": "把景别、机位、运镜、节奏和情绪转成导演可执行计划。",
    },
    {
        "key": "film_core",
        "title": "Film Core",
        "owner": "LuminAI Film Core",
        "description": "集中管理角色、服装、道具、场景、镜头连续性和批量状态。",
    },
    {
        "key": "prompt_compiler",
        "title": "Prompt Compiler",
        "owner": "Prompt Compiler",
        "description": "从结构化状态编译提示词，减少手写 prompt 漂移。",
    },
    {
        "key": "runtime_adapter",
        "title": "Runtime Adapter",
        "owner": "Runtime Abstraction",
        "description": "把影片状态转成模型无关的渲染请求，而不是绑定单一供应商。",
    },
    {
        "key": "render_runtime",
        "title": "Render Runtime",
        "owner": "Jellyfish Task Runtime",
        "description": "通过任务中心追踪图片、视频、字幕和后期合成等异步任务。",
    },
    {
        "key": "video_models",
        "title": "Video Models",
        "owner": "Provider Registry",
        "description": "面向 Kling、Wan/Vidu 等视频模型保留可替换执行边界。",
    },
    {
        "key": "qa_engine",
        "title": "QA Engine",
        "owner": "Automatic QA",
        "description": "对角色脸、服装、关键帧、提示词和镜头连续性输出结构化问题。",
    },
    {
        "key": "retry_engine",
        "title": "Retry Engine",
        "owner": "Automatic Retry",
        "description": "只重试失败镜头，并携带可解释的修复补丁和参数覆盖。",
    },
    {
        "key": "final_editing",
        "title": "Final Editing",
        "owner": "Jellyfish Editor / FFmpeg Layer",
        "description": "把通过 QA 的镜头、字幕、TTS、BGM 和转场汇成最终交付片。",
    },
]


REFERENCE_PROJECTS: list[dict[str, str]] = [
    {
        "name": "Jellyfish",
        "url": "https://github.com/Forget-C/Jellyfish",
        "adopted_layer": "Studio OS / operator workspace",
        "rule": "继续作为主 UI、资产、分镜、任务中心和后期入口，不另起一套 UI。",
    },
    {
        "name": "huobao-drama",
        "url": "https://github.com/chatfire-AI/huobao-drama",
        "adopted_layer": "Runtime / ffmpeg / subtitle / render queue",
        "rule": "只学习运行时编排，不把 Film Core 写成渲染脚本集合。",
    },
    {
        "name": "director_ai",
        "url": "https://github.com/freestylefly/director_ai",
        "adopted_layer": "Director DSL / shot language",
        "rule": "吸收镜头、场景、时间线和转场抽象，保持导演层可替换。",
    },
    {
        "name": "BigBanana-AI-Director",
        "url": "https://github.com/shuyu-labs/BigBanana-AI-Director",
        "adopted_layer": "Emotional camera and pacing rules",
        "rule": "把情绪到运镜映射做成规则层，而不是散落在提示词里。",
    },
    {
        "name": "ArcReel",
        "url": "https://github.com/ArcReel/ArcReel",
        "adopted_layer": "Novel-to-video consistency workflow",
        "rule": "参考长流程和资产库思路，但在 Jellyfish 内用单工作台闭环落地。",
    },
    {
        "name": "MoneyPrinterTurbo",
        "url": "https://github.com/harry0703/MoneyPrinterTurbo",
        "adopted_layer": "Subtitle, audio, and final packaging pipeline",
        "rule": "学习轻量交付链路，避免把短视频自动化误当电影级连续性核心。",
    },
]


IMPLEMENTATION_PHASES: list[dict[str, str]] = [
    {
        "key": "phase_1_foundation",
        "phase": "Phase 1",
        "title": "Package Skeleton / Domain Foundation",
        "owner": "LuminAI Core",
        "status": "done",
        "evidence": "Python package skeleton, Pydantic domain models, provider registry, and media reference resolver are implemented.",
        "surface": "src/apps/comic_gen, src/models, src/utils, tests/test_provider_registry.py",
    },
    {
        "key": "phase_2_comic_pipeline",
        "phase": "Phase 2",
        "title": "Comic Generation Pipeline",
        "owner": "Series Factory",
        "status": "done",
        "evidence": "Series/episode asset inheritance, prompt fallback, local snapshots, and provider routing are covered by tests.",
        "surface": "src/apps/comic_gen, tests/test_series.py, tests/test_local_only_flow.py",
    },
    {
        "key": "phase_3_runtime_adapters",
        "phase": "Phase 3",
        "title": "Runtime Adapters",
        "owner": "Runtime Abstraction",
        "status": "done",
        "evidence": "Wan/DashScope, Kling, Vidu, image references, video params, and media routing stay behind adapter contracts.",
        "surface": "src/models, src/utils/provider_media.py, tests/test_*provider*_routing.py",
    },
    {
        "key": "phase_4_film_primitives",
        "phase": "Phase 4",
        "title": "Industrial Film Primitives",
        "owner": "Film Core",
        "status": "done",
        "evidence": "ECS-inspired registries, workflow graph, film state, prompt compiler, QA, retry, and batch planning are implemented.",
        "surface": "src/film_engine/{ecs,graph,state,prompt_compiler,qa,retry,batch}.py",
    },
    {
        "key": "phase_5_platform_bridge",
        "phase": "Phase 5",
        "title": "Jellyfish Platform Bridge",
        "owner": "Platform Boundary",
        "status": "done",
        "evidence": "Project/chapter/shot/asset/task contracts map into Film Core render and continuity boundaries.",
        "surface": "src/film_engine/platform.py, tests/test_jellyfish_platform_bridge.py",
    },
    {
        "key": "phase_6_record_mapping",
        "phase": "Phase 6",
        "title": "Jellyfish Record/API Mapping",
        "owner": "Jellyfish Mapper",
        "status": "done",
        "evidence": "Real Jellyfish-shaped records can be converted without importing ORM models into the Film Core.",
        "surface": "src/film_engine/jellyfish.py, tests/test_jellyfish_record_mapper.py",
    },
    {
        "key": "phase_7_post_production",
        "phase": "Phase 7",
        "title": "Post-Production Runtime Graft",
        "owner": "Post Pipeline",
        "status": "done",
        "evidence": "TTS, subtitle, FFmpeg compose, concat, and final export steps are planned as runtime-neutral work.",
        "surface": "src/film_engine/post_production.py, tests/test_post_production_planner.py",
    },
    {
        "key": "phase_8_director_consistency",
        "phase": "Phase 8",
        "title": "Director And Consistency Layers",
        "owner": "Director DSL Layer",
        "status": "done",
        "evidence": "Director rules, character/scene bibles, consistency context, and prompt compiler handoff are implemented.",
        "surface": "src/film_engine/director.py, tests/test_director_consistency.py",
    },
    {
        "key": "phase_9_qa_retry_batch",
        "phase": "Phase 9",
        "title": "QA / Retry / Batch Closure",
        "owner": "Closed-Loop Production",
        "status": "done",
        "evidence": "Closed-loop chapter planning exposes render requests, QA reports, retry requests, and post-production planning.",
        "surface": "src/film_engine/production.py, tests/test_closed_loop_production.py",
    },
]


CINEFORGE_WORKFLOW_STAGES: list[dict[str, Any]] = [
    {
        "key": "workflow_architecture",
        "title": "Workflow-First Architecture",
        "owner": "Jellyfish Workflow Core",
        "prompt_file": "01_WORKFLOW_ARCHITECTURE_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "graph_state_integrity",
        "default_execution_mode": "automatic",
    },
    {
        "key": "novel_engine",
        "title": "Novel Engine",
        "owner": "Story System",
        "prompt_file": "02_STAGE1_NOVEL_ENGINE_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "story_continuity",
        "default_execution_mode": "automatic",
    },
    {
        "key": "asset_pipeline",
        "title": "Drama Asset Pipeline",
        "owner": "Character / Scene Bible",
        "prompt_file": "03_STAGE2_ASSET_PIPELINE_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "asset_consistency",
        "default_execution_mode": "automatic",
    },
    {
        "key": "image_runtime",
        "title": "Image Runtime",
        "owner": "FLUX / SDXL / StoryDiffusion / ComfyUI Adapter",
        "prompt_file": "04_STAGE3_IMAGE_RUNTIME_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "reference_image_quality",
        "default_execution_mode": "automatic",
    },
    {
        "key": "video_runtime",
        "title": "Video Runtime",
        "owner": "Seedance / Kling / Veo / Wan / Sora Adapter",
        "prompt_file": "05_STAGE4_VIDEO_RUNTIME_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "shot_motion_quality",
        "default_execution_mode": "automatic",
    },
    {
        "key": "qa_retry_engine",
        "title": "QA And Retry Engine",
        "owner": "Closed-Loop QA",
        "prompt_file": "06_QA_RETRY_ENGINE_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "retry_patch_quality",
        "default_execution_mode": "automatic",
    },
    {
        "key": "studio_ui",
        "title": "CineForge Studio UI",
        "owner": "Jellyfish Project Workbench",
        "prompt_file": "07_STUDIO_UI_PROMPT.md",
        "editable": True,
        "regeneratable": False,
        "qa_gate": "operator_surface_complete",
        "default_execution_mode": "manual",
    },
    {
        "key": "data_schema",
        "title": "Production Data Schema",
        "owner": "Workflow State Ledger",
        "prompt_file": "08_DATA_SCHEMA_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "schema_contract_complete",
        "default_execution_mode": "automatic",
    },
    {
        "key": "final_integration",
        "title": "AI Drama Operating System",
        "owner": "Industrial Production Loop",
        "prompt_file": "09_FINAL_INTEGRATION_PROMPT.md",
        "editable": True,
        "regeneratable": True,
        "qa_gate": "end_to_end_executable",
        "default_execution_mode": "automatic",
    },
]


@dataclass(frozen=True)
class IndustrialProjectSnapshot:
    project_id: str
    project_name: str
    project_style: str
    visual_style: str
    seed: int
    unify_style: bool
    chapter_id: str | None = None
    chapter_title: str | None = None
    chapter_index: int | None = None
    script_text_length: int = 0
    condensed_text_length: int = 0
    chapter_count: int = 0
    shot_count: int = 0
    ready_shot_count: int = 0
    generating_shot_count: int = 0
    generated_video_count: int = 0
    detail_count: int = 0
    frame_image_count: int = 0
    dialogue_line_count: int = 0
    character_count: int = 0
    actor_link_count: int = 0
    scene_link_count: int = 0
    prop_link_count: int = 0
    costume_link_count: int = 0
    pending_candidate_count: int = 0
    pending_dialogue_count: int = 0
    task_link_count: int = 0
    accepted_video_task_count: int = 0
    shot_ids: tuple[str, ...] = ()
    ready_shot_ids: tuple[str, ...] = ()
    generated_video_shot_ids: tuple[str, ...] = ()

    @property
    def has_script(self) -> bool:
        return self.script_text_length > 0 or self.condensed_text_length > 0

    @property
    def has_story_graph(self) -> bool:
        return self.shot_count > 0

    @property
    def has_director_plan(self) -> bool:
        return self.detail_count > 0

    @property
    def has_asset_bible(self) -> bool:
        return (
            self.character_count > 0
            and self.actor_link_count >= self.character_count
            and self.scene_link_count > 0
            and self.costume_link_count > 0
            and self.prop_link_count > 0
        )


def build_industrial_overview(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    """Build the operator-facing Film Core overview from a Jellyfish snapshot."""

    stages = _build_stage_index(snapshot)
    pain_points = _build_pain_points(snapshot)
    asset_health = _build_asset_health(snapshot)
    qa_retry = _build_qa_retry(snapshot)
    next_actions = _build_next_actions(snapshot)

    return {
        "workflow_mode": "jellyfish_native_industrial_closed_loop",
        "project": {
            "id": snapshot.project_id,
            "name": snapshot.project_name,
            "style": snapshot.project_style,
            "visual_style": snapshot.visual_style,
            "seed": snapshot.seed,
            "unify_style": snapshot.unify_style,
        },
        "chapter": {
            "id": snapshot.chapter_id,
            "title": snapshot.chapter_title,
            "index": snapshot.chapter_index,
        }
        if snapshot.chapter_id
        else None,
        "industrial_score": _industrial_score(snapshot),
        "pipeline": stages,
        "asset_health": asset_health,
        "qa_retry": qa_retry,
        "pain_points": pain_points,
        "reference_projects": REFERENCE_PROJECTS,
        "creation_entries": _build_creation_entries(snapshot),
        "shooting_gate": _build_shooting_gate(snapshot),
        "operator_next_actions": next_actions,
        "implementation_status": build_implementation_status(),
        "implementation_phases": IMPLEMENTATION_PHASES,
    }


def build_implementation_status() -> dict[str, Any]:
    """Summarize the nine starter-kit implementation phases for the UI."""

    total = len(IMPLEMENTATION_PHASES)
    completed = sum(1 for item in IMPLEMENTATION_PHASES if item["status"] == "done")
    return {
        "total_phases": total,
        "completed_phases": completed,
        "status": "complete" if completed == total else "in_progress",
        "label": f"{completed}/{total} starter-kit phases complete",
        "evidence": "The nine implementation phases are implemented in LuminAI core modules; Jellyfish-native Film Core UI/API is the product surface that shows them.",
    }


def build_closed_loop_plan(
    snapshot: IndustrialProjectSnapshot,
    *,
    provider: str = "runtime_adapter",
    model: str = "project_default_video_model",
    output_dir: str = "output/jellyfish-industrial",
) -> dict[str, Any]:
    """Build a runtime-neutral closed-loop plan preview for one project scope."""

    overview = build_industrial_overview(snapshot)
    shooting_gate = overview["shooting_gate"]
    shot_slots = max(snapshot.shot_count, snapshot.ready_shot_count, snapshot.generated_video_count)
    render_queue = [
        {
            "slot": index,
            "shot_ref": _shot_ref(snapshot, index),
            "provider": provider,
            "model": model,
            "output_path": f"{output_dir}/{snapshot.project_id}/{snapshot.chapter_id or 'project'}-{index:03d}.mp4",
            "references_required": ["character_identity", "costume", "scene_keyframe"],
            "compiled_prompt_contract": {
                "source": "Film Core state + Director DSL + Jellyfish assets",
                "must_include": ["character bible", "costume lock", "camera language", "negative drift terms"],
            },
        }
        for index in range(1, shot_slots + 1)
        if shooting_gate["ready"]
    ]
    retry_candidates = max(0, snapshot.ready_shot_count - snapshot.generated_video_count)
    return {
        "plan_id": f"industrial-{snapshot.project_id}-{snapshot.chapter_id or 'project'}",
        "workflow": [stage["key"] for stage in PIPELINE_STAGES],
        "overview": overview,
        "render_queue": render_queue,
        "qa_policy": {
            "face_similarity_min": 0.86,
            "outfit_similarity_min": 0.82,
            "clip_score_min": 0.28,
            "continuity_checks": [
                "character identity drift",
                "costume drift",
                "scene/light continuity",
                "shot action completeness",
            ],
        },
        "retry_policy": {
            "max_attempts": 3,
            "planned_retry_candidates": retry_candidates,
            "repair_patch_contract": [
                "increase identity reference strength",
                "lock costume and prop clauses",
                "lower randomness",
                "reuse accepted first/key frame references",
            ],
        },
        "post_production": {
            "enabled": snapshot.generated_video_count > 0,
            "steps": ["tts_alignment", "subtitle_pack", "shot_concat", "bgm_mix", "final_export"],
            "write_back_targets": ["files", "generation_task_links", "shots.generated_video_file_id"],
        },
        "blockers": [
            *[item for item in overview["operator_next_actions"] if item["severity"] == "high"],
            *[
                {"severity": "high", "action": blocker}
                for blocker in shooting_gate["blockers"]
                if not shooting_gate["ready"]
            ],
        ],
    }


def build_writeback_summary(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    """Summarize which Jellyfish records an industrial run can write back to."""

    render_targets = len(snapshot.ready_shot_ids) or snapshot.ready_shot_count
    qa_targets = len(snapshot.generated_video_shot_ids) or snapshot.generated_video_count
    retry_targets = max(0, snapshot.ready_shot_count - snapshot.generated_video_count)
    return {
        "render_targets": render_targets,
        "qa_targets": qa_targets,
        "retry_targets": retry_targets,
        "post_production_targets": 1 if snapshot.generated_video_count > 0 else 0,
        "writes_generation_tasks": True,
        "writes_task_links": True,
        "writes_shot_video_links": False,
        "note": (
            "This run creates Jellyfish task/link records for the closed loop. "
            "Provider workers attach files and update shots after real rendering completes."
        ),
    }


def build_cineforge_workflow_state(
    snapshot: IndustrialProjectSnapshot,
    *,
    workflow_id: str | None = None,
    status: str = "draft",
    version: int = 1,
    stage_data: dict[str, Any] | None = None,
    stage_status: dict[str, Any] | None = None,
    edit_log: list[dict[str, Any]] | None = None,
    regenerate_log: list[dict[str, Any]] | None = None,
    last_task_id: str | None = None,
) -> dict[str, Any]:
    """Build the persisted CineForge workflow ledger for API/UI consumption."""

    default_data = _default_cineforge_stage_data(snapshot)
    merged_data = _deep_merge(default_data, stage_data or {})
    default_status = _default_cineforge_stage_status(snapshot)
    merged_status = _deep_merge(default_status, stage_status or {})
    stage_entries = []
    for stage in CINEFORGE_WORKFLOW_STAGES:
        key = str(stage["key"])
        automation = _stage_automation(stage, merged_data.get(key, {}), merged_status.get(key, {}))
        stage_entries.append(
            {
                **stage,
                "automation": automation,
                "status": merged_status.get(key, {}),
                "data": merged_data.get(key, {}),
            }
        )

    return {
        "id": workflow_id or "",
        "workflow_key": "cineforge_ai_drama_os",
        "version": version,
        "status": status,
        "scope": {
            "project_id": snapshot.project_id,
            "project_name": snapshot.project_name,
            "chapter_id": snapshot.chapter_id,
            "chapter_title": snapshot.chapter_title,
        },
        "persisted": bool(workflow_id),
        "stage_count": len(CINEFORGE_WORKFLOW_STAGES),
        "stages": stage_entries,
        "stage_data": merged_data,
        "stage_status": merged_status,
        "edit_log": list(edit_log or []),
        "regenerate_log": list(regenerate_log or []),
        "last_task_id": last_task_id,
        "edit_contract": {
            "method": "PATCH",
            "path": "/api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}",
            "effect": "Merges a structured patch into the persisted stage data and increments the workflow version.",
        },
        "regenerate_contract": {
            "method": "POST",
            "path": "/api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/regenerate",
            "effect": "Creates a Jellyfish generation task for targeted regeneration without discarding approved stages.",
        },
        "automation_contract": {
            "mode_values": ["automatic", "manual"],
            "automatic": "When a stage completes, the workflow records the result and marks the next stage active.",
            "manual": "When a stage completes, the workflow records a waiting_operator gate and stops for user review.",
        },
    }


def patch_cineforge_stage_data(
    *,
    current_stage_data: dict[str, Any],
    current_stage_status: dict[str, Any],
    stage_key: str,
    patch: dict[str, Any],
    actor: str,
    note: str,
    next_version: int,
    execution_mode: str | None = None,
    auto_advance: bool | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Apply an operator edit to one workflow stage without touching other stages."""

    stage = ensure_cineforge_stage(stage_key)
    stage_data = deepcopy(current_stage_data)
    stage_status = deepcopy(current_stage_status)
    stage_data[stage_key] = _deep_merge(stage_data.get(stage_key, {}), patch)
    automation = _stage_automation(stage, stage_data.get(stage_key, {}), stage_status.get(stage_key, {}))
    if execution_mode is not None or auto_advance is not None:
        automation = _automation_patch(
            stage=stage,
            current=automation,
            execution_mode=execution_mode,
            auto_advance=auto_advance,
        )
        stage_data[stage_key] = _deep_merge(stage_data.get(stage_key, {}), {"automation": automation})
    stage_status[stage_key] = _deep_merge(
        stage_status.get(stage_key, {}),
        {
            "state": "edited",
            "revision": next_version,
            "last_actor": actor,
            "last_note": note,
            "automation": automation,
            "updated_at": _utc_now_iso(),
        },
    )
    edit_entry = {
        "stage_key": stage_key,
        "actor": actor,
        "note": note,
        "patch": patch,
        "automation": automation,
        "version": next_version,
        "created_at": _utc_now_iso(),
    }
    return stage_data, stage_status, edit_entry


def build_cineforge_regenerate_payload(
    *,
    snapshot: IndustrialProjectSnapshot,
    workflow_id: str,
    stage_key: str,
    reason: str,
    patch: dict[str, Any],
    provider: str,
    model: str,
    next_version: int,
) -> dict[str, Any]:
    """Create a task payload that can later be consumed by provider-specific workers."""

    stage = ensure_cineforge_stage(stage_key)
    automation = _default_stage_automation(stage)
    return {
        "workflow_id": workflow_id,
        "workflow_key": "cineforge_ai_drama_os",
        "stage_key": stage_key,
        "stage_title": stage["title"],
        "reason": reason,
        "patch": patch,
        "provider": provider,
        "model": model,
        "version": next_version,
        "project_id": snapshot.project_id,
        "chapter_id": snapshot.chapter_id,
        "source_counts": {
            "script_chars": snapshot.script_text_length,
            "shots": snapshot.shot_count,
            "ready_shots": snapshot.ready_shot_count,
            "generated_videos": snapshot.generated_video_count,
            "characters": snapshot.character_count,
            "asset_links": (
                snapshot.actor_link_count
                + snapshot.scene_link_count
                + snapshot.prop_link_count
                + snapshot.costume_link_count
            ),
        },
        "qa_gate": stage["qa_gate"],
        "automation": automation,
    }


def mark_cineforge_regeneration_queued(
    *,
    current_stage_status: dict[str, Any],
    stage_key: str,
    task_id: str,
    actor: str,
    reason: str,
    next_version: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Mark a stage as queued for regeneration and return a history row."""

    ensure_cineforge_stage(stage_key)
    stage_status = deepcopy(current_stage_status)
    stage_status[stage_key] = _deep_merge(
        stage_status.get(stage_key, {}),
        {
            "state": "regeneration_queued",
            "revision": next_version,
            "last_task_id": task_id,
            "last_actor": actor,
            "last_note": reason,
            "updated_at": _utc_now_iso(),
        },
    )
    entry = {
        "stage_key": stage_key,
        "actor": actor,
        "reason": reason,
        "task_id": task_id,
        "version": next_version,
        "created_at": _utc_now_iso(),
    }
    return stage_status, entry


def complete_cineforge_stage(
    *,
    current_stage_data: dict[str, Any],
    current_stage_status: dict[str, Any],
    stage_key: str,
    task_id: str,
    actor: str,
    result: dict[str, Any],
    next_version: int,
    execution_mode: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Close one stage and either auto-activate the next stage or wait for the operator."""

    stage = ensure_cineforge_stage(stage_key)
    stage_data = deepcopy(current_stage_data)
    stage_status = deepcopy(current_stage_status)
    automation = _automation_patch(
        stage=stage,
        current=_stage_automation(stage, stage_data.get(stage_key, {}), stage_status.get(stage_key, {})),
        execution_mode=execution_mode,
        auto_advance=None,
    )
    is_auto = automation["mode"] == "automatic" and automation["auto_advance"]
    next_stage_key = _next_cineforge_stage_key(stage_key)
    next_state = "active" if is_auto and next_stage_key else None
    current_state = "completed" if is_auto else "waiting_operator"

    stage_data[stage_key] = _deep_merge(
        stage_data.get(stage_key, {}),
        {
            "automation": automation,
            "last_result": result,
        },
    )
    stage_status[stage_key] = _deep_merge(
        stage_status.get(stage_key, {}),
        {
            "state": current_state,
            "revision": next_version,
            "last_actor": actor,
            "last_task_id": task_id,
            "automation": automation,
            "completed_at": _utc_now_iso(),
        },
    )
    if next_stage_key and next_state:
        next_stage = ensure_cineforge_stage(next_stage_key)
        next_automation = _stage_automation(
            next_stage,
            stage_data.get(next_stage_key, {}),
            stage_status.get(next_stage_key, {}),
        )
        stage_status[next_stage_key] = _deep_merge(
            stage_status.get(next_stage_key, {}),
            {
                "state": next_state,
                "revision": next_version,
                "auto_started_by_stage": stage_key,
                "auto_started_task_id": task_id,
                "automation": next_automation,
                "updated_at": _utc_now_iso(),
            },
        )

    entry = {
        "stage_key": stage_key,
        "actor": actor,
        "task_id": task_id,
        "result": result,
        "version": next_version,
        "automation": automation,
        "next_stage_key": next_stage_key,
        "next_stage_state": next_state or "operator_halt",
        "created_at": _utc_now_iso(),
    }
    return stage_data, stage_status, entry


def ensure_cineforge_stage(stage_key: str) -> dict[str, Any]:
    """Return the workflow stage spec or raise a clear error for invalid keys."""

    for stage in CINEFORGE_WORKFLOW_STAGES:
        if stage["key"] == stage_key:
            return stage
    valid = ", ".join(str(stage["key"]) for stage in CINEFORGE_WORKFLOW_STAGES)
    raise KeyError(f"Unknown CineForge workflow stage '{stage_key}'. Valid stages: {valid}")


def _default_stage_automation(stage: dict[str, Any]) -> dict[str, Any]:
    mode = _normalize_execution_mode(str(stage.get("default_execution_mode") or "automatic"))
    auto_advance = mode == "automatic"
    return {
        "mode": mode,
        "auto_advance": auto_advance,
        "stop_after_stage": not auto_advance,
        "manual_allowed": True,
        "next_stage_key": _next_cineforge_stage_key(str(stage["key"])),
    }


def _stage_automation(
    stage: dict[str, Any],
    stage_data: dict[str, Any],
    stage_status: dict[str, Any],
) -> dict[str, Any]:
    base = _default_stage_automation(stage)
    data_automation = stage_data.get("automation") if isinstance(stage_data, dict) else None
    status_automation = stage_status.get("automation") if isinstance(stage_status, dict) else None
    if isinstance(data_automation, dict):
        base = _deep_merge(base, data_automation)
    if isinstance(status_automation, dict):
        base = _deep_merge(base, status_automation)
    base["mode"] = _normalize_execution_mode(str(base.get("mode") or "automatic"))
    base["auto_advance"] = bool(base.get("auto_advance")) and base["mode"] == "automatic"
    base["stop_after_stage"] = not base["auto_advance"]
    base["next_stage_key"] = _next_cineforge_stage_key(str(stage["key"]))
    return base


def _automation_patch(
    *,
    stage: dict[str, Any],
    current: dict[str, Any],
    execution_mode: str | None,
    auto_advance: bool | None,
) -> dict[str, Any]:
    mode = _normalize_execution_mode(execution_mode or str(current.get("mode") or "automatic"))
    should_auto_advance = mode == "automatic" if auto_advance is None else bool(auto_advance) and mode == "automatic"
    return {
        **current,
        "mode": mode,
        "auto_advance": should_auto_advance,
        "stop_after_stage": not should_auto_advance,
        "manual_allowed": True,
        "next_stage_key": _next_cineforge_stage_key(str(stage["key"])),
    }


def _normalize_execution_mode(value: str) -> str:
    mode = (value or "automatic").strip().lower()
    if mode not in {"automatic", "manual"}:
        raise ValueError("execution_mode must be 'automatic' or 'manual'")
    return mode


def _next_cineforge_stage_key(stage_key: str) -> str | None:
    keys = [str(stage["key"]) for stage in CINEFORGE_WORKFLOW_STAGES]
    try:
        index = keys.index(stage_key)
    except ValueError:
        return None
    next_index = index + 1
    return keys[next_index] if next_index < len(keys) else None


def _default_cineforge_stage_data(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    shot_refs = list(snapshot.shot_ids or snapshot.ready_shot_ids)
    data = {
        "workflow_architecture": {
            "graph_order": [str(stage["key"]) for stage in CINEFORGE_WORKFLOW_STAGES],
            "persistence": "cineforge_workflow_states",
            "jellyfish_reuse": [
                "projects",
                "chapters",
                "shots",
                "project_*_links",
                "generation_tasks",
                "generation_task_links",
            ],
            "recoverability": "all operator edits and regeneration tasks are versioned",
        },
        "novel_engine": {
            "world_bible": {
                "title": snapshot.project_name,
                "style": snapshot.project_style,
                "visual_style": snapshot.visual_style,
                "seed": snapshot.seed,
                "unify_style": snapshot.unify_style,
            },
            "relationship_graph": {
                "character_count": snapshot.character_count,
                "actor_link_count": snapshot.actor_link_count,
            },
            "chapter_outline": {
                "chapter_count": snapshot.chapter_count,
                "focus_chapter": snapshot.chapter_title,
                "script_chars": snapshot.script_text_length,
                "condensed_chars": snapshot.condensed_text_length,
            },
            "cliffhanger_engine": {
                "policy": "each episode keeps an unresolved emotional or plot question",
                "candidate_source": "chapter ending + next chapter setup",
            },
        },
        "asset_pipeline": {
            "character_bible": {
                "character_count": snapshot.character_count,
                "identity_links": snapshot.actor_link_count,
            },
            "scene_bible": {
                "scene_links": snapshot.scene_link_count,
                "lighting_policy": "reuse scene references and lock lighting per shot",
            },
            "shot_graph": {
                "shot_count": snapshot.shot_count,
                "ready_shots": snapshot.ready_shot_count,
                "shot_refs": shot_refs,
            },
            "storyboard": {
                "frame_image_count": snapshot.frame_image_count,
                "dialogue_line_count": snapshot.dialogue_line_count,
            },
        },
        "image_runtime": {
            "adapters": ["flux", "sdxl", "storydiffusion", "comfyui"],
            "contract": "image requests must be compiled from character, scene, shot, and storyboard state",
            "reference_policy": ["identity lock", "costume lock", "scene keyframe", "first/key/last frame"],
        },
        "video_runtime": {
            "adapters": ["seedance", "kling", "veo", "wan2.1", "sora"],
            "contract": "video requests stay provider-neutral until runtime dispatch",
            "shot_constraints": ["duration", "ratio", "camera movement", "reference images", "negative drift terms"],
        },
        "qa_retry_engine": {
            "qa_policy": {
                "face_similarity_min": 0.86,
                "outfit_similarity_min": 0.82,
                "clip_score_min": 0.28,
                "continuity_checks": ["identity", "costume", "scene/light", "action completion"],
            },
            "retry_policy": {
                "max_attempts": 3,
                "target": "only failed shots",
                "patches": ["increase reference strength", "lock costume", "lower randomness"],
            },
            "current_inputs": {
                "generated_or_accepted_videos": snapshot.generated_video_count + snapshot.accepted_video_task_count,
                "planned_retry_candidates": max(0, snapshot.ready_shot_count - snapshot.generated_video_count),
            },
        },
        "studio_ui": {
            "surfaces": [
                "Projects -> Film Core",
                "Project Workbench -> Film Core",
                "/projects/{projectId}?tab=filmCore",
            ],
            "operator_actions": ["load workflow state", "edit stage", "queue stage regeneration", "create production tasks"],
        },
        "data_schema": {
            "schema_version": "cineforge.workflow.v1",
            "entities": [
                "workflow_state",
                "stage_data",
                "stage_status",
                "edit_log",
                "regenerate_log",
                "generation_task_link",
            ],
            "state_boundary": "Jellyfish owns persistence; provider workers own execution results.",
        },
        "final_integration": {
            "operating_system": "AI Drama Operating System",
            "workflow": [stage["key"] for stage in PIPELINE_STAGES],
            "batch_policy": "episode-by-episode closed loop with shared bibles and per-shot QA",
            "export_policy": "approved clips are handed to post-production for subtitles, audio, transitions, and final delivery",
        },
    }
    for stage in CINEFORGE_WORKFLOW_STAGES:
        key = str(stage["key"])
        data[key] = _deep_merge(data.get(key, {}), {"automation": _default_stage_automation(stage)})
    return data


def _default_cineforge_stage_status(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    generated_or_accepted = snapshot.generated_video_count + snapshot.accepted_video_task_count
    return {
        "workflow_architecture": _workflow_stage_status("ready", "state ledger and task ledger are available"),
        "novel_engine": _workflow_stage_status(
            "done" if snapshot.has_script else "blocked",
            f"script={snapshot.script_text_length}, condensed={snapshot.condensed_text_length}",
        ),
        "asset_pipeline": _workflow_stage_status(
            "done" if snapshot.has_asset_bible else "needs_input",
            (
                f"characters={snapshot.character_count}, actor_links={snapshot.actor_link_count}, "
                f"scene_links={snapshot.scene_link_count}, prop_links={snapshot.prop_link_count}, "
                f"costume_links={snapshot.costume_link_count}"
            ),
        ),
        "image_runtime": _workflow_stage_status(
            "ready" if snapshot.ready_shot_count > 0 else "waiting",
            f"frame_images={snapshot.frame_image_count}, ready_shots={snapshot.ready_shot_count}",
        ),
        "video_runtime": _workflow_stage_status(
            "ready" if snapshot.ready_shot_count > 0 else "waiting",
            f"ready_shots={snapshot.ready_shot_count}, generated_videos={snapshot.generated_video_count}",
        ),
        "qa_retry_engine": _workflow_stage_status(
            "ready" if generated_or_accepted > 0 else "waiting",
            f"qa_inputs={generated_or_accepted}",
        ),
        "studio_ui": _workflow_stage_status("done", "Film Core tab is mounted in Jellyfish Project Workbench"),
        "data_schema": _workflow_stage_status("ready", "workflow_state JSON schema is versioned"),
        "final_integration": _workflow_stage_status(
            "ready" if snapshot.ready_shot_count > 0 else "blocked",
            f"pipeline_nodes={len(PIPELINE_STAGES)}, ready_shots={snapshot.ready_shot_count}",
        ),
    }


def _workflow_stage_status(state: str, evidence: str) -> dict[str, Any]:
    return {
        "state": state,
        "evidence": evidence,
        "revision": 1,
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stage(
    key: str,
    *,
    status: str,
    evidence: str,
    next_action: str,
) -> dict[str, str]:
    base = next(item for item in PIPELINE_STAGES if item["key"] == key)
    return {
        **base,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _shot_ref(snapshot: IndustrialProjectSnapshot, index: int) -> str:
    if 1 <= index <= len(snapshot.shot_ids):
        return snapshot.shot_ids[index - 1]
    if 1 <= index <= len(snapshot.ready_shot_ids):
        return snapshot.ready_shot_ids[index - 1]
    return f"{snapshot.chapter_id or snapshot.project_id}-shot-{index:03d}"


def _build_stage_index(snapshot: IndustrialProjectSnapshot) -> list[dict[str, str]]:
    generated_or_accepted = snapshot.generated_video_count + snapshot.accepted_video_task_count
    return [
        _stage(
            "novel_script",
            status="done" if snapshot.has_script else "blocked",
            evidence=f"script={snapshot.script_text_length} chars, condensed={snapshot.condensed_text_length} chars",
            next_action="补齐章节原文或精简文本。" if not snapshot.has_script else "继续保持章节文本作为唯一剧情源。",
        ),
        _stage(
            "story_graph",
            status="done" if snapshot.has_story_graph else ("ready" if snapshot.has_script else "blocked"),
            evidence=f"chapters={snapshot.chapter_count}, shots={snapshot.shot_count}",
            next_action="运行分镜提取生成 Story Graph。" if not snapshot.has_story_graph else "检查分镜顺序和剧情因果。",
        ),
        _stage(
            "director_planner",
            status="done" if snapshot.has_director_plan else ("ready" if snapshot.has_story_graph else "blocked"),
            evidence=f"shot_details={snapshot.detail_count}, dialogues={snapshot.dialogue_line_count}",
            next_action="补齐景别、机位、运镜、情绪和动作拍点。" if not snapshot.has_director_plan else "复核节奏和镜头变化。",
        ),
        _stage(
            "film_core",
            status="done" if snapshot.has_asset_bible else ("warning" if snapshot.has_story_graph else "blocked"),
            evidence=(
                f"characters={snapshot.character_count}, actor_links={snapshot.actor_link_count}, "
                f"scene_links={snapshot.scene_link_count}, prop_links={snapshot.prop_link_count}, "
                f"costume_links={snapshot.costume_link_count}"
            ),
            next_action="把角色、演员、服装、场景、道具绑定为资产圣经。" if not snapshot.has_asset_bible else "锁定资产版本并进入批量生产。",
        ),
        _stage(
            "prompt_compiler",
            status="ready" if snapshot.ready_shot_count > 0 else ("warning" if snapshot.shot_count > 0 else "blocked"),
            evidence=f"ready_shots={snapshot.ready_shot_count}, frame_images={snapshot.frame_image_count}",
            next_action="先把待确认镜头推进到 ready。" if snapshot.ready_shot_count == 0 else "编译镜头提示词并预览引用图。",
        ),
        _stage(
            "runtime_adapter",
            status="ready" if snapshot.ready_shot_count > 0 else "waiting",
            evidence="provider boundary is model-neutral",
            next_action="选择项目默认视频模型并保持请求结构化。",
        ),
        _stage(
            "render_runtime",
            status="active" if snapshot.generating_shot_count > 0 else ("done" if generated_or_accepted > 0 else "waiting"),
            evidence=(
                f"generating_shots={snapshot.generating_shot_count}, "
                f"generated_or_accepted_videos={generated_or_accepted}, task_links={snapshot.task_link_count}"
            ),
            next_action="在任务中心追踪生成结果并写回镜头。" if snapshot.ready_shot_count > 0 else "等待镜头准备完成。",
        ),
        _stage(
            "video_models",
            status="ready" if snapshot.ready_shot_count > 0 else "waiting",
            evidence="Kling/Wan/Vidu-style providers can be selected behind runtime adapter",
            next_action="按镜头时长、比例和参考图选择模型。",
        ),
        _stage(
            "qa_engine",
            status="ready" if generated_or_accepted > 0 else "waiting",
            evidence=f"qa_inputs={generated_or_accepted}",
            next_action="对已生成视频运行身份、服装、构图、连续性 QA。" if generated_or_accepted > 0 else "等待生成视频产物。",
        ),
        _stage(
            "retry_engine",
            status="ready" if generated_or_accepted > 0 else "waiting",
            evidence=f"pending_candidates={snapshot.pending_candidate_count}, pending_dialogues={snapshot.pending_dialogue_count}",
            next_action="只针对 QA 失败镜头生成修复补丁。" if generated_or_accepted > 0 else "等待 QA 报告。",
        ),
        _stage(
            "final_editing",
            status="ready" if generated_or_accepted > 0 else "blocked",
            evidence=f"generated_videos={snapshot.generated_video_count}, accepted_video_tasks={snapshot.accepted_video_task_count}",
            next_action="合成字幕、TTS、BGM、转场并导出成片。" if generated_or_accepted > 0 else "至少需要一个已通过/已采用镜头视频。",
        ),
    ]


def _build_asset_health(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    identity_score = _ratio(snapshot.actor_link_count, max(snapshot.character_count, 1))
    scene_score = _ratio(snapshot.scene_link_count, max(snapshot.shot_count, 1))
    prop_score = _ratio(snapshot.prop_link_count, max(snapshot.shot_count, 1))
    costume_score = _ratio(snapshot.costume_link_count, max(snapshot.character_count, 1))
    return {
        "identity_score": identity_score,
        "scene_score": scene_score,
        "prop_score": prop_score,
        "costume_score": costume_score,
        "pending_candidate_count": snapshot.pending_candidate_count,
        "pending_dialogue_count": snapshot.pending_dialogue_count,
        "summary": _health_summary([identity_score, scene_score, prop_score, costume_score]),
    }


def _build_qa_retry(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    generated_or_accepted = snapshot.generated_video_count + snapshot.accepted_video_task_count
    retry_candidates = max(0, snapshot.ready_shot_count - generated_or_accepted)
    return {
        "qa_ready": generated_or_accepted > 0,
        "generated_or_accepted_videos": generated_or_accepted,
        "planned_retry_candidates": retry_candidates,
        "risk_level": "high" if retry_candidates > 0 or snapshot.pending_candidate_count > 0 else "normal",
        "automatic_retry_enabled": True,
        "post_production_ready": generated_or_accepted > 0,
    }


def _build_pain_points(snapshot: IndustrialProjectSnapshot) -> list[dict[str, Any]]:
    pain_points = [
        {
            "key": "character_consistency",
            "title": "角色脸和身份漂移",
            "severity": "high" if snapshot.character_count == 0 or snapshot.actor_link_count == 0 else "medium",
            "diagnosis": f"characters={snapshot.character_count}, actor_links={snapshot.actor_link_count}",
            "solution": "用角色/演员/参考图建立 identity lock，并在 Prompt Compiler 中强制注入。",
        },
        {
            "key": "costume_prop_drift",
            "title": "服装与道具漂移",
            "severity": "high" if snapshot.costume_link_count == 0 and snapshot.prop_link_count == 0 else "medium",
            "diagnosis": f"costume_links={snapshot.costume_link_count}, prop_links={snapshot.prop_link_count}",
            "solution": "把服装、道具作为资产绑定到角色和镜头，不把它们写成一次性 prompt 文本。",
        },
        {
            "key": "shot_continuity",
            "title": "长剧情镜头连续性断裂",
            "severity": "high" if snapshot.shot_count == 0 else ("medium" if snapshot.detail_count < snapshot.shot_count else "low"),
            "diagnosis": f"shots={snapshot.shot_count}, shot_details={snapshot.detail_count}",
            "solution": "使用 Story Graph + Director DSL 记录每个镜头的动作拍点、场景、机位和情绪。",
        },
        {
            "key": "prompt_randomness",
            "title": "提示词随机和不可复现",
            "severity": "medium" if snapshot.seed == 0 or not snapshot.unify_style else "low",
            "diagnosis": f"seed={snapshot.seed}, unify_style={snapshot.unify_style}",
            "solution": "提示词必须由状态编译，项目 seed 和统一风格作为稳定生产约束。",
        },
        {
            "key": "manual_qa",
            "title": "人工审片无法规模化",
            "severity": "high" if snapshot.generated_video_count > 0 and snapshot.accepted_video_task_count == 0 else "medium",
            "diagnosis": f"generated_videos={snapshot.generated_video_count}, accepted_video_tasks={snapshot.accepted_video_task_count}",
            "solution": "把脸、服装、CLIP、运动完整度、灯光连续性做成结构化 QA 分数和重试原因。",
        },
    ]
    return pain_points


def _build_creation_entries(snapshot: IndustrialProjectSnapshot) -> list[dict[str, str]]:
    return [
        {
            "key": "blank_project",
            "title": "新建项目",
            "purpose": "创建空项目外壳，适合已经有章节、分镜或资产要逐步导入的团队。",
            "when_to_use": "制片人已有剧本或资产，只需要 Jellyfish 工作台承接生产状态。",
            "route_hint": "/projects -> 新建项目",
            "output": "Project 记录；不会自动生成小说、角色或分镜。",
        },
        {
            "key": "text_to_drama",
            "title": "文本生成漫剧",
            "purpose": "从一句创意或正文自动扩展小说稿、分集脚本、分镜、资产圣经和参考采集任务。",
            "when_to_use": "只有创意/梗概，希望从零进入多集 AI 漫剧工业流水线。",
            "route_hint": "/projects -> 文本生成漫剧",
            "output": "Project、Chapter、Shot、角色/服装/道具/场景、CineForge 工作流和任务账本。",
        },
        {
            "key": "film_core",
            "title": "Film Core",
            "purpose": "项目级控制中心，用来检查门禁、编辑九阶段状态、生成计划并创建生产任务。",
            "when_to_use": "项目已经存在，需要判断是否能拍、该用什么运行时模型、哪些镜头要 QA/重试。",
            "route_hint": f"/projects/{snapshot.project_id}?tab=filmCore",
            "output": "只读/编辑/编排已有项目状态，不负责新建空项目。",
        },
    ]


def _build_shooting_gate(snapshot: IndustrialProjectSnapshot) -> dict[str, Any]:
    blockers: list[str] = []
    if not snapshot.has_script:
        blockers.append("缺少小说稿或章节剧本文本，不能进入拍摄。")
    if snapshot.shot_count <= 0:
        blockers.append("缺少分集脚本和分镜图谱，不能创建镜头级生产任务。")
    if snapshot.character_count <= 0:
        blockers.append("缺少角色圣经，无法锁定角色身份。")
    if snapshot.actor_link_count < max(snapshot.character_count, 1):
        blockers.append("角色缺少演员形象/身份参考绑定。")
    if snapshot.scene_link_count <= 0:
        blockers.append("缺少场景资产绑定，无法保证镜头空间连续性。")
    if snapshot.costume_link_count <= 0:
        blockers.append("缺少服装资产绑定，无法保证跨镜头造型连续。")
    if snapshot.prop_link_count <= 0:
        blockers.append("缺少关键道具绑定，无法跟踪道具连续性。")
    if snapshot.detail_count < snapshot.shot_count:
        blockers.append("部分镜头缺少景别、机位、运镜、动作拍点或视效说明。")

    ready = len(blockers) == 0 and snapshot.ready_shot_count > 0
    if not ready and snapshot.ready_shot_count <= 0:
        blockers.append("没有 ready 状态镜头，生产任务会停在 Film Core 门禁。")

    return {
        "ready": ready,
        "state": "ready_to_shoot" if ready else "blocked_before_shooting",
        "message": (
            "角色、资产、分镜和运行时前置条件已满足，可以创建生产任务。"
            if ready
            else "拍摄前置门禁未通过；先补齐小说、分镜、角色/资产和镜头细节。"
        ),
        "blockers": blockers,
        "required_before_shooting": [
            "小说稿/章节脚本",
            "每集分镜和动作拍点",
            "角色圣经与演员形象参考",
            "服装、道具、场景资产绑定",
            "图片/视频运行时模型配置",
            "QA 与 Retry 策略",
        ],
        "allowed_runtime_models": [
            "Image: FLUX / SDXL / StoryDiffusion / ComfyUI",
            "Video: Seedance / Kling / Veo / Wan2.1 / Sora / Vidu",
        ],
    }


def _build_next_actions(snapshot: IndustrialProjectSnapshot) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not snapshot.has_script:
        actions.append({"severity": "high", "action": "先在章节里补齐原文或精简文本。"})
    if snapshot.has_script and snapshot.shot_count == 0:
        actions.append({"severity": "high", "action": "运行分镜提取，建立 Story Graph。"})
    if snapshot.shot_count > 0 and snapshot.detail_count < snapshot.shot_count:
        actions.append({"severity": "medium", "action": "补齐每个镜头的景别、机位、运镜、动作拍点和对白。"})
    if snapshot.character_count == 0 or snapshot.actor_link_count == 0:
        actions.append({"severity": "high", "action": "为主要角色绑定演员形象和身份参考。"})
    if snapshot.costume_link_count == 0:
        actions.append({"severity": "medium", "action": "把关键角色服装加入项目/镜头资产绑定。"})
    if snapshot.ready_shot_count > snapshot.generated_video_count:
        actions.append({"severity": "medium", "action": "对 ready 镜头创建批量视频生成任务。"})
    if snapshot.generated_video_count > 0:
        actions.append({"severity": "medium", "action": "运行自动 QA，并让 Retry Engine 只重试失败镜头。"})
    if not actions:
        actions.append({"severity": "low", "action": "当前项目可进入批量渲染、QA 和后期导出闭环。"})
    return actions


def _industrial_score(snapshot: IndustrialProjectSnapshot) -> int:
    checks = [
        snapshot.has_script,
        snapshot.has_story_graph,
        snapshot.has_director_plan,
        snapshot.has_asset_bible,
        snapshot.ready_shot_count > 0,
        snapshot.generated_video_count + snapshot.accepted_video_task_count > 0,
        snapshot.seed > 0,
        snapshot.unify_style,
    ]
    return round(sum(1 for item in checks if item) / len(checks) * 100)


def _ratio(value: int, total: int) -> int:
    if total <= 0:
        return 0
    return min(100, round(value / total * 100))


def _health_summary(scores: list[int]) -> str:
    avg = sum(scores) / len(scores) if scores else 0
    if avg >= 80:
        return "ready"
    if avg >= 45:
        return "needs_locking"
    return "fragile"
