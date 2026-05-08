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
POST /api/v1/film/industrial/projects/{project_id}/run
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
The run endpoint writes the industrial loop into Jellyfish task records:

- `industrial_video_render` tasks linked to shot video relations
- `industrial_qa` tasks linked to generated-video shots
- `industrial_retry_plan` tasks linked to ready shots that still need accepted video
- `industrial_post_production` tasks linked to the project or chapter export scope
- `industrial_gate` task when the project is blocked before any renderable shot exists

This means the Film Core is no longer only a document or preview. It has a
Jellyfish-native UI surface, API surface, OpenAPI client, task-center writeback,
and test coverage. Real provider workers still decide when actual files are
created and when `shots.generated_video_file_id` is updated; the Film Core keeps
that execution behind the runtime adapter boundary.

---

## 11. Are The Documented Functions Complete?

Short answer: the industrial architecture, UI entry point, planning contract,
task writeback, tests, and operator documentation are implemented. The system is
usable as a production control plane today, and it avoids the toy-generator
failure mode by keeping story, assets, prompts, runtime, QA, retry, and final
editing as separate systems.

Implemented:

- graph-based workflow and 11-node production pipeline
- ECS-inspired Film Core primitives
- runtime abstraction for video/image providers
- prompt compiler contract from structured state
- character, costume, prop, scene, and shot continuity scoring
- automatic QA policy and retry repair-patch planning
- batch render queue planning
- Jellyfish-native Project Workbench `Film Core` tab
- task-center writeback through `generation_tasks` and `generation_task_links`
- CORS/runtime defaults for `7790 -> 8011`
- OpenAPI generated frontend client
- full local run path for backend `8011` and frontend `7790`

UI operation is involved. The intended operator path is not command-line only:
producers and artists use Jellyfish pages for project, chapter, assets, shots,
Film Core, task center, and editing. The CLI and HTTP smoke endpoints are for
engineering verification.

Industry pain points addressed:

- character drift: character/actor identity lock is surfaced as a health score
- costume/prop drift: costume and prop bindings are measured separately
- shot continuity breakage: Story Graph and Director Planner are explicit stages
- prompt randomness: prompt compiler contracts replace freehand prompt splicing
- vendor lock-in: runtime adapters keep providers behind one boundary
- manual QA bottleneck: QA tasks and thresholds are structured and repeatable
- expensive blind retry: Retry Engine produces targeted repair patches
- batch chaos: Film Core creates queueable tasks with task-link writeback

Remaining production integration work is provider-specific worker binding and
real CV/CLIP/face/outfit detectors. Those are deliberately runtime modules, not
Film Core monolith code.

---

## 12. From Zero To A Multi-Episode AI Manju

This is the recommended operator manual for creating a multi-episode AI manju
from a blank local setup.

### 12.1 Prepare The Local Environment

1. Clone and initialize the repository.

```bash
git submodule update --init --recursive
```

2. Start Jellyfish backend on the Film Core default port.

```bash
cd vendor/jellyfish/backend
NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 \
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8011
```

3. Confirm backend health.

```bash
NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 \
curl http://127.0.0.1:8011/health
```

Expected response:

```json
{"code":200,"message":"success","data":{"status":"ok"},"meta":null}
```

4. Start or open the Jellyfish frontend. In this workspace it is commonly
served at:

```text
http://localhost:7790/projects
```

If you start it manually:

```bash
cd vendor/jellyfish/front
VITE_BACKEND_URL=http://127.0.0.1:8011 npx pnpm@9.15.9 run dev -- --host 0.0.0.0 --port 7790
```

5. Configure model providers in Jellyfish:

```text
侧边栏 -> 模型管理 -> Providers / Models / Settings
```

At minimum, set one default image model and one default video model. The Film
Core can plan without credentials, but real image/video generation requires
valid provider keys.

### 12.2 Create A Series Project

1. Open `项目列表`.
2. Click `新建项目`.
3. Fill:

- project name, for example `霓虹审判`
- visual style, for example `现实`
- project style, for example `真人都市`
- seed, keep a fixed number for repeatability
- default video ratio, usually `9:16` for short drama or `16:9` for film
- enable unified style

4. Click `创建并进入`.

The project seed and unified style become global consistency constraints. Do
not change them mid-series unless you intentionally want a visual reset.

### 12.3 Build Multiple Episodes Or Chapters

In Jellyfish this project stores episodes as chapters.

1. Open the project workbench.
2. Go to `章节`.
3. Create one chapter per episode:

