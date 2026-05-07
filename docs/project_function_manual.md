# LuminAI Project Function Manual

> This document explains what this project is, what it can do, and how to work
> on it during future sessions.

---

## 1. What This Project Is

LuminAI is an industrial AI manju / AI film engine foundation.

It is not a toy video generator and not a prompt-splicing demo. The target is a
repeatable content production system for cinematic short dramas, manju, and AI
film workflows.

The platform direction is:

```text
Jellyfish as AI Studio OS / Workflow Core
LuminAI as Film Core / Continuity / QA / Retry / Runtime abstraction
```

Jellyfish provides the studio workbench. LuminAI provides the systems that make
production controllable across long stories, many shots, and many episodes.

---

## 2. What It Can Do Now

Current implemented capabilities:

- model series, episodes, characters, scenes, props, storyboards, and video tasks
- inherit assets and prompt config from series to episodes
- resolve local media references and provider-specific media input modes
- route Wan/DashScope, Kling, Vidu, and future provider families through a registry
- represent film entities with ECS-inspired components
- build graph-driven workflows
- record shot continuity state
- compile provider prompts from structured director data and continuity state
- define runtime render requests and results
- evaluate QA metrics into structured issues
- convert QA failures into retry decisions
- plan industrial batch workflows across episodes
- map Jellyfish-style Project/Chapter/Shot/Asset/Task concepts into Film Core

The latest bridge code is:

- `src/film_engine/platform.py`
- `tests/test_jellyfish_platform_bridge.py`

---

## 3. What It Should Do Next

The next product layers should be added in this order:

1. Connect an actual Jellyfish fork or API client to `StudioPlatformBridge`.
2. Feed Jellyfish shot readiness into LuminAI Film State.
3. Compile Director DSL and continuity into provider-specific render requests.
4. Attach huobao-drama-style FFmpeg, subtitle, TTS, and stitching as Runtime Layer services.
5. Add character/scene bible contracts for repeatable identity and location continuity.
6. Run QA after each generated shot and create retry decisions automatically.
7. Write approved outputs back into Jellyfish media and shot records.
8. Expose batch production controls in the studio UI.

---

## 4. How The Core Workflow Works

```text
Script / Novel
    ↓
Jellyfish Project + Chapter
    ↓
Shot Preparation + Asset Confirmation
    ↓
LuminAI Platform Bridge
    ↓
Film State + Director DSL + Shot Graph
    ↓
Prompt Compiler
    ↓
Runtime Adapter
    ↓
Video / Image / TTS / FFmpeg Runtime
    ↓
QA Engine
    ↓
Retry Engine
    ↓
Final Export + Reusable Media
```

The default bridge workflow is:

```text
script_breakdown
→ shot_preparation
→ asset_consistency
→ film_state
→ prompt_compiler
→ runtime_adapter
→ qa_engine
→ retry_engine
→ final_export
```

---

## 5. How To Use The Bridge In Code

```python
from src.film_engine import (
    CompiledPrompt,
    StudioAsset,
    StudioPlatformBridge,
    StudioShot,
)

bridge = StudioPlatformBridge()

shot = StudioShot(
    id="shot_001",
    project_id="project_001",
    chapter_id="chapter_001",
    index=1,
    scene_id="scene_001",
    character_ids=["char_001"],
    camera={"framing": "medium_closeup", "movement": "dolly_in"},
)

assets = [
    StudioAsset(
        id="char_001",
        kind="character",
        name="Ari",
        reference_media=["ref/ari_front.png"],
    ),
    StudioAsset(
        id="scene_001",
        kind="scene",
        name="Neon Alley",
        reference_media=["ref/alley.png"],
        metadata={"lighting": "neon_rain"},
    ),
]

continuity = bridge.shot_to_continuity(shot, assets=assets)
director_dsl = bridge.shot_to_director_dsl(shot)

compiled = CompiledPrompt(
    provider="kling",
    text="shot=shot_001; scene=scene_001; movement=dolly_in",
    references=continuity.reference_media,
    parameters=director_dsl,
)

request = bridge.compile_render_request(
    shot,
    compiled,
    model="kling-v1",
    output_path="output/shot_001.mp4",
)
```

The bridge keeps runtime details at the adapter boundary. It does not let
Jellyfish platform state leak into provider-specific code.

---

## 6. Directory Guide

```text
src/apps/comic_gen/      Current series, episode, asset, prompt, and task pipeline
src/film_engine/         Reusable Film Core systems
src/film_engine/platform.py
                         Jellyfish-style platform bridge
src/models/              Runtime model adapters
src/utils/               Media resolution and provider registry utilities
docs/                    Architecture, plans, workflows, and session index
samples/                 Reusable asset and workflow examples
tests/                   Python and contract tests
skills/                  Skill specs for engine modules
freeze/                  Frozen contracts
benchmarks/              Benchmark expectations
```

---

## 7. Verification

Run targeted bridge tests:

```bash
python3 -m pytest -q -s tests/test_jellyfish_platform_bridge.py
```

Run the full suite:

```bash
python3 -m pytest -q -s
```

The `-s` flag is the repository's known stable mode for this environment.

---

## 8. Session Task Index Rule

Every session must update:

```text
docs/task_progress_index.md
```

Required fields:

- current task
- node name
- node status
- evidence file or command
- verification result
- commit / push result when requested

Use the index as the handoff point after context compaction or future sessions.
