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
- map Jellyfish OpenAPI/ORM-shaped records into bridge contracts
- prepare director consistency from character and scene bibles
- plan TTS, subtitle, FFmpeg compose, concat, and export steps
- build closed-loop chapter plans with render requests, QA, retry, and optional post-production
- track Jellyfish as a real upstream studio base under `vendor/jellyfish`
- inspect Jellyfish base status, run commands, ports, and missing files
- run a dependency-light HTTP/CLI smoke service that exposes health, a
  closed-loop demo production plan, Studio Dashboard UI, and status APIs

The latest bridge code is:

- `src/film_engine/platform.py`
- `src/film_engine/jellyfish.py`
- `src/film_engine/jellyfish_base.py`
- `src/film_engine/director.py`
- `src/film_engine/post_production.py`
- `src/film_engine/production.py`
- `src/film_engine/studio.py`
- `src/film_engine/demo.py`
- `src/film_engine/server.py`
- `tests/test_jellyfish_platform_bridge.py`
- `tests/test_jellyfish_base_status.py`
- `tests/test_luminai_runtime_entrypoint.py`

---

## 3. What It Should Do Next

The next product layers should be added in this order:

1. Bind `JellyfishRecordMapper` to the tracked Jellyfish fork/API client.
2. Write approved outputs and retry outcomes back into Jellyfish media, task,
   and shot records.
3. Expose QA, retry, post-production, and batch production controls in the
   studio UI.
4. Add provider-specific workers that execute the closed-loop plans while
   keeping Film Core runtime-neutral.

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
src/film_engine/jellyfish_base.py
                         Jellyfish upstream checkout and run-status inspector
src/film_engine/studio.py
                         Local Studio Dashboard payload and renderer
vendor/jellyfish/        Upstream Jellyfish Studio OS base submodule
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

Run the runtime entrypoint tests:

```bash
python3 -m pytest -q -s tests/test_luminai_runtime_entrypoint.py
```

Run the Jellyfish base and stage-evidence tests:

```bash
python3 -m pytest -q -s tests/test_jellyfish_base_status.py
```

Run the full suite:

```bash
python3 -m pytest -q -s
```

The `-s` flag is the repository's known stable mode for this environment.

---

## 8. Run The Project

Start the local LuminAI runtime server and Studio Dashboard:

```bash
python3 -m src.film_engine.server --host 127.0.0.1 --port 8765
```

Open the UI:

```text
http://127.0.0.1:8765/
```

Smoke endpoints:

```text
GET /health
GET /api/studio/status
GET /api/jellyfish/base-status
GET /demo/closed-loop-plan
```

The demo endpoint returns a full closed-loop chapter plan: workflow order,
compiled render requests, QA failures, retry requests, and post-production
steps.

Inspect the Jellyfish base:

```bash
python3 -m src.film_engine.jellyfish_base
```

Validate the Jellyfish Docker Compose config:

```bash
cd vendor/jellyfish
docker compose --env-file deploy/compose/.env.example -f deploy/compose/docker-compose.yml config -q
```

---

## 9. Session Task Index Rule

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

---

## 10. Jellyfish-Native Film Core

The industrial Film Core is now exposed inside the existing Jellyfish project
workbench.

Open a project and select:

```text
Project Workbench -> Film Core
```

The same view is also reachable from:

```text
Projects -> Project Card -> Film Core
Projects -> Project Preview -> Film Core Status
Project Workbench Header -> Film Core
Direct URL -> /projects/{project_id}?tab=filmCore
```

Backend endpoints:

```text
GET  /api/v1/film/industrial/projects/{project_id}/overview
POST /api/v1/film/industrial/projects/{project_id}/plan
```

Local frontend runtime defaults to Jellyfish backend `http://localhost:8011`.
If Vite moves from `7788` to `7790` because the first port is occupied, backend
CORS still allows the studio requests, including `/api/v1/studio/projects` and
`/api/v1/film/tasks`.

The overview endpoint maps live Jellyfish project/chapter/shot/asset/task state
into:

- Novel / Script
- Story Graph
- Director Planner
- Film Core
- Prompt Compiler
- Runtime Adapter
- Render Runtime
- Video Models
- QA Engine
- Retry Engine
- Final Editing

The same overview now also exposes the starter-kit implementation evidence:

```text
implementation_status      9/9 complete
implementation_phases      Phase 1 through Phase 9 with owner, evidence, and code/test surface
```

This is rendered in the `Film Core` tab as the `九阶段交付状态` panel, so the
producer can see that the nine implementation phases are complete without
opening repository docs.

The plan endpoint returns a preview contract for render queue entries, QA
thresholds, retry repair patches, post-production steps, and current blockers.
It does not bypass Jellyfish UI or replace Jellyfish task/media records.
