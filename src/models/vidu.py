from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from src.utils.oss import OSSImageUploader
from src.utils.provider_media import resolve_media_input


class ViduModel:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.vidu.com/v1").rstrip("/")
        self.poll_interval = float(config.get("poll_interval", 1))

    def generate(
        self,
        *,
        prompt: str,
        output_path: str,
        img_path: str | None = None,
        img_url: str | None = None,
        model: str = "viduq3-pro",
        duration: int = 5,
        seed: int | None = None,
        audio: bool | None = None,
        movement_amplitude: str | None = None,
        negative_prompt: str | None = None,
        **_: Any,
    ) -> tuple[str, float]:
        started = time.time()
        image_ref = img_path or img_url
        body: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
        }
        if image_ref:
            resolved = resolve_media_input(
                image_ref,
                model_name=model,
                backend="vendor",
                modality="image",
                uploader=OSSImageUploader(),
            )
            body["images"] = [resolved.value]
        optional = {
            "seed": seed,
            "audio": audio,
            "movement_amplitude": movement_amplitude,
            "negative_prompt": negative_prompt,
        }
        body.update({key: value for key, value in optional.items() if value is not None})

        headers = {"Authorization": f"Token {self.api_key}"}
        create = requests.post(
            f"{self.base_url}/img2video" if image_ref else f"{self.base_url}/text2video",
            headers=headers,
            json=body,
            timeout=60,
        )
        payload = create.json()
        task_id = payload.get("task_id") or payload.get("id")
        if not task_id:
            raise RuntimeError(f"Vidu response missing task id: {payload}")

        video_url = self._poll(task_id, headers)
        self._download(video_url, output_path)
        return output_path, time.time() - started

    def _poll(self, task_id: str, headers: dict[str, str]) -> str:
        for _ in range(120):
            response = requests.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=headers,
                timeout=60,
            )
            payload = response.json()
            state = payload.get("state") or payload.get("status")
            if state in {"success", "succeed", "SUCCEEDED"}:
                creations = payload.get("creations") or []
                if creations:
                    return creations[0]["url"]
                if payload.get("url"):
                    return payload["url"]
            if state in {"failed", "error", "FAILED"}:
                raise RuntimeError(f"Vidu task failed: {payload}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Vidu task timed out: {task_id}")

    @staticmethod
    def _download(video_url: str, output_path: str) -> None:
        response = requests.get(video_url, timeout=120)
        content = getattr(response, "content", b"")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(content)
