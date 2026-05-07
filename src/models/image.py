from __future__ import annotations

import os
import time
from typing import Any

import requests

from src.utils.oss import OSSImageUploader
from src.utils.provider_media import resolve_media_input
from src.utils.provider_registry import get_provider_base_url, resolve_provider_backend


class WanxImageModel:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.params = config.get("params", {})
        self.base_url = config.get("base_url") or get_provider_base_url("dashscope")
        self.poll_interval = float(config.get("poll_interval", 1))

    def _resolve_wan26_reference_image(
        self,
        ref: str,
        model_name: str | None = None,
    ) -> str:
        model_name = model_name or self.params.get("i2i_model_name", "wan2.6-image")
        try:
            backend = resolve_provider_backend(model_name)
        except KeyError:
            backend = "dashscope"
        resolved = resolve_media_input(
            ref,
            model_name=model_name,
            backend=backend,
            modality="image",
            uploader=OSSImageUploader(),
        )
        return resolved.value

    def _generate_wan26_image_http(
        self,
        *,
        prompt: str,
        size: str = "1280*1280",
        n: int = 1,
        negative_prompt: str | None = None,
        ref_image_paths: list[str] | None = None,
        model_name: str | None = None,
    ) -> str:
        model_name = model_name or self.params.get("i2i_model_name", "wan2.6-image")
        content: list[dict[str, str]] = []
        for ref in ref_image_paths or []:
            content.append({"image": self._resolve_wan26_reference_image(ref, model_name)})
        content.append({"text": prompt})
        payload = {
            "model": model_name,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": {"size": size, "n": n},
        }
        if negative_prompt is not None:
            payload["parameters"]["negative_prompt"] = negative_prompt
        headers = {"Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY', '')}"}
        response = requests.post(
            f"{self.base_url.rstrip('/')}/api/v1/services/aigc/multimodal-generation/generation",
            headers=headers,
            json=payload,
            timeout=60,
        )
        task_id = response.json().get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"Wanx image response missing task id: {response.text}")
        return self._poll_image_task(task_id, headers)

    def _poll_image_task(self, task_id: str, headers: dict[str, str]) -> str:
        for _ in range(120):
            response = requests.get(
                f"{self.base_url.rstrip('/')}/api/v1/tasks/{task_id}",
                headers=headers,
                timeout=60,
            )
            payload = response.json()
            output = payload.get("output", payload)
            status = output.get("task_status") or output.get("status")
            if status in {"SUCCEEDED", "success", "succeed"}:
                choices = output.get("choices") or []
                for choice in choices:
                    content = choice.get("message", {}).get("content", [])
                    for item in content:
                        if "image" in item:
                            return item["image"]
                if output.get("image_url"):
                    return output["image_url"]
            if status in {"FAILED", "failed", "error"}:
                raise RuntimeError(f"Wanx image task failed: {payload}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Wanx image task timed out: {task_id}")
