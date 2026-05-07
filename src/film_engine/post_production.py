from __future__ import annotations

from dataclasses import dataclass, field

from src.film_engine.platform import StudioShot
from src.film_engine.runtime import RenderResult


@dataclass
class DialogueCue:
    shot_id: str
    text: str
    speaker_id: str | None = None
    speaker_name: str | None = None
    voice_id: str | None = None
    start_seconds: float = 0.5
    end_seconds: float | None = None
    mode: str = "dialogue"


@dataclass
class SubtitleCue:
    index: int
    text: str
    start_seconds: float
    end_seconds: float
    shot_id: str | None = None


@dataclass
class PostProductionClip:
    shot_id: str
    video_path: str
    duration: float
    dialogue: list[DialogueCue] = field(default_factory=list)
    audio_path: str | None = None
    subtitle_path: str | None = None
    composed_output_path: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class PostProductionStep:
    id: str
    system: str
    inputs: dict[str, object] = field(default_factory=dict)
    outputs: dict[str, object] = field(default_factory=dict)
    parameters: dict[str, object] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class PostProductionPlan:
    project_id: str
    chapter_id: str
    clips: list[PostProductionClip]
    steps: list[PostProductionStep]
    output_path: str
    metadata: dict[str, object] = field(default_factory=dict)

    def steps_by_system(self, system: str) -> list[PostProductionStep]:
        return [step for step in self.steps if step.system == system]


class DialogueNormalizer:
    IGNORE_SPEAKERS = {
        "ambient",
        "background",
        "bgm",
        "environment",
        "sfx",
        "sound effect",
    }
    IGNORE_TEXTS = {
        "",
        "none",
        "null",
        "n/a",
        "na",
        "no dialogue",
        "no voiceover",
        "ambient",
        "bgm",
        "sfx",
    }

    def parse(self, *, shot_id: str, line: str, duration: float) -> DialogueCue | None:
        raw = line.strip()
        if not raw:
            return None
        speaker_name: str | None = None
        text = raw
        for delimiter in (":", "："):
            if delimiter in raw:
                speaker_name, text = raw.split(delimiter, 1)
                speaker_name = speaker_name.strip() or None
                text = text.strip()
                break
        if self._ignorable(speaker_name, text):
            return None
        return DialogueCue(
            shot_id=shot_id,
            text=text,
            speaker_name=speaker_name,
            end_seconds=max(1.0, duration - 0.5),
        )

    def _ignorable(self, speaker_name: str | None, text: str) -> bool:
        speaker = (speaker_name or "").strip().lower()
        clean_text = text.strip().lower()
        return speaker in self.IGNORE_SPEAKERS or clean_text in self.IGNORE_TEXTS


