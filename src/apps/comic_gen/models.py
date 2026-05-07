from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _now() -> float:
    return time.time()


class ProviderBackend(str, Enum):
    DASHSCOPE = "dashscope"
    VENDOR = "vendor"


class ProviderRoutingConfig(BaseModel):
    KLING_PROVIDER_MODE: ProviderBackend = ProviderBackend.DASHSCOPE
    VIDU_PROVIDER_MODE: ProviderBackend = ProviderBackend.DASHSCOPE
    PIXVERSE_PROVIDER_MODE: ProviderBackend = ProviderBackend.DASHSCOPE

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_backend(cls, value: Any) -> ProviderBackend:
        if isinstance(value, ProviderBackend):
            return value
        if isinstance(value, str) and value.lower() in {b.value for b in ProviderBackend}:
            return ProviderBackend(value.lower())
        return ProviderBackend.DASHSCOPE


class PromptConfig(BaseModel):
    storyboard_polish: str = ""
    video_polish: str = ""
    r2v_polish: str = ""


class ModelSettings(BaseModel):
    t2i_model: str = "wan2.6-t2i"
    i2i_model: str = "wan2.6-image"
    i2v_model: str = "wan2.6-i2v"
    storyboard_aspect_ratio: str = "16:9"
    video_resolution: str = "720P"
    video_duration: int = 5


class Character(BaseModel):
    id: str
    name: str
    description: str = ""
    image_url: str | None = None
    reference_images: list[str] = Field(default_factory=list)
    lora: str | None = None
    embedding: str | None = None
    outfit: str | None = None
    voice_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    id: str
    name: str
    description: str = ""
    image_url: str | None = None
    lighting: str | None = None
    weather: str | None = None
    tone: str | None = None
    mood: str | None = None
    camera_style: str | None = None


class Prop(BaseModel):
    id: str
    name: str
    description: str = ""
    image_url: str | None = None
    reference_images: list[str] = Field(default_factory=list)


class StoryboardFrame(BaseModel):
    id: str
    scene_id: str | None = None
    character_ids: list[str] = Field(default_factory=list)
    prop_ids: list[str] = Field(default_factory=list)
    prompt: str = ""
    rendered_image_url: str | None = None
    camera: dict[str, Any] = Field(default_factory=dict)
    duration: float | None = None


class VideoTask(BaseModel):
    id: str
    project_id: str
    image_url: str
    prompt: str
    status: str = "pending"
    video_url: str | None = None
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
    created_at: float = Field(default_factory=_now)
    updated_at: float = Field(default_factory=_now)


class Script(BaseModel):
    id: str
    title: str
    original_text: str = ""
    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    props: list[Prop] = Field(default_factory=list)
    frames: list[StoryboardFrame] = Field(default_factory=list)
    video_tasks: list[VideoTask] = Field(default_factory=list)
    prompt_config: PromptConfig = Field(default_factory=PromptConfig)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    series_id: str | None = None
    episode_number: int | None = None
    created_at: float = Field(default_factory=_now)
    updated_at: float = Field(default_factory=_now)


class Series(BaseModel):
    id: str
    title: str
    description: str = ""
    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    props: list[Prop] = Field(default_factory=list)
    art_direction: str | None = None
    prompt_config: PromptConfig = Field(default_factory=PromptConfig)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    episode_ids: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=_now)
    updated_at: float = Field(default_factory=_now)
