from __future__ import annotations

import argparse
import json
from typing import Any

from src.film_engine.director import CharacterBible, SceneBible
from src.film_engine.platform import StudioAsset, StudioChapter, StudioProject, StudioShot
from src.film_engine.production import ClosedLoopChapterPlan, ClosedLoopProductionPlanner
from src.film_engine.runtime import RenderRequest, RenderResult


def build_demo_chapter_plan() -> ClosedLoopChapterPlan:
    project = StudioProject(
        id="project_demo_neon_trial",
        title="Neon Trial",
        description="Run-ready industrial AI film engine smoke project.",
    )
    chapter = StudioChapter(
        id="chapter_demo_001",
        project_id=project.id,
        title="Rain Alley",
        order=1,
    )
    assets = [
        StudioAsset(
            id="char_ari",
            kind="character",
            name="Ari",
            description="Lead investigator with a fixed black rain coat identity.",
            reference_media=["refs/ari_front.png", "refs/ari_profile.png"],
            metadata={"voice_id": "voice_ari"},
        ),
        StudioAsset(
            id="scene_neon_alley",
            kind="scene",
            name="Neon alley",
            description="Blue neon rain alley with noir lighting continuity.",
            reference_media=["refs/neon_alley.png"],
            metadata={"lighting": "neon_blue", "weather": "rain", "tone": "noir"},
        ),
    ]
    character_bibles = [
        CharacterBible(
            id="char_ari",
            name="Ari",
            reference_media=["refs/ari_bible.png"],
            outfits={"coat_black": "black rain coat"},
            default_outfit="coat_black",
            voice_id="voice_ari",
            lora="ari_v12.safetensors",
            embeddings=["ari_face_v4"],
            negative_terms=["wrong face", "different hairstyle"],
        )
    ]
    scene_bibles = [
        SceneBible(
            id="scene_neon_alley",
            name="Neon alley",
            lighting="neon_blue",
            weather="rain",
            tone="noir",
            mood="suspense",
            camera_style="handheld restrained",
            reference_media=["refs/neon_alley_bible.png"],
        )
    ]
    shots = [
        StudioShot(
            id="shot_demo_001",
            project_id=project.id,
            chapter_id=chapter.id,
            index=1,
            title="Ari enters the alley",
            summary="Ari steps into the neon rain and realizes she is being watched.",
            scene_id="scene_neon_alley",
            character_ids=["char_ari"],
            dialogue=["Ari: Keep walking."],
            camera={
                "framing": "medium_closeup",
                "movement": "dolly_in",
                "lens": "85mm",
                "emotion": "wary",
                "pacing": "slow",
            },
            duration=4,
            readiness_state="ready",
        ),
        StudioShot(
            id="shot_demo_002",
            project_id=project.id,
            chapter_id=chapter.id,
            index=2,
            title="The alley reveals a clue",
            summary="A gloved hand leaves a photo under a broken sign.",
            scene_id="scene_neon_alley",
            character_ids=["char_ari"],
            camera={
                "framing": "wide",
                "movement": "track",
                "lens": "35mm",
                "emotion": "urgent",
                "pacing": "medium",
            },
            duration=3,
            readiness_state="ready",
        ),
    ]

    return ClosedLoopProductionPlanner().plan_chapter(
        project=project,
        chapter=chapter,
        shots=shots,
        assets=assets,
        character_bibles=character_bibles,
        scene_bibles=scene_bibles,
        provider="kling",
        model="kling-v1",
        output_dir="output/demo/renders",
        qa_metrics_by_shot={
            "shot_demo_001": {
                "face_similarity": 0.61,
                "outfit_similarity": 0.82,
                "clip_score": 0.52,
            },
            "shot_demo_002": {
                "face_similarity": 0.94,
                "outfit_similarity": 0.90,
                "clip_score": 0.58,
            },
        },
        render_results=[
            RenderResult(
                "shot_demo_001",
                "output/demo/renders/shot_demo_001.mp4",
                "kling",
                {"duration": 4},
            ),
            RenderResult(
                "shot_demo_002",
                "output/demo/renders/shot_demo_002.mp4",
                "kling",
                {"duration": 3},
            ),
        ],
        export_output_path="output/demo/exports/chapter_demo_001.mp4",
    )


def build_demo_plan_summary() -> dict[str, Any]:
    plan = build_demo_chapter_plan()
    failed_shots = [
        {
            "shot_id": shot_plan.shot.id,
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                    "repair_hint": issue.repair_hint,
                }
                for issue in shot_plan.qa_report.issues
            ],
        }
        for shot_plan in plan.shot_plans
        if not shot_plan.qa_report.passed
    ]
    return {
        "project": {
            "id": plan.project.id,
            "title": plan.project.title,
            "description": plan.project.description,
        },
        "chapter": {
            "id": plan.chapter.id,
            "title": plan.chapter.title,
            "order": plan.chapter.order,
        },
        "workflow": [node.system for node in plan.workflow.topological_order()],
        "metadata": dict(plan.metadata),
        "qa": {
            "passed": plan.qa_passed,
            "failed_shots": failed_shots,
        },
        "render_requests": [
            _render_request_summary(request) for request in plan.render_requests
        ],
        "retry_requests": [
            _render_request_summary(request) for request in plan.retry_requests
        ],
        "post_production": _post_production_summary(plan),
    }


def _render_request_summary(request: RenderRequest) -> dict[str, Any]:
    return {
        "shot_id": request.shot_id,
        "model": request.model,
        "output_path": request.output_path,
        "prompt": request.prompt,
        "references": list(request.references),
        "parameters": dict(request.parameters),
    }


def _post_production_summary(plan: ClosedLoopChapterPlan) -> dict[str, Any]:
    if plan.post_production_plan is None:
        return {"enabled": False, "steps": []}
    return {
        "enabled": True,
        "output_path": plan.post_production_plan.output_path,
        "steps": [
            {
                "id": step.id,
                "system": step.system,
                "depends_on": list(step.depends_on),
            }
            for step in plan.post_production_plan.steps
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the LuminAI closed-loop demo.")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of indented JSON.",
    )
    args = parser.parse_args(argv)
    indent = None if args.compact else 2
    print(json.dumps(build_demo_plan_summary(), indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
