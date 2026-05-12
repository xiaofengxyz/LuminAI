from __future__ import annotations

from app.models.llm import ModelCategoryKey
from app.services.llm.provider_registry import ProviderSpec, register_many


def bootstrap_builtin_providers() -> None:
    register_many(
        [
            ProviderSpec(
                key="openai",
                display_name="OpenAI",
                aliases=("openai",),
                supported_categories=(
                    ModelCategoryKey.text,
                    ModelCategoryKey.image,
                    ModelCategoryKey.video,
                ),
                default_base_url="https://api.openai.com/v1",
            ),
            ProviderSpec(
                key="volcengine",
                display_name="火山引擎",
                aliases=("火山引擎", "volcengine", "volc", "doubao", "bytedance", "ark"),
                supported_categories=(ModelCategoryKey.image, ModelCategoryKey.video),
                default_base_url="https://ark.cn-beijing.volces.com/api/v3",
            ),
            ProviderSpec(
                key="aliyun_bailian",
                display_name="阿里百炼",
                aliases=("阿里百炼", "aliyun", "bailian", "dashscope"),
                supported_categories=(ModelCategoryKey.text,),
                default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            ProviderSpec(
                key="comfyui",
                display_name="ComfyUI",
                aliases=("comfyui", "comfy", "comfy ui"),
                supported_categories=(ModelCategoryKey.image,),
                default_base_url="http://127.0.0.1:8188",
                requires_api_key=False,
            ),
            ProviderSpec(
                key="flux",
                display_name="FLUX Runtime",
                aliases=("flux", "black forest labs", "bfl"),
                supported_categories=(ModelCategoryKey.image,),
                requires_api_key=False,
                is_experimental=True,
            ),
            ProviderSpec(
                key="sdxl",
                display_name="SDXL Runtime",
                aliases=("sdxl", "stable diffusion xl", "stable-diffusion-xl"),
                supported_categories=(ModelCategoryKey.image,),
                requires_api_key=False,
                is_experimental=True,
            ),
            ProviderSpec(
                key="storydiffusion",
                display_name="StoryDiffusion",
                aliases=("storydiffusion", "story diffusion"),
                supported_categories=(ModelCategoryKey.image,),
                requires_api_key=False,
                is_experimental=True,
            ),
            ProviderSpec(
                key="kling",
                display_name="Kling",
                aliases=("kling", "快手可灵", "可灵"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
            ProviderSpec(
                key="seedance",
                display_name="Seedance",
                aliases=("seedance", "seedance video", "豆包视频", "即梦视频"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
            ProviderSpec(
                key="veo",
                display_name="Veo",
                aliases=("veo", "google veo"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
            ProviderSpec(
                key="wan2_1",
                display_name="Wan2.1",
                aliases=("wan", "wan2.1", "wan2_1", "通义万相"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
            ProviderSpec(
                key="sora",
                display_name="Sora",
                aliases=("sora", "openai sora"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
            ProviderSpec(
                key="vidu",
                display_name="Vidu",
                aliases=("vidu", "生数科技"),
                supported_categories=(ModelCategoryKey.video,),
                is_experimental=True,
            ),
        ]
    )
