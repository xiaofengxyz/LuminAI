from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "vendor" / "jellyfish" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.industrial_film_core import (  # noqa: E402
    CINEFORGE_WORKFLOW_STAGES,
    IndustrialProjectSnapshot,
    build_cineforge_workflow_state,
    build_closed_loop_plan,
    build_industrial_overview,
    build_writeback_summary,
)


def test_industrial_overview_maps_jellyfish_state_to_full_film_pipeline():
    snapshot = IndustrialProjectSnapshot(
        project_id="proj-1",
        project_name="Neon Trial",
        project_style="真人都市",
        visual_style="现实",
        seed=42,
        unify_style=True,
        chapter_id="ch-1",
        chapter_title="第一章",
        chapter_index=1,
        script_text_length=1200,
        condensed_text_length=400,
        chapter_count=3,
        shot_count=5,
        ready_shot_count=4,
        generated_video_count=2,
        detail_count=5,
        frame_image_count=8,
        dialogue_line_count=12,
        character_count=3,
        actor_link_count=3,
        scene_link_count=4,
        prop_link_count=2,
        costume_link_count=3,
        task_link_count=6,
        accepted_video_task_count=1,
    )

    overview = build_industrial_overview(snapshot)

    assert overview["workflow_mode"] == "jellyfish_native_industrial_closed_loop"
    assert [stage["key"] for stage in overview["pipeline"]] == [
        "novel_script",
        "story_graph",
        "director_planner",
        "film_core",
        "prompt_compiler",
        "runtime_adapter",
        "render_runtime",
        "video_models",
        "qa_engine",
        "retry_engine",
        "final_editing",
    ]
    assert overview["industrial_score"] >= 80
    assert overview["asset_health"]["summary"] == "ready"
    assert overview["qa_retry"]["automatic_retry_enabled"] is True
    assert any(item["name"] == "Jellyfish" for item in overview["reference_projects"])


def test_closed_loop_plan_exposes_render_qa_retry_and_post_contracts():
    snapshot = IndustrialProjectSnapshot(
        project_id="proj-2",
        project_name="Runway",
        project_style="真人科幻",
        visual_style="现实",
        seed=0,
        unify_style=False,
        script_text_length=500,
        chapter_count=1,
        shot_count=2,
        ready_shot_count=2,
        generated_video_count=0,
        detail_count=1,
        character_count=1,
        actor_link_count=0,
        shot_ids=("shot-a", "shot-b"),
        ready_shot_ids=("shot-a", "shot-b"),
    )

    plan = build_closed_loop_plan(snapshot, provider="kling", model="kling-v1", output_dir="output/test")

    assert plan["plan_id"] == "industrial-proj-2-project"
    assert len(plan["render_queue"]) == 2
    assert plan["render_queue"][0]["shot_ref"] == "shot-a"
    assert plan["render_queue"][0]["provider"] == "kling"
    assert plan["qa_policy"]["face_similarity_min"] > 0.8
    assert plan["retry_policy"]["planned_retry_candidates"] == 2
    assert plan["post_production"]["enabled"] is False
    assert any(blocker["severity"] == "high" for blocker in plan["blockers"])


def test_writeback_summary_counts_render_qa_retry_and_post_targets():
    snapshot = IndustrialProjectSnapshot(
        project_id="proj-writeback",
        project_name="Writeback",
        project_style="真人都市",
        visual_style="现实",
        seed=11,
        unify_style=True,
        script_text_length=900,
        chapter_count=1,
        shot_count=3,
        ready_shot_count=3,
        generated_video_count=1,
        detail_count=3,
        character_count=2,
        actor_link_count=2,
        scene_link_count=3,
        prop_link_count=1,
        costume_link_count=2,
        shot_ids=("shot-1", "shot-2", "shot-3"),
        ready_shot_ids=("shot-1", "shot-2", "shot-3"),
        generated_video_shot_ids=("shot-1",),
    )

    summary = build_writeback_summary(snapshot)

    assert summary["render_targets"] == 3
    assert summary["qa_targets"] == 1
    assert summary["retry_targets"] == 2
    assert summary["post_production_targets"] == 1
    assert summary["writes_generation_tasks"] is True
    assert summary["writes_task_links"] is True


