from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.graph import WorkflowGraph, WorkflowNode


@dataclass
class BatchPlan:
    series_id: str
    episode_ids: list[str]
    workflow: WorkflowGraph
    metadata: dict[str, object] = field(default_factory=dict)


class BatchPlanner:
    SYSTEM_ORDER = [
        "story_graph",
        "director_planner",
        "film_state",
        "prompt_compiler",
        "runtime_adapter",
        "qa_engine",
        "retry_engine",
        "final_editing",
    ]

    def plan_series(self, series_id: str, episode_ids: list[str]) -> BatchPlan:
        graph = WorkflowGraph()
        previous_id: str | None = None
        for episode_id in episode_ids:
            for system in self.SYSTEM_ORDER:
                node_id = f"{episode_id}:{system}"
                graph.add_node(
                    WorkflowNode(
                        id=node_id,
                        system=system,
                        payload={"series_id": series_id, "episode_id": episode_id},
                    )
                )
                if previous_id:
                    graph.connect(previous_id, node_id)
                previous_id = node_id
        return BatchPlan(
            series_id=series_id,
            episode_ids=list(episode_ids),
            workflow=graph,
            metadata={"mode": "industrial_batch"},
        )
