from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShotContinuityState:
    shot_id: str
    character_ids: list[str] = field(default_factory=list)
    scene_id: str | None = None
    outfit_map: dict[str, str] = field(default_factory=dict)
    emotion_map: dict[str, str] = field(default_factory=dict)
    lighting: str | None = None
    timeline_position: str | None = None
    reference_media: list[str] = field(default_factory=list)


@dataclass
class FilmState:
    series_id: str | None = None
    episode_id: str | None = None
    shots: dict[str, ShotContinuityState] = field(default_factory=dict)

    def record_shot(self, state: ShotContinuityState) -> None:
        self.shots[state.shot_id] = state

    def previous_shot(self, shot_id: str) -> ShotContinuityState | None:
        keys = list(self.shots)
        if shot_id not in self.shots:
            return self.shots[keys[-1]] if keys else None
        index = keys.index(shot_id)
        if index == 0:
            return None
        return self.shots[keys[index - 1]]
