from __future__ import annotations

import os
from pathlib import Path


class OSSImageUploader:
    """Small OSS facade used by provider adapters.

    Real deployments can replace this with a full uploader. The default keeps
    tests and local-only flows deterministic while preserving the runtime seam.
    """

    def __init__(self) -> None:
        self.bucket = os.getenv("OSS_BUCKET_NAME", "")
        self.endpoint = os.getenv("OSS_ENDPOINT", "").rstrip("/")
        self.base_path = os.getenv("OSS_BASE_PATH", "lumenx").strip("/")
        self.access_key = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
        self.secret_key = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
        self.is_configured = all(
            [self.bucket, self.endpoint, self.access_key, self.secret_key]
        )

    def upload_file(
        self,
        local_path: str,
        sub_path: str = "",
        custom_filename: str | None = None,
    ) -> str | None:
        if not self.is_configured:
            return None
        filename = custom_filename or Path(local_path).name
        parts = [self.base_path]
        if sub_path:
            parts.append(sub_path.strip("/"))
        parts.append(filename)
        return "/".join(part for part in parts if part)

    def sign_url_for_api(self, object_key: str) -> str:
        if object_key.startswith("oss://"):
            object_key = object_key.removeprefix("oss://")
        if self.endpoint and self.bucket:
            return f"{self.endpoint}/{self.bucket}/{object_key.lstrip('/')}"
        return object_key
