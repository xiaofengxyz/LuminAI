from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.film_engine.ecs import Component, Entity, EntityRegistry
from src.film_engine.graph import WorkflowGraph, WorkflowNode
from src.film_engine.prompt_compiler import CompiledPrompt
from src.film_engine.runtime import RenderRequest
from src.film_engine.state import ShotContinuityState


JELLYFISH_FILM_WORKFLOW = [
    "script_breakdown",
    "shot_preparation",
    "asset_consistency",
    "film_state",
    "prompt_compiler",
    "runtime_adapter",
    "qa_engine",
    "retry_engine",
    "final_export",
]


@dataclass
class StudioProject:
    id: str
    title: str
    description: str = ""
    chapter_ids: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class StudioChapter:
    id: str
    project_id: str
    title: str
    order: int = 1
    script_id: str | None = None
    shot_ids: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class StudioAsset:
    id: str
    kind: str
    name: str
    description: str = ""
    reference_media: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class StudioShot:
    id: str
    project_id: str
    chapter_id: str
    index: int
    title: str = ""
    summary: str = ""
    scene_id: str | None = None
    character_ids: list[str] = field(default_factory=list)
    prop_ids: list[str] = field(default_factory=list)
    costume_ids: list[str] = field(default_factory=list)
    dialogue: list[str] = field(default_factory=list)
    camera: dict[str, object] = field(default_factory=dict)
    duration: float | None = None
    readiness_state: str = "draft"
    reference_media: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def is_generation_ready(self) -> bool:
        return self.readiness_state == "ready"


@dataclass
class StudioTask:
    id: str
    project_id: str
    chapter_id: str | None = None
    shot_id: str | None = None
    task_type: str = "generation"
    status: str = "pending"
    result_media: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class StudioPlatformBridge:
    """Boundary between the Jellyfish-style studio OS and LuminAI Film Core."""

    def asset_to_entity(self, asset: StudioAsset) -> Entity:
        entity = Entity(id=asset.id, kind=asset.kind)
        entity.add_component(
            Component(
                kind="identity",
                data={
                    "name": asset.name,
                    "description": asset.description,
                },
            )
        )
        entity.add_component(
            Component(
                kind="references",
                data={"media": list(asset.reference_media)},
            )
        )
        entity.add_component(
            Component(
                kind="metadata",
                data=dict(asset.metadata),
            )
        )
        return entity

    def register_assets(
        self,
        registry: EntityRegistry,
        assets: Iterable[StudioAsset],
    ) -> list[Entity]:
        entities = [self.asset_to_entity(asset) for asset in assets]
        for entity in entities:
            registry.add(entity)
        return entities

    def shot_to_continuity(
        self,
        shot: StudioShot,
        *,
        assets: Iterable[StudioAsset] = (),
    ) -> ShotContinuityState:
        asset_map = {asset.id: asset for asset in assets}
        references = list(shot.reference_media)
        linked_asset_ids = [
            *shot.character_ids,
            *shot.prop_ids,
            *shot.costume_ids,
        ]
        if shot.scene_id:
            linked_asset_ids.append(shot.scene_id)
        for asset_id in linked_asset_ids:
            asset = asset_map.get(asset_id)
            if asset:
                references.extend(asset.reference_media)

        scene_asset = asset_map.get(shot.scene_id or "")
        lighting = shot.metadata.get("lighting")
        if lighting is None and scene_asset:
            lighting = scene_asset.metadata.get("lighting")

        return ShotContinuityState(
            shot_id=shot.id,
            character_ids=list(shot.character_ids),
            scene_id=shot.scene_id,
            outfit_map=self._string_map(shot.metadata.get("outfit_map")),
            emotion_map=self._string_map(shot.metadata.get("emotion_map")),
            lighting=str(lighting) if lighting is not None else None,
            timeline_position=str(
                shot.metadata.get(
                    "timeline_position",
                    f"chapter:{shot.chapter_id}:shot:{shot.index:04d}",
                )
            ),
            reference_media=references,
        )

    def shot_to_director_dsl(self, shot: StudioShot) -> dict[str, object]:
        dsl = dict(shot.camera)
        if shot.duration is not None:
            dsl["duration"] = shot.duration
        if shot.summary:
            dsl["summary"] = shot.summary
        return dsl

    def build_chapter_workflow(
        self,
        project: StudioProject,
        chapter: StudioChapter,
        shots: Iterable[StudioShot],
    ) -> WorkflowGraph:
        graph = WorkflowGraph()
        shot_ids = [shot.id for shot in shots]
        previous_id: str | None = None
        for system in JELLYFISH_FILM_WORKFLOW:
            node_id = f"{chapter.id}:{system}"
            graph.add_node(
                WorkflowNode(
                    id=node_id,
                    system=system,
                    payload={
                        "project_id": project.id,
                        "chapter_id": chapter.id,
                        "shot_ids": list(shot_ids),
                    },
                )
            )
            if previous_id:
                graph.connect(previous_id, node_id)
            previous_id = node_id
        return graph

    def compile_render_request(
        self,
        shot: StudioShot,
        compiled_prompt: CompiledPrompt,
        *,
        model: str,
        output_path: str,
    ) -> RenderRequest:
        return RenderRequest(
            shot_id=shot.id,
            prompt=compiled_prompt.text,
            model=model,
            output_path=output_path,
            references=list(compiled_prompt.references),
            parameters={
                **compiled_prompt.parameters,
                "provider": compiled_prompt.provider,
                "negative_prompt": compiled_prompt.negative_text,
            },
        )

    @staticmethod
    def _string_map(value: object) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(key): str(item) for key, item in value.items()}
