from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.director import (
    CharacterBible,
    DirectorConsistencyEngine,
    PreparedShotContext,
    SceneBible,
)
from src.film_engine.platform import (
    StudioAsset,
    StudioChapter,
    StudioPlatformBridge,
    StudioProject,
    StudioShot,
)
from src.film_engine.post_production import PostProductionPlan, PostProductionPlanner
from src.film_engine.prompt_compiler import CompiledPrompt, PromptCompiler
from src.film_engine.qa import QAReport, RuleBasedQAEngine
from src.film_engine.retry import RetryDecision, RetryEngine
from src.film_engine.runtime import RenderRequest, RenderResult
from src.film_engine.graph import WorkflowGraph


@dataclass
class ProductionShotPlan:
    shot: StudioShot
    prepared_context: PreparedShotContext
    compiled_prompt: CompiledPrompt
    render_request: RenderRequest
    qa_report: QAReport
    retry_decision: RetryDecision
    retry_request: RenderRequest | None = None


@dataclass
class ClosedLoopChapterPlan:
    project: StudioProject
    chapter: StudioChapter
    workflow: WorkflowGraph
    shot_plans: list[ProductionShotPlan]
    post_production_plan: PostProductionPlan | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def render_requests(self) -> list[RenderRequest]:
        return [plan.render_request for plan in self.shot_plans]

    @property
    def retry_requests(self) -> list[RenderRequest]:
        return [plan.retry_request for plan in self.shot_plans if plan.retry_request is not None]

    @property
    def qa_passed(self) -> bool:
        return all(plan.qa_report.passed for plan in self.shot_plans)


class ClosedLoopProductionPlanner:
    def __init__(
        self,
        *,
        bridge: StudioPlatformBridge | None = None,
        director_engine: DirectorConsistencyEngine | None = None,
        prompt_compiler: PromptCompiler | None = None,
        qa_engine: RuleBasedQAEngine | None = None,
        retry_engine: RetryEngine | None = None,
        post_planner: PostProductionPlanner | None = None,
    ) -> None:
        self.bridge = bridge or StudioPlatformBridge()
        self.director_engine = director_engine or DirectorConsistencyEngine()
        self.prompt_compiler = prompt_compiler or PromptCompiler()
        self.qa_engine = qa_engine or RuleBasedQAEngine()
        self.retry_engine = retry_engine or RetryEngine()
        self.post_planner = post_planner or PostProductionPlanner()

    def plan_chapter(
        self,
        *,
        project: StudioProject,
        chapter: StudioChapter,
        shots: list[StudioShot],
        assets: list[StudioAsset],
        character_bibles: list[CharacterBible],
        scene_bibles: list[SceneBible],
        provider: str,
        model: str,
        output_dir: str,
        qa_metrics_by_shot: dict[str, dict[str, float]] | None = None,
        attempts_by_shot: dict[str, int] | None = None,
        render_results: list[RenderResult] | None = None,
        export_output_path: str | None = None,
    ) -> ClosedLoopChapterPlan:
        ordered_shots = sorted(shots, key=lambda shot: shot.index)
        workflow = self.bridge.build_chapter_workflow(project, chapter, ordered_shots)
        qa_metrics_by_shot = qa_metrics_by_shot or {}
        attempts_by_shot = attempts_by_shot or {}

        shot_plans = [
            self._plan_shot(
                shot=shot,
                assets=assets,
                character_bibles=character_bibles,
                scene_bibles=scene_bibles,
                provider=provider,
                model=model,
                output_dir=output_dir,
                qa_metrics=qa_metrics_by_shot.get(shot.id, self._passing_metrics()),
                attempt=attempts_by_shot.get(shot.id, 1),
            )
            for shot in ordered_shots
        ]

        post_plan = None
        if render_results and export_output_path:
            clips = self.post_planner.clips_from_shots(ordered_shots, render_results)
            if clips:
                post_plan = self.post_planner.plan_chapter(
                    project_id=project.id,
                    chapter_id=chapter.id,
                    clips=clips,
                    output_path=export_output_path,
                    work_dir=f"{output_dir}/post",
                )

        return ClosedLoopChapterPlan(
            project=project,
            chapter=chapter,
            workflow=workflow,
            shot_plans=shot_plans,
            post_production_plan=post_plan,
            metadata={
                "mode": "closed_loop_industrial_batch",
                "provider": provider,
                "model": model,
                "shot_count": len(shot_plans),
                "retry_count": len([plan for plan in shot_plans if plan.retry_decision.should_retry]),
            },
        )

    def _plan_shot(
        self,
        *,
        shot: StudioShot,
        assets: list[StudioAsset],
        character_bibles: list[CharacterBible],
        scene_bibles: list[SceneBible],
        provider: str,
        model: str,
        output_dir: str,
        qa_metrics: dict[str, float],
        attempt: int,
    ) -> ProductionShotPlan:
        continuity = self.bridge.shot_to_continuity(shot, assets=assets)
        prepared = self.director_engine.prepare_shot(
            shot=shot,
            continuity=continuity,
            character_bibles=character_bibles,
            scene_bibles=scene_bibles,
        )
        compiled = self.prompt_compiler.compile_shot(
            provider=provider,
            director_dsl=prepared.director_dsl,
            continuity=prepared.continuity,
        )
        request = self.bridge.compile_render_request(
            shot,
            compiled,
            model=model,
            output_path=f"{output_dir}/{shot.id}.mp4",
        )
        qa_report = self.qa_engine.evaluate(shot_id=shot.id, metrics=qa_metrics)
        retry_decision = self.retry_engine.decide(qa_report, attempt=attempt)
        retry_request = None
        if retry_decision.should_retry:
            retry_request = self._retry_request(request, retry_decision)
        return ProductionShotPlan(
            shot=shot,
            prepared_context=prepared,
            compiled_prompt=compiled,
            render_request=request,
            qa_report=qa_report,
            retry_decision=retry_decision,
            retry_request=retry_request,
        )

    def _retry_request(
        self,
        request: RenderRequest,
        retry_decision: RetryDecision,
    ) -> RenderRequest:
        prompt = request.prompt
        if retry_decision.prompt_patches:
            prompt = "; ".join([prompt, *retry_decision.prompt_patches])
        parameters = {
            **request.parameters,
            **retry_decision.parameter_patches,
            "retry_attempt": retry_decision.attempt,
            "retry_reason": retry_decision.reason,
        }
        return RenderRequest(
            shot_id=request.shot_id,
            prompt=prompt,
            model=request.model,
            output_path=request.output_path,
            references=list(request.references),
            parameters=parameters,
        )

    def _passing_metrics(self) -> dict[str, float]:
        return {
            "face_similarity": 0.95,
            "outfit_similarity": 0.92,
            "clip_score": 0.55,
        }
