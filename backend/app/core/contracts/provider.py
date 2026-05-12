"""生成能力共享的供应商类型契约。"""

from __future__ import annotations

from dataclasses import dataclass
# Provider keys are registry-owned strings, not a closed enum.  This keeps
# runtime workers isolated from concrete vendors while still allowing built-in
# adapters to special-case OpenAI or Volcengine where needed.
ProviderKey = str


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """执行生成任务时需要的供应商配置。"""

    provider: ProviderKey
    api_key: str
    base_url: str | None = None
