from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from src.apps.comic_gen.llm import DEFAULT_PROMPTS
from src.apps.comic_gen.models import (
    Character,
    Prop,
    Scene,
    Script,
    Series,
    VideoTask,
)
from src.utils.media_refs import classify_media_ref, resolve_local_media_path
from src.utils.provider_registry import get_default_provider_registry


class ScriptProcessor:
    pass


class AssetGenerator:
    pass


class StoryboardGenerator:
    pass


class VideoGenerator:
    def __init__(self, model=None) -> None:
        if model is None:
            from src.models.wanx import WanxModel

            model = WanxModel({"params": {}})
        self.model = model


class AudioGenerator:
    pass


class ExportManager:
    pass


class ComicGenPipeline:
    def __init__(self) -> None:
        self.data_file = "data/projects.json"
        self.series_data_file = "data/series.json"
        self.scripts: dict[str, Script] = {}
        self.series_store: dict[str, Series] = {}
        self.script_processor = ScriptProcessor()
        self.asset_generator = AssetGenerator()
        self.storyboard_generator = StoryboardGenerator()
        self.video_generator = VideoGenerator()
        self.audio_generator = AudioGenerator()
        self.export_manager = ExportManager()
        self._kling_model = None
        self._vidu_model = None

    def _save_data(self) -> None:
        return None

    def get_script(self, script_id: str) -> Script | None:
        return self.scripts.get(script_id)

    def create_series(self, title: str, description: str = "") -> Series:
        now = time.time()
        series = Series(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self.series_store[series.id] = series
        self._save_data()
        return series

    def get_series(self, series_id: str) -> Series | None:
        return self.series_store.get(series_id)

    def list_series(self) -> list[Series]:
        return list(self.series_store.values())

    def update_series(self, series_id: str, updates: dict[str, Any]) -> Series:
        series = self._require_series(series_id)
        protected = {"id", "created_at", "episode_ids"}
        for key, value in updates.items():
            if key in protected or not hasattr(series, key):
                continue
            setattr(series, key, value)
        series.updated_at = time.time()
        self._save_data()
        return series

    def delete_series(self, series_id: str) -> None:
        series = self._require_series(series_id)
        for episode_id in list(series.episode_ids):
            episode = self.scripts.get(episode_id)
            if episode:
                episode.series_id = None
                episode.episode_number = None
                episode.updated_at = time.time()
        del self.series_store[series_id]
        self._save_data()

    def add_episode_to_series(
        self,
        series_id: str,
        episode_id: str,
        episode_number: int | None = None,
    ) -> Series:
        series = self._require_series(series_id)
        episode = self._require_script(episode_id)
        if episode.series_id and episode.series_id != series_id:
            old_series = self.series_store.get(episode.series_id)
            if old_series and episode_id in old_series.episode_ids:
                old_series.episode_ids.remove(episode_id)
                old_series.updated_at = time.time()
        if episode_id not in series.episode_ids:
            series.episode_ids.append(episode_id)
        episode.series_id = series_id
        episode.episode_number = episode_number or len(series.episode_ids)
        episode.updated_at = time.time()
        series.updated_at = time.time()
        self._save_data()
        return series

    def remove_episode_from_series(self, series_id: str, episode_id: str) -> Series:
        series = self._require_series(series_id)
        if episode_id in series.episode_ids:
            series.episode_ids.remove(episode_id)
        episode = self.scripts.get(episode_id)
        if episode:
            episode.series_id = None
            episode.episode_number = None
            episode.updated_at = time.time()
        series.updated_at = time.time()
        self._save_data()
        return series

    def get_series_episodes(self, series_id: str) -> list[Script]:
        series = self._require_series(series_id)
        episodes = [self.scripts[eid] for eid in series.episode_ids if eid in self.scripts]
        return sorted(
            episodes,
            key=lambda episode: (
                episode.episode_number
                if episode.episode_number is not None
                else 10**9,
                episode.created_at,
            ),
        )

    def resolve_episode_assets(
        self,
        episode: Script,
        series: Series | None = None,
    ) -> dict[str, list[Character] | list[Scene] | list[Prop]]:
        series = series or (
            self.series_store.get(episode.series_id) if episode.series_id else None
        )
        if series is None:
            return {
                "characters": list(episode.characters),
                "scenes": list(episode.scenes),
                "props": list(episode.props),
            }
        return {
            "characters": self._merge_assets(series.characters, episode.characters),
            "scenes": self._merge_assets(series.scenes, episode.scenes),
            "props": self._merge_assets(series.props, episode.props),
        }

    def get_effective_prompt(
        self,
        prompt_type: str,
        episode: Script,
        series: Series | None = None,
    ) -> str:
        if prompt_type not in DEFAULT_PROMPTS:
            raise ValueError(f"Invalid prompt_type: {prompt_type}")
        episode_value = getattr(episode.prompt_config, prompt_type, "")
        if isinstance(episode_value, str) and episode_value.strip():
            return episode_value
        series = series or (
            self.series_store.get(episode.series_id) if episode.series_id else None
        )
        if series:
            series_value = getattr(series.prompt_config, prompt_type, "")
            if isinstance(series_value, str) and series_value.strip():
                return series_value
        return DEFAULT_PROMPTS[prompt_type]

    def import_assets_from_series(
        self,
        target_series_id: str,
        source_series_id: str,
        asset_ids: list[str],
    ) -> tuple[Series, list[str], list[str]]:
        target = self._require_series(target_series_id)
        source = self._require_series(source_series_id)
        imported: list[str] = []
        skipped: list[str] = []
        source_groups = [
            ("characters", source.characters),
            ("scenes", source.scenes),
            ("props", source.props),
        ]
        for asset_id in asset_ids:
            found = False
            for attr, assets in source_groups:
                asset = next((item for item in assets if item.id == asset_id), None)
                if asset is None:
                    continue
                clone = asset.model_copy(deep=True, update={"id": str(uuid.uuid4())})
                getattr(target, attr).append(clone)
                imported.append(asset_id)
                found = True
                break
            if not found:
                skipped.append(asset_id)
        if imported:
            target.updated_at = time.time()
            self._save_data()
        return target, imported, skipped

    def _split_text_by_markers(
        self,
        text: str,
        episodes_data: list[dict[str, str]],
    ) -> list[str]:
        count = len(episodes_data)
        if count == 0:
            return []
        if count == 1:
            return [text]
        if not any(
            item.get("start_marker", "") or item.get("end_marker", "")
            for item in episodes_data
        ):
            return self._equal_split(text, count)

        chunks: list[str] = []
        cursor = 0
        for item in episodes_data:
            start_marker = item.get("start_marker", "")
            end_marker = item.get("end_marker", "")
            start_idx = cursor
            if start_marker:
                start_idx = text.find(start_marker, cursor)
                if start_idx < 0:
                    return self._equal_split(text, count)
            search_from = start_idx + len(start_marker)
            if end_marker:
                end_idx = text.find(end_marker, search_from)
                if end_idx < 0:
                    return self._equal_split(text, count)
                end_idx += len(end_marker)
            else:
                end_idx = len(text)
            if end_idx < start_idx:
                return self._equal_split(text, count)
            chunks.append(text[start_idx:end_idx])
            cursor = end_idx
        return chunks if len(chunks) == count else self._equal_split(text, count)

    def create_video_task(
        self,
        script_id: str,
        image_url: str,
        prompt: str,
        **kwargs: Any,
    ) -> tuple[Script, str]:
        script = self._require_script(script_id)
        task_id = str(uuid.uuid4())
        stable_image_url = self._snapshot_video_input(image_url, task_id)
        task = VideoTask(
            id=task_id,
            project_id=script_id,
            image_url=stable_image_url,
            prompt=prompt,
            **kwargs,
        )
        script.video_tasks.append(task)
        script.updated_at = time.time()
        self._save_data()
        return script, task.id

    def process_video_task(self, script_id: str, task_id: str) -> VideoTask:
        script = self._require_script(script_id)
        task = next((item for item in script.video_tasks if item.id == task_id), None)
        if task is None:
            raise ValueError("Video task not found")
        task.status = "processing"
        task.updated_at = time.time()
        output_rel = f"video/video_{task.id}.mp4"
        output_path = str(Path("output") / output_rel)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        image_input = self._prepare_video_image_input(task.image_url)
        model_name = task.model or "wan2.6-i2v"
        backend = self._resolve_backend(model_name)

        if backend == "vendor" and model_name.lower().startswith("kling"):
            result = self._get_kling_model().generate(
                prompt=task.prompt,
                output_path=output_path,
                img_path=image_input,
                model=model_name,
                duration=task.duration,
                seed=task.seed,
                mode=task.mode,
                sound=task.sound,
                cfg_scale=task.cfg_scale,
                negative_prompt=task.negative_prompt,
            )
        elif backend == "vendor" and model_name.lower().startswith("vidu"):
            result = self._get_vidu_model().generate(
                prompt=task.prompt,
                output_path=output_path,
                img_path=image_input,
                model=model_name,
                duration=task.duration,
                seed=task.seed,
                audio=task.vidu_audio,
                movement_amplitude=task.movement_amplitude,
                negative_prompt=task.negative_prompt,
            )
        else:
            result = self.video_generator.model.generate(
                prompt=task.prompt,
                output_path=output_path,
                img_path=image_input,
                model=model_name,
                model_name=model_name,
                duration=task.duration,
                seed=task.seed,
                resolution=task.resolution,
                prompt_extend=task.prompt_extend,
                negative_prompt=task.negative_prompt,
                shot_type=task.shot_type,
                mode=task.mode,
                sound=task.sound,
                cfg_scale=task.cfg_scale,
                audio=task.vidu_audio,
                movement_amplitude=task.movement_amplitude,
            )

        if isinstance(result, tuple) and result:
            output_path = result[0]
        task.video_url = output_rel
        task.status = "completed"
        task.updated_at = time.time()
        script.updated_at = time.time()
        self._save_data()
        return task

    def _snapshot_video_input(self, image_url: str, task_id: str) -> str:
        if classify_media_ref(image_url) != "local_path":
            return image_url
        source = Path(resolve_local_media_path(image_url))
        if not source.exists():
            return image_url
        target_dir = Path("output") / "video_inputs"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_name = f"{task_id}_{source.name}"
        target = target_dir / target_name
        shutil.copy2(source, target)
        return f"video_inputs/{target_name}"

    def _prepare_video_image_input(self, image_url: str) -> str:
        kind = classify_media_ref(image_url)
        if kind == "remote_url":
            downloader = getattr(self, "_download_temp_image", None)
            return downloader(image_url) if callable(downloader) else image_url
        if kind == "local_path":
            return resolve_local_media_path(image_url)
        return image_url

    def _download_temp_image(self, image_url: str) -> str:
        return image_url

    def _get_kling_model(self):
        if self._kling_model is None:
            from src.models.kling import KlingModel

            self._kling_model = KlingModel(
                {
                    "access_key": os.getenv("KLING_ACCESS_KEY", ""),
                    "secret_key": os.getenv("KLING_SECRET_KEY", ""),
                }
            )
        return self._kling_model

    def _get_vidu_model(self):
        if self._vidu_model is None:
            from src.models.vidu import ViduModel

            self._vidu_model = ViduModel({"api_key": os.getenv("VIDU_API_KEY", "")})
        return self._vidu_model

    def _resolve_backend(self, model_name: str) -> str:
        try:
            return get_default_provider_registry().resolve_backend(model_name)
        except KeyError:
            return "dashscope"

    def _require_series(self, series_id: str) -> Series:
        series = self.series_store.get(series_id)
        if not series:
            raise ValueError("Series not found")
        return series

    def _require_script(self, script_id: str) -> Script:
        script = self.scripts.get(script_id)
        if not script:
            raise ValueError("Script not found")
        return script

    @staticmethod
    def _merge_assets(series_assets: list[Any], episode_assets: list[Any]) -> list[Any]:
        episode_ids = {asset.id for asset in episode_assets}
        merged = list(episode_assets)
        merged.extend(asset for asset in series_assets if asset.id not in episode_ids)
        return merged

    @staticmethod
    def _equal_split(text: str, count: int) -> list[str]:
        if count <= 0:
            return []
        base = len(text) // count
        remainder = len(text) % count
        chunks: list[str] = []
        cursor = 0
        for index in range(count):
            size = base + (1 if index < remainder else 0)
            chunks.append(text[cursor : cursor + size])
            cursor += size
        return chunks
