from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

import requests


class KlingModel:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.access_key = config.get("access_key", "")
        self.secret_key = config.get("secret_key", "")
        self.base_url = config.get("base_url", "https://api.klingai.com/v1").rstrip("/")
        self.poll_interval = float(config.get("poll_interval", 1))

    def generate(
        self,
        *,
        prompt: str,
        output_path: str,
        img_path: str | None = None,
        img_url: str | None = None,
        model: str = "kling-v1",
        duration: int = 5,
        seed: int | None = None,
        mode: str | None = None,
        sound: str | None = None,
        cfg_scale: float | None = None,
        negative_prompt: str | None = None,
        **_: Any,
    ) -> tuple[str, float]:
        started = time.time()
        endpoint = "image2video" if (img_path or img_url) else "text2video"
        body: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
        }
        if img_path:
            body["image"] = self._image_to_base64(img_path)
        elif img_url:
            body["image"] = img_url
        optional = {
            "seed": seed,
            "mode": mode,
            "sound": sound,
            "cfg_scale": cfg_scale,
            "negative_prompt": negative_prompt,
        }
        body.update({key: value for key, value in optional.items() if value is not None})

        headers = {"Authorization": f"Bearer {self._token()}"}
        create = requests.post(
            f"{self.base_url}/videos/{endpoint}",
            headers=headers,
            json=body,
            timeout=60,
        )
        self._raise_for_status(create)
        payload = create.json()
        task_id = (
            payload.get("data", {}).get("task_id")
            or payload.get("task_id")
            or payload.get("id")
        )
        if not task_id:
            raise RuntimeError(f"Kling response missing task id: {payload}")

        video_url = self._poll(task_id, endpoint, headers)
        self._download(video_url, output_path)
        return output_path, time.time() - started

    def _poll(self, task_id: str, endpoint: str, headers: dict[str, str]) -> str:
        for _ in range(120):
            response = requests.get(
                f"{self.base_url}/videos/{endpoint}/{task_id}",
                headers=headers,
                timeout=60,
            )
            self._raise_for_status(response)
            payload = response.json()
            data = payload.get("data", payload)
            status = data.get("task_status") or data.get("status")
            if status in {"succeed", "success", "SUCCEEDED"}:
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    return videos[0]["url"]
                if data.get("url"):
                    return data["url"]
            if status in {"failed", "error", "FAILED"}:
                raise RuntimeError(f"Kling task failed: {payload}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Kling task timed out: {task_id}")

    @staticmethod
    def _download(video_url: str, output_path: str) -> None:
        response = requests.get(video_url, timeout=120)
        content = getattr(response, "content", b"")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(content)

    @staticmethod
    def _image_to_base64(path_or_url: str) -> str:
        path = Path(path_or_url)
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode("ascii")
        return path_or_url

    def _token(self) -> str:
        return f"{self.access_key}:{self.secret_key}"

    @staticmethod
    def _raise_for_status(response) -> None:
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        elif getattr(response, "status_code", 200) >= 400:
            raise RuntimeError(getattr(response, "text", "HTTP error"))