- Episode 1: setup and hook
- Episode 2: conflict escalation
- Episode 3: reversal
- Episode 4+: continuing arcs

4. Paste raw script/novel text into each chapter.
5. Keep character names, locations, key props, and outfits stable across
chapters. The extraction and Film Core layers depend on stable names.

### 12.4 Extract Story Graph And Shot Lists

For each chapter:

1. Use the project card's recommended next action or open the chapter shots page.
2. Run shot extraction.
3. Review every shot title, order, and script excerpt.
4. Confirm the shot list before moving to asset preparation.

This creates the Story Graph stage. It is the backbone for long-story
continuity; do not skip it for multi-episode production.

### 12.5 Prepare Characters, Assets, And Director Data

1. Open `演员`, `角色`, `场景`, `道具`, and `服装`.
2. Create the reusable assets:

- protagonist and supporting characters
- actor/reference images for identity lock
- recurring scenes
- props with story significance
- costume variants and continuity rules

3. Open each shot in the shot studio.
4. Confirm:

- characters appearing in the shot
- scene binding
- prop binding
- costume binding
- camera shot type
- angle
- movement
- duration
- action beats
- dialogue lines
- first/key/last frame prompt or generated frame references

This turns the project from text into controllable film state.

### 12.6 Use Film Core Overview

Open Film Core from any of these entry points:

```text
项目列表顶部 Film Core button
项目卡片 Film Core
项目速览 Film Core 状态
项目工作台顶部 Film Core
/projects/{project_id}?tab=filmCore
```

Read these panels in order:

1. `九阶段交付状态`: confirms the implementation stack is complete.
2. `工业化分数`: tells whether this project is ready for batch production.
3. `一致性健康`: shows identity, scene, prop, and costume readiness.
4. `痛点诊断`: explains why a project is still fragile.
5. `生产闭环`: shows the 11 runtime stages from script to final editing.

If the page says the project has blockers, resolve them in the normal Jellyfish
pages first. Film Core intentionally points back to the right production object
instead of hiding problems behind a one-click button.

### 12.7 Generate A Closed-Loop Plan

In `Film Core`:

1. Click `生成闭环计划`.
2. Review:

- render queue length
- provider/model boundary
- QA thresholds
- retry candidate count
- post-production steps
- blockers

The plan is a preview. It tells you what the system will queue and why.

### 12.8 Create Production Tasks

In `Film Core`:

1. Click `创建生产任务`.
2. Confirm the writeback panel appears.
3. Open the task center.
4. Filter or inspect task kinds:

```text
industrial_video_render
industrial_qa
industrial_retry_plan
industrial_post_production
industrial_gate
```

These records are written to Jellyfish `generation_tasks` and
`generation_task_links`. That gives the batch pipeline durable state and makes
the tasks visible in the existing UI.

### 12.9 Generate Media

For each ready shot:

1. Use existing Jellyfish video generation controls when provider credentials
are configured.
2. Check frame references and prompt preview before submitting.
3. Let task center track progress.
4. Adopt the generated video when it passes review.

The industrial task ledger and the normal video generation tasks share the same
task-center substrate. This keeps Film Core orchestration separate from
provider execution.

### 12.10 QA And Retry

After videos exist:

1. Return to `Film Core`.
2. Click `创建生产任务` again to queue QA tasks for generated-video shots.
3. Use QA outputs and retry tasks to decide which shots need repair.
4. Retry only failed shots, and preserve accepted shots.

Retry repair patches should target specific causes:

- identity reference strength
- costume or prop lock
- lower randomness
- first/key/last-frame reference reuse
- camera/action completeness

### 12.11 Final Editing And Export

When accepted clips exist:

1. Open `进入后期剪辑`.
2. Assemble shots in order.
3. Add or verify:

- TTS or voiceover
- subtitles
- BGM
- transitions
- final aspect ratio

4. Export the episode.
5. Repeat for every chapter/episode.

The post-production task created by Film Core records the intended export scope
and writeback targets, while actual file creation remains with the editor and
runtime workers.

### 12.12 Multi-Episode Continuity Checklist

Before starting the next episode, check:

- project seed unchanged
- visual style unchanged
- character references still accepted
- costume variants named and reused intentionally
- recurring scenes share the same scene records
- props are linked to the same prop records
- episode cliffhanger state is reflected in the next chapter's raw text
- Film Core industrial score does not regress
- accepted videos are not retried unless QA flags a real issue

That loop is the production rhythm: chapter text, shot graph, assets, Film Core,
task queue, generation, QA, retry, editing, then next episode.
