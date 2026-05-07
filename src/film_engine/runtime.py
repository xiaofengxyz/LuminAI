from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RenderRequest:
    shot_id: str
    prompt: str
    model: str
    output_path: str
    references: list[str] = field(default_factory=list)
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass
class RenderResult:
    shot_id: str
    output_path: str
    runtime: str
    metadata: dict[str, object] = field(default_factory=dict)


class RuntimeAdapter(Protocol):
    name: str

    def render(self, request: RenderRequest) -> RenderResult:
        ...
