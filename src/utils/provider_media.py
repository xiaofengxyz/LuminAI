from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from src.utils.media_refs import classify_media_ref, resolve_local_media_path

RESOLVE_HEADER_DASHSCOPE_OSS_RESOURCE = "X-DashScope-OssResourceResolve"


@dataclass(frozen=True)
class ResolvedMediaInput:
    value: str
    headers: dict[str, str] = field(default_factory=dict)


def _read_base64(local_path: str) -> str:
    return base64.b64encode(Path(local_path).read_bytes()).decode("ascii")


def _read_data_uri(local_path: str) -> str:
    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    return f"data:{mime_type};base64,{_read_base64(local_path)}"


def _upload_and_sign(ref: str, local_path: str | None, uploader) -> str | None:
    if uploader is None or not getattr(uploader, "is_configured", False):
        return None
    if local_path:
        object_key = uploader.upload_file(
            local_path,
            sub_path="temp/provider_media",
        )
    else:
        object_key = ref
    if not object_key:
        return None
    return uploader.sign_url_for_api(object_key)


def _is_wan_i2v_like(model_name: str) -> bool:
    lowered = model_name.lower()
    return lowered.startswith("wan2.6-") and any(token in lowered for token in ("i2v", "r2v"))


def resolve_media_input(
    ref: str,
    *,
    model_name: str,
    backend: str,
    modality: str,
    uploader=None,
    project_root: str | None = None,
    dashscope_temp_url_resolver: Callable[[str], str] | None = None,
) -> ResolvedMediaInput:
    kind = classify_media_ref(ref)
    if kind in {"remote_url", "data_uri"}:
        return ResolvedMediaInput(ref, {})

    local_path: str | None = None
    if kind == "local_path":
        local_path = resolve_local_media_path(ref, project_root=project_root)

    signed_url = _upload_and_sign(ref, local_path, uploader)
    if signed_url:
        return ResolvedMediaInput(signed_url, {})

    if kind == "object_key":
        return ResolvedMediaInput(ref, {})

    if not local_path:
        return ResolvedMediaInput(ref, {})

    if backend == "dashscope":
        if modality == "image" and not _is_wan_i2v_like(model_name):
            return ResolvedMediaInput(_read_data_uri(local_path), {})
        if dashscope_temp_url_resolver is None:
            raise ValueError(
                f"{model_name} {modality} local media requires OSS or a dashscope_temp_url_resolver"
            )
        return ResolvedMediaInput(
            dashscope_temp_url_resolver(local_path),
            {RESOLVE_HEADER_DASHSCOPE_OSS_RESOURCE: "enable"},
        )

    if backend == "vendor" and model_name.lower().startswith("kling") and modality == "image":
        return ResolvedMediaInput(_read_base64(local_path), {})

    raise ValueError(
        f"{model_name} {modality} local media requires a URL-compatible media source"
    )


def resolve_media_inputs(
    refs: Iterable[str],
    *,
    model_name: str,
    backend: str,
    modality: str,
    uploader=None,
    project_root: str | None = None,
    dashscope_temp_url_resolver: Callable[[str], str] | None = None,
) -> list[ResolvedMediaInput]:
    return [
        resolve_media_input(
            ref,
            model_name=model_name,
            backend=backend,
            modality=modality,
            uploader=uploader,
            project_root=project_root,
            dashscope_temp_url_resolver=dashscope_temp_url_resolver,
        )
        for ref in list(refs)
    ]
