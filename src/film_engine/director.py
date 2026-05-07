from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.platform import StudioShot
from src.film_engine.state import ShotContinuityState


@dataclass
class DirectorIssue:
    code: str
    severity: str
    message: str
    repair_hint: str = ""


@dataclass
class DirectorRuleResult:
    passed: bool
    issues: list[DirectorIssue] = field(default_factory=list)


@dataclass
class CharacterBible:
    id: str
    name: str
    reference_media: list[str] = field(default_factory=list)
    outfits: dict[str, str] = field(default_factory=dict)
    default_outfit: str | None = None
    voice_id: str | None = None
    lora: str | None = None
    embeddings: list[str] = field(default_factory=list)
    identity_terms: list[str] = field(default_factory=list)
    negative_terms: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def outfit_for(self, outfit_id: str | None = None) -> str | None:
        selected = outfit_id or self.default_outfit
        if selected and selected in self.outfits:
            return self.outfits[selected]
        if selected:
            return selected
        if self.outfits:
            return next(iter(self.outfits.values()))
        return None


@dataclass
class SceneBible:
    id: str
    name: str
    location: str = ""
    lighting: str | None = None
    weather: str | None = None
    tone: str | None = None
    mood: str | None = None
    camera_style: str | None = None
    reference_media: list[str] = field(default_factory=list)
    continuity_rules: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class PreparedShotContext:
    shot_id: str
    director_dsl: dict[str, object]
    continuity: ShotContinuityState
    character_bibles: dict[str, CharacterBible] = field(default_factory=dict)
    scene_bible: SceneBible | None = None
    issues: list[DirectorIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "high" for issue in self.issues)


class DirectorRuleEngine:
    REQUIRED_SHOT_FIELDS = ("framing", "movement", "lens", "emotion")

    def validate_dsl(self, director_dsl: dict[str, object]) -> DirectorRuleResult:
        issues: list[DirectorIssue] = []
        for field_name in self.REQUIRED_SHOT_FIELDS:
            if not director_dsl.get(field_name):
                issues.append(
                    DirectorIssue(
                        code=f"missing_{field_name}",
                        severity="medium",
                        message=f"Director DSL is missing {field_name}",
                        repair_hint=f"Set {field_name} before prompt compilation.",
                    )
                )
        duration = director_dsl.get("duration")
        if duration is not None:
            try:
                if float(duration) <= 0:
                    issues.append(
                        DirectorIssue(
                            code="invalid_duration",
                            severity="high",
                            message="Shot duration must be greater than zero",
                            repair_hint="Set a positive duration in seconds.",
                        )
                    )
            except (TypeError, ValueError):
                issues.append(
                    DirectorIssue(
                        code="invalid_duration",
                        severity="high",
                        message="Shot duration must be numeric",
                        repair_hint="Use a numeric duration in seconds.",
                    )
                )
        return DirectorRuleResult(passed=not issues, issues=issues)


class DirectorConsistencyEngine:
    def __init__(self, *, rule_engine: DirectorRuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or DirectorRuleEngine()

    def prepare_shot(
        self,
        *,
        shot: StudioShot,
        continuity: ShotContinuityState,
        character_bibles: list[CharacterBible] | None = None,
        scene_bibles: list[SceneBible] | None = None,
    ) -> PreparedShotContext:
        character_map = {character.id: character for character in character_bibles or []}
        scene_map = {scene.id: scene for scene in scene_bibles or []}
        director_dsl = dict(shot.camera)
        if shot.duration is not None:
            director_dsl.setdefault("duration", shot.duration)
        if shot.summary:
            director_dsl.setdefault("summary", shot.summary)

        prepared_continuity = ShotContinuityState(
            shot_id=continuity.shot_id,
            character_ids=list(continuity.character_ids),
            scene_id=continuity.scene_id,
            outfit_map=dict(continuity.outfit_map),
            emotion_map=dict(continuity.emotion_map),
            lighting=continuity.lighting,
            timeline_position=continuity.timeline_position,
            reference_media=list(continuity.reference_media),
        )
        issues = list(self.rule_engine.validate_dsl(director_dsl).issues)
        character_context: dict[str, dict[str, object]] = {}
        voice_map: dict[str, str] = {}
        negative_terms: list[str] = []

        for character_id in prepared_continuity.character_ids:
            bible = character_map.get(character_id)
            if bible is None:
                issues.append(
                    DirectorIssue(
                        code="missing_character_bible",
                        severity="high",
                        message=f"Missing character bible for {character_id}",
                        repair_hint="Create or link a CharacterBible before generation.",
                    )
                )
                continue
            selected_outfit = prepared_continuity.outfit_map.get(character_id)
            outfit = bible.outfit_for(selected_outfit)
            if outfit and character_id not in prepared_continuity.outfit_map:
                prepared_continuity.outfit_map[character_id] = outfit
            if character_id not in prepared_continuity.emotion_map and director_dsl.get("emotion"):
                prepared_continuity.emotion_map[character_id] = str(director_dsl["emotion"])
            prepared_continuity.reference_media.extend(bible.reference_media)
            negative_terms.extend(bible.negative_terms)
            if bible.voice_id:
                voice_map[character_id] = bible.voice_id
            character_context[character_id] = {
                "name": bible.name,
                "outfit": prepared_continuity.outfit_map.get(character_id),
                "lora": bible.lora,
                "embeddings": list(bible.embeddings),
                "identity_terms": list(bible.identity_terms),
            }

        scene_bible = scene_map.get(prepared_continuity.scene_id or "")
        if prepared_continuity.scene_id and scene_bible is None:
            issues.append(
                DirectorIssue(
                    code="missing_scene_bible",
                    severity="high",
                    message=f"Missing scene bible for {prepared_continuity.scene_id}",
                    repair_hint="Create or link a SceneBible before generation.",
                )
            )
        elif scene_bible:
            if prepared_continuity.lighting is None:
                prepared_continuity.lighting = scene_bible.lighting
            prepared_continuity.reference_media.extend(scene_bible.reference_media)
            director_dsl.setdefault("scene_mood", scene_bible.mood)
            director_dsl.setdefault("weather", scene_bible.weather)
            director_dsl.setdefault("tone", scene_bible.tone)
            director_dsl.setdefault("camera_style", scene_bible.camera_style)
            director_dsl.setdefault("location", scene_bible.location or scene_bible.name)

        prepared_continuity.reference_media = self._dedupe(prepared_continuity.reference_media)
        director_dsl["character_context"] = character_context
        if voice_map:
            director_dsl["voice_map"] = voice_map
        if negative_terms:
            director_dsl["negative_terms"] = self._dedupe(negative_terms)

        return PreparedShotContext(
            shot_id=shot.id,
            director_dsl={key: value for key, value in director_dsl.items() if value is not None},
            continuity=prepared_continuity,
            character_bibles=character_map,
            scene_bible=scene_bible,
            issues=issues,
        )

    def _dedupe(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
