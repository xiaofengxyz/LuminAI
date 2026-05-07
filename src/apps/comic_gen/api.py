from __future__ import annotations

from pydantic import BaseModel


class CreateVideoTaskRequest(BaseModel):
    image_url: str
    prompt: str
    model: str = "wan2.6-i2v"
    duration: int = 5
    seed: int | None = None
    resolution: str = "720P"
    generate_audio: bool = False
    prompt_extend: bool = True
    negative_prompt: str | None = None
    shot_type: str = "single"
    generation_mode: str = "i2v"
    mode: str | None = None
    sound: str | None = None
    cfg_scale: float | None = None
    vidu_audio: bool | None = None
    movement_amplitude: str | None = None
