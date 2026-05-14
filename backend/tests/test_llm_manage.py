from __future__ import annotations

from fastapi import HTTPException
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.config import settings
from app.models.llm import LogLevel, Model, ModelCategoryKey, ModelSettings, Provider
from app.schemas.llm import ModelCreate, ModelSettingsUpdate, ModelUpdate, ProviderCreate
from app.services.llm.env_bootstrap import BAILIAN_MODEL_ID, BAILIAN_PROVIDER_ID, ensure_bailian_default_text_model
from app.services.llm.manage import (
    create_model,
    create_provider,
    get_image_generation_options,
    get_or_create_settings,
    get_runtime_model_config,
    list_models_paginated,
    list_supported_providers,
    update_model,
    update_model_settings,
)


async def _build_session() -> tuple[AsyncSession, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return session_local(), engine


@pytest.mark.asyncio
async def test_create_model_persists_with_non_default_flag() -> None:
    db, engine = await _build_session()
    async with db:
        await create_provider(
            db,
            body=ProviderCreate(
                id="p1",
                name="OpenAI",
                base_url="https://api.openai.com/v1",
                api_key="k",
            ),
        )
        created = await create_model(
            db,
            body=ModelCreate(
                id="m1",
                name="gpt-4o-mini",
                category=ModelCategoryKey.text,
                provider_id="p1",
            ),
        )
        assert created.id == "m1"
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_model_allows_regular_field_updates() -> None:
    db, engine = await _build_session()
    async with db:
        provider = Provider(id="p1", name="OpenAI", base_url="https://api.openai.com/v1", api_key="k")
        db.add(provider)
        db.add(
            Model(
                id="m_text",
                name="gpt-4o-mini",
                category=ModelCategoryKey.text,
                provider_id="p1",
            )
        )
        await db.commit()

        updated = await update_model(
            db,
            model_id="m_text",
            body=ModelUpdate(description="updated"),
        )
        assert updated.description == "updated"
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_or_create_settings_behaves_like_singleton() -> None:
    db, engine = await _build_session()
    async with db:
        first = await get_or_create_settings(db)
        second = await get_or_create_settings(db)

        rows = (await db.execute(select(ModelSettings))).scalars().all()

        assert first.id == 1
        assert second.id == 1
        assert len(rows) == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_model_settings_persists_latest_values() -> None:
    db, engine = await _build_session()
    async with db:
        updated = await update_model_settings(
            db,
            body=ModelSettingsUpdate(api_timeout=45, log_level=LogLevel.debug),
        )

        stored = await db.get(ModelSettings, 1)
        assert updated.id == 1
        assert updated.api_timeout == 45
        assert updated.log_level == LogLevel.debug
        assert stored is not None and stored.api_timeout == 45
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_models_paginated_returns_filtered_items() -> None:
    db, engine = await _build_session()
    async with db:
        provider = Provider(id="p1", name="OpenAI", base_url="https://api.openai.com/v1", api_key="k")
        db.add(provider)
        db.add_all(
            [
                Model(id="m1", name="gpt-4o-mini", category=ModelCategoryKey.text, provider_id="p1"),
                Model(id="m2", name="seedream", category=ModelCategoryKey.image, provider_id="p1"),
            ]
        )
        await db.commit()

        resp = await list_models_paginated(
            db,
            provider_id="p1",
            category=ModelCategoryKey.image,
            q="seed",
            order="created_at",
            is_desc=False,
            page=1,
            page_size=10,
            allow_fields={"created_at", "name"},
        )

        assert resp.data is not None
        assert resp.data.pagination.total == 1
        assert [item.id for item in resp.data.items] == ["m2"]
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_model_rejects_unsupported_category_for_provider() -> None:
    db, engine = await _build_session()
    async with db:
        await create_provider(
            db,
            body=ProviderCreate(
                id="p-bailian",
                name="阿里百炼",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key="k",
            ),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_model(
                db,
                body=ModelCreate(
                    id="m-video-invalid",
                    name="qwen-vl-video",
                    category=ModelCategoryKey.video,
                    provider_id="p-bailian",
                ),
            )
        assert exc_info.value.status_code == 400
        assert "does not support category=video" in str(exc_info.value.detail)
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_model_rejects_switch_to_unsupported_provider_category_combo() -> None:
    db, engine = await _build_session()
    async with db:
        await create_provider(
            db,
            body=ProviderCreate(
                id="p-openai",
                name="OpenAI",
                base_url="https://api.openai.com/v1",
                api_key="k",
            ),
        )
        await create_provider(
            db,
            body=ProviderCreate(
                id="p-bailian",
                name="阿里百炼",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key="k",
            ),
        )
        await create_model(
            db,
            body=ModelCreate(
                id="m-video-ok",
                name="sora",
                category=ModelCategoryKey.video,
                provider_id="p-openai",
            ),
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_model(
                db,
                model_id="m-video-ok",
                body=ModelUpdate(provider_id="p-bailian"),
            )
        assert exc_info.value.status_code == 400
        assert "does not support category=video" in str(exc_info.value.detail)
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_image_generation_options_uses_default_image_model_capability() -> None:
    db, engine = await _build_session()
    async with db:
        await create_provider(
            db,
            body=ProviderCreate(
                id="p-volc",
                name="火山引擎",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key="k",
            ),
        )
        await create_model(
            db,
            body=ModelCreate(
                id="m-image-default",
                name="seedream-4.0",
                category=ModelCategoryKey.image,
                provider_id="p-volc",
            ),
        )
        await update_model_settings(
            db,
            body=ModelSettingsUpdate(default_image_model_id="m-image-default"),
        )

        options = await get_image_generation_options(db)

        assert options.provider == "volcengine"
        assert options.model_id == "m-image-default"
        assert options.default_resolution_profile == "standard"
        assert options.ratio_size_profiles["9:16"]["standard"] == "1600x2848"
        assert options.ratio_size_profiles["21:9"]["high"] == "4704x2016"
    await engine.dispose()


@pytest.mark.asyncio
async def test_runtime_model_config_isolates_generic_video_provider_base_url_and_key_state() -> None:
    db, engine = await _build_session()
    async with db:
        await create_provider(
            db,
            body=ProviderCreate(
                id="p-kling",
                name="Kling",
                base_url="https://gateway.example/kling",
                video_base_url="https://video-gateway.example/kling",
                api_key="sk-kling",
            ),
        )
        await create_model(
            db,
            body=ModelCreate(
                id="m-kling-video",
                name="kling-v2",
                category=ModelCategoryKey.video,
                provider_id="p-kling",
                params={"duration": 6},
            ),
        )

        config = await get_runtime_model_config(db, model_id="m-kling-video")

        assert config.provider_key == "kling"
        assert config.base_url == "https://video-gateway.example/kling"
        assert config.api_key_configured is True
        assert config.isolated_adapter == "kling:video"
        assert config.params == {"duration": 6}
    await engine.dispose()


@pytest.mark.asyncio
async def test_env_bootstrap_configures_bailian_as_default_text_model(monkeypatch) -> None:
    db, engine = await _build_session()
    monkeypatch.setattr(settings, "aliyun_bailian_api_key", None)
    monkeypatch.setattr(settings, "bailian_api_key", "sk-test-bailian")
    monkeypatch.setattr(settings, "dashscope_api_key", None)
    monkeypatch.setattr(settings, "vite_api_key", None)
    monkeypatch.setattr(settings, "bailian_model", "qwen-max")
    monkeypatch.setattr(settings, "aliyun_bailian_model", None)
    monkeypatch.setattr(settings, "dashscope_model", None)
    monkeypatch.setattr(settings, "bailian_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    async with db:
        bootstrapped = await ensure_bailian_default_text_model(db)
        await db.commit()

        provider = await db.get(Provider, BAILIAN_PROVIDER_ID)
        model = await db.get(Model, BAILIAN_MODEL_ID)
        model_settings = await db.get(ModelSettings, 1)
        runtime_config = await get_runtime_model_config(db, model_id=BAILIAN_MODEL_ID)

        assert bootstrapped is True
        assert provider is not None
        assert provider.api_key == "sk-test-bailian"
        assert model is not None
        assert model.name == "qwen-max"
        assert model_settings is not None
        assert model_settings.default_text_model_id == BAILIAN_MODEL_ID
        assert runtime_config.provider_key == "aliyun_bailian"
        assert runtime_config.api_key_configured is True
    await engine.dispose()


def test_builtin_provider_registry_includes_cinematic_runtime_gateways() -> None:
    video_keys = {item.key for item in list_supported_providers(category=ModelCategoryKey.video)}
    image_keys = {item.key for item in list_supported_providers(category=ModelCategoryKey.image)}

    assert {"kling", "seedance", "veo", "wan2_1", "sora", "vidu"}.issubset(video_keys)
    assert {"comfyui", "flux", "sdxl", "storydiffusion"}.issubset(image_keys)
