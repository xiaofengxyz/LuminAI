from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

from src.utils.oss import OSSImageUploader
from src.utils.provider_media import RESOLVE_HEADER_DASHSCOPE_OSS_RESOURCE, resolve_media_input
from src.utils.provider_registry import get_provider_base_url


class WanxModel:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.params = config.get("params", {})
        self.base_url = config.get("base_url") or get_provider_base_url("dashscope")
        self.poll_interval = float(config.get("poll_interval", 1))

    def generate(
        self,
        *,
        prompt: str,
        output_path: str,
        img_path: str | None = None,
        img_url: str | None = None,
        model_name: str | None = None,
        model: str | None = None,
        size: str = "1280*720",
        resolution: str = "720P",
        duration: int = 5,
        prompt_extend: bool = True,
        negative_prompt: str | None = None,
        audio_url: str | None = None,
        watermark: bool = False,
        seed: int | None = None,
        shot_type: str = "single",
        ref_video_urls: list[str] | None = None,
        reference_video_urls: list[str] | None = None,
        camera_motion: str | None = None,
        subject_motion: str | None = None,
        **_: Any,
    ) -> tuple[str, float]:
        started = time.time()
        name = model_name or model or self.params.get("i2v_model_name", "wan2.6-i2v")
        uploader = OSSImageUploader()
        headers: dict[str, str] = {}

        resolved_img = None
        image_ref = img_path or img_url
        if image_ref:
            resolved = resolve_media_input(
                image_ref,
                model_name=name,
                backend="dashscope",
                modality="image",
                uploader=uploader,
                dashscope_temp_url_resolver=lambda local_path: self._create_dashscope_temp_url(
                    local_path, name
                ),
            )
            resolved_img = resolved.value
            headers.update(resolved.headers)

        resolved_audio = None
        if audio_url:
            resolved = resolve_media_input(
                audio_url,
                model_name=name,
                backend="dashscope",
                modality="audio",
                uploader=uploader,
                dashscope_temp_url_resolver=lambda local_path: self._create_dashscope_temp_url(
                    local_path, name
                ),
            )
            resolved_audio = resolved.value
            headers.update(resolved.headers)

        resolved_refs: list[str] | None = None
        refs = reference_video_urls if reference_video_urls is not None else ref_video_urls
        if refs:
            resolved_refs = []
            for ref in refs:
                resolved = resolve_media_input(
                    ref,
                    model_name=name,
                    backend="dashscope",
                    modality="reference_video",
                    uploader=uploader,
                    dashscope_temp_url_resolver=lambda local_path: self._create_dashscope_temp_url(
                        local_path, name
                    ),
                )
                resolved_refs.append(resolved.value)
                headers.update(resolved.headers)

        if name.startswith("wan2.6-"):
            http_kwargs = {
                "prompt": prompt,
                "img_url": resolved_img,
                "model_name": name,
                "resolution": resolution,
                "duration": duration,
                "prompt_extend": prompt_extend,
                "negative_prompt": negative_prompt,
                "audio_url": resolved_audio,
                "watermark": watermark,
                "seed": seed,
                "shot_type": shot_type,
                "extra_headers": headers,
            }
            if resolved_refs is not None:
                http_kwargs["reference_video_urls"] = resolved_refs
            video_url = self._generate_wan_i2v_http(**http_kwargs)
        else:
            video_url = self._generate_sdk(
                prompt,
                name,
                img_url=resolved_img,
                size=size,
                duration=duration,
                prompt_extend=prompt_extend,
                negative_prompt=negative_prompt,
                audio_url=resolved_audio,
                watermark=watermark,
                seed=seed,
                camera_motion=camera_motion,
                subject_motion=subject_motion,
            )

        self._download_video(video_url, output_path)
        return output_path, time.time() - started

    def _generate_wan_i2v_http(
        self,
        *,
        prompt: str,
        img_url: str | None,
        model_name: str = "wan2.6-i2v",
        resolution: str = "720P",
        duration: int = 5,
        prompt_extend: bool = True,
        negative_prompt: str | None = None,
        audio_url: str | None = None,
        watermark: bool = False,
        seed: int | None = None,
        shot_type: str = "single",
        reference_video_urls: list[str] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        input_payload: dict[str, Any] = {"prompt": prompt}
        if img_url:
            input_payload["img_url"] = img_url
        if audio_url:
            input_payload["audio_url"] = audio_url
        if reference_video_urls:
            input_payload["reference_video_urls"] = reference_video_urls
        parameters = {
            "resolution": resolution,
            "duration": duration,
            "prompt_extend": prompt_extend,
            "watermark": watermark,
            "shot_type": shot_type,
        }
        if negative_prompt is not None:
            parameters["negative_prompt"] = negative_prompt
        if seed is not None:
            parameters["seed"] = seed

        headers = {"Authorization": f"Bearer {self._api_key()}"}
        headers.update(extra_headers or {})
        response = requests.post(
            f"{self.base_url.rstrip('/')}/api/v1/services/aigc/video-synthesis/video-synthesis",
            headers=headers,
            json={
                "model": model_name,
                "input": input_payload,
                "parameters": parameters,
            },
            timeout=60,
        )
        payload = response.json()
        task_id = payload.get("output", {}).get("task_id") or payload.get("task_id")
        if not task_id:
            raise RuntimeError(f"Wanx response missing task id: {payload}")
        return self._poll_video_task(task_id, headers)

    def _poll_video_task(self, task_id: str, headers: dict[str, str]) -> str:
        for _ in range(120):
            response = requests.get(
                f"{self.base_url.rstrip('/')}/api/v1/tasks/{task_id}",
                headers=headers,
                timeout=60,
            )
            payload = response.json()
            output = payload.get("output", payload)
            status = output.get("task_status") or output.get("status")
            if status in {"SUCCEEDED", "succeed", "success"}:
                video_url = output.get("video_url") or output.get("url")
                if video_url:
                    return video_url
            if status in {"FAILED", "failed", "error"}:
                raise RuntimeError(f"Wanx task failed: {payload}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Wanx task timed out: {task_id}")

    def _generate_sdk(
        self,
        prompt,
        model_name,
        img_url=None,
        size="1280*720",
        duration=5,
        prompt_extend=True,
        negative_prompt=None,
        audio_url=None,
        watermark=False,
        seed=None,
        camera_motion=None,
        subject_motion=None,
    ) -> str:
        return self._generate_wan_i2v_http(
            prompt=prompt,
            img_url=img_url,
            model_name=model_name,
            resolution=size,
            duration=duration,
            prompt_extend=prompt_extend,
            negative_prompt=negative_prompt,
            audio_url=audio_url,
            watermark=watermark,
            seed=seed,
        )

    def _create_dashscope_temp_url(self, local_path: str, model_name: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key()}"}
        policy = requests.get(
            f"{self.base_url.rstrip('/')}/api/v1/uploads",
            params={"action": "getPolicy", "model": model_name},
            headers=headers,
            timeout=60,
        ).json()["output"]
        filename = Path(local_path).name
        upload_dir = policy["upload_dir"].strip("/")
        object_key = f"{upload_dir}/{filename}"
        with Path(local_path).open("rb") as file_obj:
            requests.post(
                policy["upload_host"],
                data={
                    "key": object_key,
                    "policy": policy["policy"],
                    "signature": policy["signature"],
                    "OSSAccessKeyId": policy["oss_access_key_id"],
                },
                files={"file": (filename, file_obj)},
                timeout=120,
            )
        return f"oss://{object_key}"

    @staticmethod
    def _download_video(video_url: str, output_path: str) -> None:
        response = requests.get(video_url, timeout=120)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(getattr(response, "content", b""))

    @staticmethod
    def _api_key() -> str:
        return os.getenv("DASHSCOPE_API_KEY", "")