class SubtitleCompiler:
    def cues_for_clip(self, clip: PostProductionClip) -> list[SubtitleCue]:
        cues = []
        for index, dialogue in enumerate(clip.dialogue, start=1):
            start = dialogue.start_seconds
            end = dialogue.end_seconds or max(start + 1.0, clip.duration - 0.5)
            cues.append(
                SubtitleCue(
                    index=index,
                    text=dialogue.text,
                    start_seconds=start,
                    end_seconds=end,
                    shot_id=clip.shot_id,
                )
            )
        return cues

    def to_srt(self, cues: list[SubtitleCue]) -> str:
        blocks = []
        for cue in cues:
            blocks.append(
                "\n".join(
                    [
                        str(cue.index),
                        f"{self._timestamp(cue.start_seconds)} --> {self._timestamp(cue.end_seconds)}",
                        cue.text,
                    ]
                )
            )
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    def _timestamp(self, seconds: float) -> str:
        milliseconds = int(round(max(0.0, seconds) * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class PostProductionPlanner:
    def __init__(self, *, dialogue_normalizer: DialogueNormalizer | None = None) -> None:
        self.dialogue_normalizer = dialogue_normalizer or DialogueNormalizer()

    def clips_from_shots(
        self,
        shots: list[StudioShot],
        render_results: list[RenderResult],
    ) -> list[PostProductionClip]:
        result_by_shot = {result.shot_id: result for result in render_results}
        clips = []
        for shot in sorted(shots, key=lambda item: item.index):
            result = result_by_shot.get(shot.id)
            if result is None:
                continue
            duration = float(shot.duration or result.metadata.get("duration") or 0)
            dialogue = [
                cue
                for line in shot.dialogue
                if (
                    cue := self.dialogue_normalizer.parse(
                        shot_id=shot.id,
                        line=line,
                        duration=duration or 3.0,
                    )
                )
            ]
            clips.append(
                PostProductionClip(
                    shot_id=shot.id,
                    video_path=result.output_path,
                    duration=duration or 3.0,
                    dialogue=dialogue,
                    metadata={"runtime": result.runtime, **result.metadata},
                )
            )
        return clips

    def plan_chapter(
        self,
        *,
        project_id: str,
        chapter_id: str,
        clips: list[PostProductionClip],
        output_path: str,
        work_dir: str = "output/post",
        tts_provider: str = "tts_runtime",
        burn_subtitles: bool = True,
        export_preset: str = "h264_aac_faststart",
    ) -> PostProductionPlan:
        if not clips:
            raise ValueError("Post-production requires at least one clip")

        steps: list[PostProductionStep] = []
        compose_step_ids: list[str] = []
        for index, clip in enumerate(clips, start=1):
            if not clip.video_path:
                raise ValueError(f"Clip {clip.shot_id} is missing video_path")
            base_id = f"{chapter_id}:{clip.shot_id}"
            dependencies: list[str] = []
            audio_path = clip.audio_path
            subtitle_path = clip.subtitle_path

            if clip.dialogue and not audio_path:
                step_id = f"{base_id}:tts"
                audio_path = f"{work_dir}/{clip.shot_id}.mp3"
                steps.append(
                    PostProductionStep(
                        id=step_id,
                        system="tts",
                        inputs={
                            "dialogue": [cue.text for cue in clip.dialogue],
                            "speakers": [cue.speaker_name for cue in clip.dialogue],
                        },
                        outputs={"audio_path": audio_path},
                        parameters={"provider": tts_provider},
                    )
                )
                dependencies.append(step_id)

            if clip.dialogue and burn_subtitles and not subtitle_path:
                step_id = f"{base_id}:subtitle"
                subtitle_path = f"{work_dir}/{clip.shot_id}.srt"
                steps.append(
                    PostProductionStep(
                        id=step_id,
                        system="subtitle",
                        inputs={"dialogue": [cue.text for cue in clip.dialogue]},
                        outputs={"subtitle_path": subtitle_path},
                        parameters={"format": "srt"},
                    )
                )
                dependencies.append(step_id)

            composed_path = clip.composed_output_path or f"{work_dir}/{index:04d}_{clip.shot_id}.mp4"
            compose_id = f"{base_id}:compose"
            steps.append(
                PostProductionStep(
                    id=compose_id,
                    system="ffmpeg_compose",
                    inputs={
                        "video_path": clip.video_path,
                        "audio_path": audio_path,
                        "subtitle_path": subtitle_path,
                    },
                    outputs={"video_path": composed_path},
                    parameters={
                        "video_codec": "libx264",
                        "audio_codec": "aac",
                        "burn_subtitles": bool(subtitle_path and burn_subtitles),
                    },
                    depends_on=dependencies,
                )
            )
            compose_step_ids.append(compose_id)

        concat_id = f"{chapter_id}:concat"
        steps.append(
            PostProductionStep(
                id=concat_id,
                system="ffmpeg_concat",
                inputs={
                    "clip_paths": [
                        step.outputs["video_path"]
                        for step in steps
                        if step.id in compose_step_ids
                    ]
                },
                outputs={"video_path": f"{work_dir}/{chapter_id}_merged.mp4"},
                parameters={"safe": False, "normalize_audio": True},
                depends_on=compose_step_ids,
            )
        )
        steps.append(
            PostProductionStep(
                id=f"{chapter_id}:export",
                system="export",
                inputs={"video_path": f"{work_dir}/{chapter_id}_merged.mp4"},
                outputs={"video_path": output_path},
                parameters={"preset": export_preset},
                depends_on=[concat_id],
            )
        )
        return PostProductionPlan(
            project_id=project_id,
            chapter_id=chapter_id,
            clips=list(clips),
            steps=steps,
            output_path=output_path,
            metadata={
                "mode": "huobao_style_post_production",
                "clip_count": len(clips),
                "burn_subtitles": burn_subtitles,
            },
        )


class FFmpegCommandCompiler:
    def compile(self, step: PostProductionStep) -> list[str]:
        if step.system == "ffmpeg_compose":
            return self._compose(step)
        if step.system == "ffmpeg_concat":
            return self._concat(step)
        if step.system == "export":
            return self._export(step)
        raise ValueError(f"Unsupported FFmpeg command step: {step.system}")

    def _compose(self, step: PostProductionStep) -> list[str]:
        video_path = str(step.inputs["video_path"])
        audio_path = step.inputs.get("audio_path")
        subtitle_path = step.inputs.get("subtitle_path")
        output_path = str(step.outputs["video_path"])
        args = ["ffmpeg", "-y", "-i", video_path]
        if audio_path:
            args.extend(["-i", str(audio_path)])
        if subtitle_path and step.parameters.get("burn_subtitles"):
            args.extend(["-vf", f"subtitles={subtitle_path}"])
        args.extend(["-c:v", str(step.parameters.get("video_codec", "libx264"))])
        if audio_path:
            args.extend(["-map", "0:v", "-map", "1:a", "-c:a", str(step.parameters.get("audio_codec", "aac")), "-shortest"])
        else:
            args.append("-an")
        args.append(output_path)
        return args

    def _concat(self, step: PostProductionStep) -> list[str]:
        list_path = str(step.inputs.get("list_path", "concat.txt"))
        output_path = str(step.outputs["video_path"])
        return [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0" if step.parameters.get("safe") is False else "1",
            "-i",
            list_path,
            "-fflags",
            "+genpts",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            output_path,
        ]

    def _export(self, step: PostProductionStep) -> list[str]:
        input_path = str(step.inputs["video_path"])
        output_path = str(step.outputs["video_path"])
        return [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            output_path,
        ]
