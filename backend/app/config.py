"""应用配置，从环境变量加载。"""

import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent.parent.parent
ENV_FILES = (REPO_ROOT / ".env", BACKEND_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(path) for path in ENV_FILES),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Jellyfish API"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./jellyfish.db"

    # Redis / Celery Broker
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    celery_broker_url: str | None = None

    # CORS：环境变量中建议使用逗号分隔（更贴近 docker-compose 用法）
    # 也兼容 JSON 数组：'["http://a","http://b"]'
    cors_origins: str = (
        "http://localhost:7788,http://127.0.0.1:7788,"
        "http://localhost:7790,http://127.0.0.1:7790,"
        "http://localhost:24732,http://127.0.0.1:24732"
    )
    # 本地前端端口在冲突时会从 7788 漂移到 7790/其他端口；正则只放行本机开发源。
    cors_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @property
    def cors_origins_list(self) -> list[str]:
        s = (self.cors_origins or "").strip()
        if not s:
            return []
        if s.startswith("["):
            loaded = json.loads(s)
            if isinstance(loaded, list):
                return [str(x).strip() for x in loaded if str(x).strip()]
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    @property
    def cors_origin_regex_value(self) -> str | None:
        s = (self.cors_origin_regex or "").strip()
        return s or None

    # S3 / 对象存储（用于素材文件）
    s3_endpoint_url: str | None = None
    s3_region_name: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    # 可选：统一前缀，方便按环境/项目隔离，如 "jellyfish/dev"
    s3_base_path: str = ""
    # 可选：对外访问基址（CDN 或自定义域名），为空则使用 S3 自带 URL 或预签名 URL
    s3_public_base_url: str | None = None

    # 阿里百炼 / DashScope 兼容 OpenAI 的文本模型默认配置。
    # 多个变量名用于兼容历史 .env；密钥只用于后端调用，不在 API 中回显。
    aliyun_bailian_api_key: str | None = None
    bailian_api_key: str | None = None
    dashscope_api_key: str | None = None
    vite_api_key: str | None = None
    aliyun_bailian_base_url: str | None = None
    bailian_base_url: str | None = None
    dashscope_base_url: str | None = None
    aliyun_bailian_model: str | None = None
    bailian_model: str | None = None
    dashscope_model: str | None = None

    @property
    def bailian_resolved_api_key(self) -> str:
        """按兼容优先级解析阿里百炼 API Key。"""
        for value in (
            self.aliyun_bailian_api_key,
            self.bailian_api_key,
            self.dashscope_api_key,
            self.vite_api_key,
        ):
            if value and value.strip():
                return value.strip()
        return ""

    @property
    def bailian_resolved_base_url(self) -> str:
        """解析阿里百炼 OpenAI-compatible Base URL。"""
        for value in (
            self.aliyun_bailian_base_url,
            self.bailian_base_url,
            self.dashscope_base_url,
        ):
            if value and value.strip():
                return value.strip().rstrip("/")
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @property
    def bailian_resolved_model_name(self) -> str:
        """解析默认百炼文本模型名。"""
        for value in (
            self.aliyun_bailian_model,
            self.bailian_model,
            self.dashscope_model,
        ):
            if value and value.strip():
                return value.strip()
        return "qwen-plus"

    def model_post_init(self, __context: object) -> None:
        if not self.celery_broker_url or not str(self.celery_broker_url).strip():
            password_part = f":{self.redis_password}@" if self.redis_password else ""
            self.celery_broker_url = f"redis://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