def test_cineforge_workflow_state_exposes_persisted_editable_stage_contracts():
    snapshot = IndustrialProjectSnapshot(
        project_id="proj-cineforge",
        project_name="Editable Workflow",
        project_style="真人都市",
        visual_style="现实",
        seed=99,
        unify_style=True,
        script_text_length=1000,
        chapter_count=2,
        shot_count=6,
        ready_shot_count=4,
        generated_video_count=1,
        detail_count=6,
        character_count=3,
        actor_link_count=3,
        scene_link_count=4,
        prop_link_count=2,
        costume_link_count=3,
        shot_ids=("shot-1", "shot-2"),
    )

    state = build_cineforge_workflow_state(snapshot, workflow_id="workflow-1")

    assert state["workflow_key"] == "cineforge_ai_drama_os"
    assert state["stage_count"] == 9
    assert [stage["key"] for stage in state["stages"]] == [stage["key"] for stage in CINEFORGE_WORKFLOW_STAGES]
    assert state["stage_data"]["novel_engine"]["world_bible"]["title"] == "Editable Workflow"
    assert state["stage_data"]["image_runtime"]["adapters"] == ["flux", "sdxl", "storydiffusion", "comfyui"]
    assert state["stage_data"]["video_runtime"]["adapters"] == ["seedance", "kling", "veo", "wan2.1", "sora"]
    assert state["edit_contract"]["method"] == "PATCH"
    assert state["regenerate_contract"]["method"] == "POST"


def test_industrial_overview_exposes_nine_implementation_phases():
    snapshot = IndustrialProjectSnapshot(
        project_id="proj-3",
        project_name="Phase Evidence",
        project_style="真人都市",
        visual_style="现实",
        seed=7,
        unify_style=True,
        script_text_length=800,
        chapter_count=1,
        shot_count=3,
        ready_shot_count=3,
        generated_video_count=1,
        detail_count=3,
        character_count=2,
        actor_link_count=2,
        scene_link_count=2,
        prop_link_count=1,
        costume_link_count=2,
    )

    overview = build_industrial_overview(snapshot)

    assert overview["implementation_status"]["total_phases"] == 9
    assert overview["implementation_status"]["completed_phases"] == 9
    assert overview["implementation_status"]["status"] == "complete"
    assert len(overview["implementation_phases"]) == 9
    assert overview["implementation_phases"][0]["phase"] == "Phase 1"
    assert overview["implementation_phases"][-1]["key"] == "phase_9_qa_retry_batch"


def test_jellyfish_industrial_routes_are_registered():
    route_file = BACKEND_DIR / "app" / "api" / "v1" / "routes" / "film" / "__init__.py"
    route_source = route_file.read_text(encoding="utf-8")
    industrial_source = (BACKEND_DIR / "app" / "api" / "v1" / "routes" / "film" / "industrial.py").read_text(
        encoding="utf-8"
    )

    assert "industrial.router" in route_source
    assert "createIndustrialRun" in industrial_source
    assert "loadWorkflowState" in industrial_source
    assert "editWorkflowState" in industrial_source
    assert "regenerateWorkflowStage" in industrial_source
    assert "CineForgeWorkflowState" in industrial_source
    assert "GenerationTaskLink" in industrial_source


def test_project_workbench_surfaces_film_core_from_lobby_and_generated_client():
    front_dir = BACKEND_DIR.parent / "front" / "src"
    lobby_source = (front_dir / "pages" / "aiStudio" / "project" / "ProjectLobby.tsx").read_text(encoding="utf-8")
    routes_source = (
        front_dir / "pages" / "aiStudio" / "project" / "ProjectWorkbench" / "routes.ts"
    ).read_text(encoding="utf-8")
    film_service_source = (front_dir / "services" / "industrialFilm.ts").read_text(encoding="utf-8")
    film_core_source = (
        front_dir / "pages" / "aiStudio" / "project" / "ProjectWorkbench" / "tabs" / "FilmCoreTab.tsx"
    ).read_text(encoding="utf-8")
    generated_film_service_source = (front_dir / "services" / "generated" / "services" / "FilmService.ts").read_text(
        encoding="utf-8"
    )

    assert "getProjectFilmCorePath" in routes_source
    assert "Film Core 状态" in lobby_source
    assert "创建生产任务" in film_core_source
    assert "CineForge 可编辑工作流状态" in film_core_source
    assert "保存阶段编辑" in film_core_source
    assert "重生成阶段" in film_core_source
    assert "Film Core Overview" in film_core_source
    assert "loadWorkflowState" in film_service_source
    assert "editWorkflowState" in film_service_source
    assert "regenerateWorkflowStage" in film_service_source
    assert "loadWorkflowState" in generated_film_service_source
    assert "createIndustrialRun" in film_service_source
    assert "FilmService" in film_service_source
    assert "services/http" not in film_service_source
