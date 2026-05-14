"""从环境变量引导本地默认 LLM 配置。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.llm import Model, ModelCategoryKey, ModelSettings, Provider, ProviderStatus


BAILIAN_PROVIDER_ID = "aliyun_bailian"
BAILIAN_MODEL_ID = "aliyun_bailian_text_default"


async def ensure_bailian_default_text_model(db: AsyncSession) -> bool:
    """确保阿里百炼被配置为默认文本大模型。

    返回值用于测试和诊断：`True` 表示本次发现可用密钥并完成了 Provider /
    Model / Settings 引导；`False` 表示环境里没有密钥，因此不修改数据库。
    """

    api_key = settings.bailian_resolved_api_key
    if not api_key:
        return False

    provider = await db.get(Provider, BAILIAN_PROVIDER_ID)
    if provider is None:
        provider = Provider(
            id=BAILIAN_PROVIDER_ID,
            name="阿里百炼",
            base_url=settings.bailian_resolved_base_url,
            api_key=api_key,
            description="由 .env 自动引导的阿里百炼文本大模型 Provider。",
            status=ProviderStatus.active,
            created_by="system_env_bootstrap",
        )
        db.add(provider)
    else:
        # 环境变量是本地重启恢复的权威来源；只更新必要字段，避免破坏用户说明。
        provider.name = "阿里百炼"
        provider.base_url = settings.bailian_resolved_base_url
        provider.api_key = api_key
        provider.status = ProviderStatus.active

    model = await db.get(Model, BAILIAN_MODEL_ID)
    if model is None:
        model = Model(
            id=BAILIAN_MODEL_ID,
            name=settings.bailian_resolved_model_name,
            category=ModelCategoryKey.text,
            provider_id=BAILIAN_PROVIDER_ID,
            params={"temperature": 0},
            description="由 .env 自动引导的默认百炼文本模型。",
            created_by="system_env_bootstrap",
        )
        db.add(model)
    else:
        # 模型名可通过 .env 覆盖，模型 ID 保持稳定以便默认设置长期引用。
        model.name = settings.bailian_resolved_model_name
        model.category = ModelCategoryKey.text
        model.provider_id = BAILIAN_PROVIDER_ID

    model_settings = await db.get(ModelSettings, 1)
    if model_settings is None:
        model_settings = ModelSettings(id=1)
        db.add(model_settings)

    # 用户明确要求大模型使用阿里百炼，因此启动引导总是刷新默认文本模型。
    model_settings.default_text_model_id = BAILIAN_MODEL_ID
    await db.flush()
    return True
