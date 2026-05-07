from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ProviderFamilyConfig:
    model_family: str
    backend_default: str = "dashscope"
    backend_env_key: str | None = None
    credential_sources: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    supported_modalities: tuple[str, ...] = ()
    image_input_mode: Mapping[str, str] = field(default_factory=dict)
    audio_input_mode: Mapping[str, str] = field(default_factory=dict)
    reference_video_input_mode: Mapping[str, str] = field(default_factory=dict)


class ProviderRegistry:
    def __init__(self) -> None:
        self._families: list[ProviderFamilyConfig] = []

    def register_family(self, config: ProviderFamilyConfig) -> None:
        self._families.append(config)
        self._families.sort(key=lambda item: len(item.model_family), reverse=True)

    def resolve_family(self, model_name: str) -> ProviderFamilyConfig:
        for family in self._families:
            if model_name.startswith(family.model_family):
                return family
        raise KeyError(f"No provider family registered for model: {model_name}")

    def resolve_backend(
        self,
        model_name: str,
        env: Mapping[str, str] | None = None,
    ) -> str:
        family = self.resolve_family(model_name)
        values = env if env is not None else os.environ
        requested = ""
        if family.backend_env_key:
            requested = values.get(family.backend_env_key, "").strip().lower()
        if requested in {"dashscope", "vendor"}:
            return requested
        return family.backend_default


def get_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register_family(
        ProviderFamilyConfig(
            model_family="wan2.6-",
            backend_default="dashscope",
            credential_sources={"dashscope": ("DASHSCOPE_API_KEY",)},
            supported_modalities=("t2i", "i2i", "i2v", "r2v"),
            image_input_mode={"dashscope": "dashscope_image_input"},
            audio_input_mode={"dashscope": "dashscope_temp_file_url"},
            reference_video_input_mode={"dashscope": "dashscope_temp_file_url"},
        )
    )
    registry.register_family(
        ProviderFamilyConfig(
            model_family="kling",
            backend_default="dashscope",
            backend_env_key="KLING_PROVIDER_MODE",
            credential_sources={
                "dashscope": ("DASHSCOPE_API_KEY",),
                "vendor": ("KLING_ACCESS_KEY", "KLING_SECRET_KEY"),
            },
            supported_modalities=("t2v", "i2v"),
            image_input_mode={
                "dashscope": "dashscope_image_input",
                "vendor": "kling_vendor_base64",
            },
        )
    )
    registry.register_family(
        ProviderFamilyConfig(
            model_family="vidu",
            backend_default="dashscope",
            backend_env_key="VIDU_PROVIDER_MODE",
            credential_sources={
                "dashscope": ("DASHSCOPE_API_KEY",),
                "vendor": ("VIDU_API_KEY",),
            },
            supported_modalities=("t2v", "i2v"),
            image_input_mode={
                "dashscope": "dashscope_image_input",
                "vendor": "vidu_vendor_url",
            },
        )
    )
    registry.register_family(
        ProviderFamilyConfig(
            model_family="pixverse-",
            backend_default="dashscope",
            backend_env_key="PIXVERSE_PROVIDER_MODE",
            credential_sources={
                "dashscope": ("DASHSCOPE_API_KEY",),
                "vendor": ("PIXVERSE_API_KEY",),
            },
            supported_modalities=("t2v", "i2v"),
            image_input_mode={
                "dashscope": "dashscope_image_input",
                "vendor": "pixverse_vendor_image_input",
            },
        )
    )
    return registry


def resolve_provider_backend(model_name: str, env: Mapping[str, str] | None = None) -> str:
    return get_default_provider_registry().resolve_backend(model_name, env=env)


def get_provider_base_url(provider: str) -> str:
    if provider == "dashscope":
        return os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com")
    return ""
