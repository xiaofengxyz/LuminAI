from __future__ import annotations

from dataclasses import dataclass
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
        return self.character_count > 0 and (
            self.scene_link_count > 0 or self.prop_link_count > 0 or self.costume_link_count > 0
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
        "blockers": [item for item in overview["operator_next_actions"] if item["severity"] == "high"],
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
