from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.film_engine.platform import (
    StudioAsset,
    StudioChapter,
    StudioProject,
    StudioShot,
    StudioTask,
)


Record = Mapping[str, Any]


@dataclass
class JellyfishShotBundle:
    """Collected Jellyfish API records for one shot mapping pass."""

    project: Record | None = None
    chapter: Record | None = None
    shot: Record = field(default_factory=dict)
    detail: Record | None = None
    asset_overview: list[Record] = field(default_factory=list)
    dialogue_lines: list[Record] = field(default_factory=list)
    frame_images: list[Record] = field(default_factory=list)


class JellyfishRecordMapper:
    """Maps Jellyfish platform records into LuminAI studio bridge contracts.

    The mapper intentionally accepts plain mappings so LuminAI can consume
    Jellyfish OpenAPI responses, ORM dumps, or fork-specific DTOs without
    importing Jellyfish models into the film core.
    """

    ASSET_KIND_ALIASES = {
        "actor": "actor",
        "character": "character",
        "scene": "scene",
        "prop": "prop",
        "costume": "costume",
        "location": "scene",
    }

    READY_STATUSES = {"ready", "done", "completed", "success"}
    ACTIVE_STATUSES = {"generating", "running", "processing", "shooting", "pending"}

    def project(self, record: Record) -> StudioProject:
        chapter_ids = self._ids_from(record.get("chapters"))
        return StudioProject(
            id=self._required(record, "id", "project_id"),
            title=self._text(record, "name", "title"),
            description=self._text(record, "description"),
            chapter_ids=chapter_ids,
            metadata=self._metadata(
                record,
                exclude={"id", "project_id", "name", "title", "description", "chapters"},
            ),
        )

    def chapter(self, record: Record) -> StudioChapter:
        shot_ids = self._ids_from(record.get("shots"))
        return StudioChapter(
            id=self._required(record, "id", "chapter_id"),
            project_id=self._required(record, "project_id"),
            title=self._text(record, "title", "name"),
            order=self._int(record.get("index", record.get("order")), default=1),
            script_id=self._optional_text(record, "script_id"),
            shot_ids=shot_ids,
            metadata=self._metadata(
                record,
                exclude={
                    "id",
                    "chapter_id",
                    "project_id",
                    "title",
                    "name",
                    "index",
                    "order",
                    "script_id",
                    "shots",
                },
            ),
        )

    def asset(self, record: Record, *, kind: str | None = None) -> StudioAsset:
        asset_kind = self._asset_kind(record, kind)
        references = self._references(record)
        return StudioAsset(
            id=self._required(record, "id", "asset_id", "linked_entity_id"),
            kind=asset_kind,
            name=self._text(record, "name", "entity_name", "candidate_name"),
            description=self._text(record, "description", "summary"),
            reference_media=references,
            metadata=self._metadata(
                record,
                exclude={
                    "id",
                    "asset_id",
                    "linked_entity_id",
                    "kind",
                    "type",
                    "asset_type",
                    "entity_type",
                    "name",
                    "entity_name",
                    "candidate_name",
                    "description",
                    "summary",
                    "thumbnail",
                    "file_id",
                    "images",
                    "reference_media",
                },
            ),
        )

    def shot(
        self,
        record: Record,
        *,
        project_id: str | None = None,
        detail: Record | None = None,
        asset_overview: list[Record] | None = None,
        dialogue_lines: list[Record] | None = None,
        frame_images: list[Record] | None = None,
    ) -> StudioShot:
        detail = detail or {}
        asset_overview = asset_overview or []
        dialogue_lines = dialogue_lines or []
        frame_images = frame_images or []

        linked = self._linked_assets(asset_overview)
        scene_id = self._optional_text(detail, "scene_id")
        if scene_id is None and linked["scene_ids"]:
            scene_id = linked["scene_ids"][0]
        status = self._text(record, "status").lower()
        camera = self._camera(detail)
        references = self._references(record) + self._references(detail)
        for frame in frame_images:
            references.extend(self._references(frame))

        return StudioShot(
            id=self._required(record, "id", "shot_id"),
            project_id=project_id or self._text(record, "project_id"),
            chapter_id=self._required(record, "chapter_id"),
            index=self._int(record.get("index"), default=1),
            title=self._text(record, "title", "name"),
            summary=self._text(record, "summary", "script_excerpt"),
            scene_id=scene_id,
            character_ids=self._direct_ids(record, "character_ids") + linked["character_ids"],
            prop_ids=self._direct_ids(record, "prop_ids") + linked["prop_ids"],
            costume_ids=self._direct_ids(record, "costume_ids") + linked["costume_ids"],
            dialogue=self._dialogue(dialogue_lines) or self._direct_texts(record, "dialogue"),
            camera=camera,
            duration=self._float(detail.get("duration")),
            readiness_state=self._readiness(status),
            reference_media=self._dedupe(references),
            metadata={
                **self._metadata(
                    record,
                    exclude={
                        "id",
                        "shot_id",
                        "project_id",
                        "chapter_id",
                        "index",
                        "title",
                        "name",
                        "summary",
                        "script_excerpt",
                        "thumbnail",
                        "status",
                        "character_ids",
                        "prop_ids",
                        "costume_ids",
                        "dialogue",
                    },
                ),
                "jellyfish_status": status,
                "extraction": record.get("extraction"),
                "video_ratio": detail.get("override_video_ratio"),
                "asset_overview": [dict(item) for item in asset_overview],
            },
        )

    def shot_bundle(self, bundle: JellyfishShotBundle) -> StudioShot:
        project_id = None
        if bundle.project:
            project_id = self._required(bundle.project, "id", "project_id")
        elif bundle.chapter:
            project_id = self._required(bundle.chapter, "project_id")
        return self.shot(
            bundle.shot,
            project_id=project_id,
            detail=bundle.detail,
            asset_overview=bundle.asset_overview,
            dialogue_lines=bundle.dialogue_lines,
            frame_images=bundle.frame_images,
        )

    def task(self, record: Record, *, project_id: str | None = None) -> StudioTask:
        relation_type = self._text(record, "relation_type", "navigate_relation_type")
        relation_id = self._text(record, "relation_entity_id", "navigate_relation_entity_id")
        task_project_id = project_id or self._text(record, "project_id")
        chapter_id = self._optional_text(record, "chapter_id")
        shot_id = self._optional_text(record, "shot_id")
        if relation_type == "project" and relation_id:
            task_project_id = relation_id
        elif relation_type == "chapter" and relation_id:
            chapter_id = relation_id
        elif relation_type == "shot" and relation_id:
            shot_id = relation_id

        return StudioTask(
            id=self._required(record, "task_id", "id"),
            project_id=task_project_id,
            chapter_id=chapter_id,
            shot_id=shot_id,
            task_type=self._text(record, "task_kind", "resource_type", default="generation"),
            status=self._text(record, "status", default="pending"),
            result_media=self._result_media(record),
            metadata=self._metadata(
                record,
                exclude={
                    "task_id",
                    "id",
                    "project_id",
                    "chapter_id",
                    "shot_id",
                    "task_kind",
                    "resource_type",
                    "status",
                    "result",
                },
            ),
        )

    def _asset_kind(self, record: Record, fallback: str | None) -> str:
        raw = fallback or self._text(record, "kind", "type", "asset_type", "entity_type")
        return self.ASSET_KIND_ALIASES.get(raw.lower(), raw.lower() or "asset")

    def _camera(self, detail: Record) -> dict[str, object]:
        camera: dict[str, object] = {}
        aliases = {
            "camera_shot": "framing",
            "angle": "angle",
            "movement": "movement",
            "atmosphere": "atmosphere",
            "vfx_type": "vfx_type",
            "vfx_note": "vfx_note",
            "action_beats": "action_beats",
            "mood_tags": "emotion",
        }
        for source, target in aliases.items():
            value = detail.get(source)
            if value not in (None, "", []):
                camera[target] = self._plain(value)
        if detail.get("override_video_ratio"):
            camera["ratio"] = detail["override_video_ratio"]
        return camera

    def _linked_assets(self, items: list[Record]) -> dict[str, list[str]]:
        linked = {
            "character_ids": [],
            "scene_ids": [],
            "prop_ids": [],
            "costume_ids": [],
        }
        for item in items:
            asset_id = self._text(item, "linked_entity_id", "asset_id", "id")
            if not asset_id:
                continue
            kind = self._asset_kind(item, None)
            if kind == "actor":
                kind = "character"
            key = f"{kind}_ids"
            if key in linked and self._bool(item.get("is_linked"), default=True):
                linked[key].append(asset_id)
        return {key: self._dedupe(values) for key, values in linked.items()}

    def _dialogue(self, records: list[Record]) -> list[str]:
        rows = sorted(records, key=lambda item: self._int(item.get("index"), default=0))
        return [text for text in (self._text(row, "text") for row in rows) if text]

    def _references(self, record: Record) -> list[str]:
        references: list[str] = []
        for key in ("thumbnail", "file_id", "generated_video_file_id"):
            value = self._optional_text(record, key)
            if value:
                references.append(value)
        for value in self._as_list(record.get("reference_media")):
            text = self._plain(value)
            if text:
                references.append(str(text))
        for image in self._as_list(record.get("images")):
            if isinstance(image, Mapping):
                references.extend(self._references(image))
            else:
                text = self._plain(image)
                if text:
                    references.append(str(text))
        return self._dedupe(references)

    def _result_media(self, record: Record) -> list[str]:
        result = record.get("result")
        if isinstance(result, Mapping):
            media = []
            for key in ("file_id", "video_file_id", "output_path", "url"):
                value = self._optional_text(result, key)
                if value:
                    media.append(value)
            media.extend(str(value) for value in self._as_list(result.get("media")))
            return self._dedupe(media)
        return self._references(record)

    def _ids_from(self, value: object) -> list[str]:
        ids = []
        for item in self._as_list(value):
            if isinstance(item, Mapping):
                item_id = self._text(item, "id", "chapter_id", "shot_id", "asset_id")
                if item_id:
                    ids.append(item_id)
            elif item is not None:
                ids.append(str(item))
        return self._dedupe(ids)

    def _direct_ids(self, record: Record, key: str) -> list[str]:
        return [str(item) for item in self._as_list(record.get(key)) if item not in (None, "")]

    def _direct_texts(self, record: Record, key: str) -> list[str]:
        return [str(item) for item in self._as_list(record.get(key)) if item not in (None, "")]

    def _readiness(self, status: str) -> str:
        if status in self.READY_STATUSES:
            return "ready"
        if status in self.ACTIVE_STATUSES:
            return "processing"
        return "draft"

    def _metadata(self, record: Record, *, exclude: set[str]) -> dict[str, object]:
        return {
            str(key): self._plain(value)
            for key, value in record.items()
            if str(key) not in exclude and value is not None
        }

    def _required(self, record: Record, *keys: str) -> str:
        value = self._text(record, *keys)
        if not value:
            raise ValueError(f"Missing required Jellyfish field: {'/'.join(keys)}")
        return value

    def _text(self, record: Record, *keys: str, default: str = "") -> str:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return str(self._plain(value))
        return default

    def _optional_text(self, record: Record, key: str) -> str | None:
        value = record.get(key)
        if value in (None, ""):
            return None
        return str(self._plain(value))

    def _int(self, value: object, *, default: int) -> int:
        if value in (None, ""):
            return default
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    def _float(self, value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def _bool(self, value: object, *, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() not in {"0", "false", "no", "off"}
        return bool(value)

    def _as_list(self, value: object) -> list[object]:
        if value is None:
            return []
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, set):
            return list(value)
        return [value]

    def _plain(self, value: object) -> object:
        if hasattr(value, "value"):
            return getattr(value, "value")
        return value

    def _dedupe(self, values: list[str]) -> list[str]:
        seen = set()
        deduped = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped
