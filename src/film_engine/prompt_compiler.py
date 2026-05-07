from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.state import ShotContinuityState


@dataclass
class CompiledPrompt:
    provider: str
    text: str
    negative_text: str = ""
    references: list[str] = field(default_factory=list)
    parameters: dict[str, object] = field(default_factory=dict)


class PromptCompiler:
    def compile_shot(
        self,
        *,
        provider: str,
        director_dsl: dict[str, object],
        continuity: ShotContinuityState,
    ) -> CompiledPrompt:
        parts = [
            f"shot={continuity.shot_id}",
            f"scene={continuity.scene_id or 'unknown'}",
            f"characters={','.join(continuity.character_ids) or 'none'}",
        ]
        for key in ("framing", "movement", "lens", "emotion", "pacing"):
            if key in director_dsl and director_dsl[key]:
                parts.append(f"{key}={director_dsl[key]}")
        if continuity.lighting:
            parts.append(f"lighting={continuity.lighting}")
        if continuity.outfit_map:
            outfit_text = ", ".join(
                f"{character}:{outfit}"
                for character, outfit in sorted(continuity.outfit_map.items())
            )
            parts.append(f"outfits={outfit_text}")
        return CompiledPrompt(
            provider=provider,
            text="; ".join(parts),
            negative_text="identity drift, outfit inconsistency, broken anatomy",
            references=list(continuity.reference_media),
            parameters={
                "camera": director_dsl.get("movement"),
                "pacing": director_dsl.get("pacing"),
            },
        )
