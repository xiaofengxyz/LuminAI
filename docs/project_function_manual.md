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
- persist CineForge workflow state inside Jellyfish as nine editable stages
- save stage-level operator edits with versioned task-ledger evidence
- queue targeted stage regeneration without resetting approved project state
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
2. Write approved provider outputs and final retry outcomes back into Jellyfish
   media and shot records after real workers finish.
3. Add provider-specific workers that execute the closed-loop plans while
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
POST  /api/v1/film/industrial/text-to-drama
GET   /api/v1/film/industrial/projects/{project_id}/overview
GET   /api/v1/film/industrial/projects/{project_id}/workflow-state
PATCH /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}
POST  /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/regenerate
POST  /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/complete
POST  /api/v1/film/industrial/projects/{project_id}/plan
POST  /api/v1/film/industrial/projects/{project_id}/run
```

Local frontend runtime defaults to Jellyfish backend `http://127.0.0.1:8011`.
Use the `dev:film-core` script when you want the operator UI to be predictably
available at `http://localhost:7790/projects`; backend CORS also allows other
local Vite ports when the port is intentionally changed.

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

The same overview also exposes two producer-facing control contracts:

- `creation_entries`: explains the three creation surfaces. `新建空项目` only
  creates a blank Project shell; `一键文本生成漫剧` creates the story/assets/shots
  from one text; `Film Core` is the existing-project control center.
- `shooting_gate`: blocks render queues until the project has novel/script
  text, shot graph, characters, actor identity references, scenes, props,
  costumes, shot details, and ready shots.

The workflow-state endpoints persist the CineForge Prompt workflow as nine
editable stages:

```text
workflow_architecture
novel_engine
asset_pipeline
image_runtime
video_runtime
qa_retry_engine
studio_ui
data_schema
final_integration
```

`GET /workflow-state` initializes or loads `cineforge_workflow_states`.
`PATCH /workflow-state/{stage_key}` merges a structured operator patch, bumps
the workflow version, and writes a succeeded `cineforge_workflow_edit` task.
`POST /workflow-state/{stage_key}/regenerate` queues a pending
`cineforge_stage_regenerate` task linked to the same workflow. This is the
edit/regenerate loop required by the CineForge prompts, and it reuses Jellyfish
task tables instead of inventing a second queue.
`POST /workflow-state/{stage_key}/complete` applies the stage switch:
automatic stages activate the next stage, while manual stages stop with
`waiting_operator`.

The plan endpoint returns a preview contract for render queue entries, QA
thresholds, retry repair patches, post-production steps, and current blockers.
If `shooting_gate.ready=false`, the plan intentionally returns an empty render
queue and high-severity blockers. This prevents the old failure mode where a
project could be sent to shooting before characters or assets existed.
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
- persisted nine-stage CineForge workflow state
- stage-level edit and targeted regeneration controls
- stage-level automatic/manual execution switches and completion gates
- text-to-drama intake from one source text into generated novel manuscript,
  multi-episode scripts, storyboard shots, character/scene/prop/costume/VFX
  bibles, role web reference-harvest tasks, workflow state, and task ledger
- provider/model runtime config isolation with base URL and key presence checks
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
- model endpoint sprawl: providers and models isolate base URLs and API keys
  from story/runtime orchestration
- manual QA bottleneck: QA tasks and thresholds are structured and repeatable
- expensive blind retry: Retry Engine produces targeted repair patches
- destructive rework after edits: workflow stages are versioned and can be
  regenerated one at a time
- risky full automation: manual switches intentionally halt at
  `waiting_operator` when a stage needs user approval
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

2. Start Jellyfish backend and frontend on the Film Core default ports.

Recommended one-command local startup:

```bash
scripts/start_jellyfish_film_core.sh
```

This helper exports `NO_PROXY=localhost,127.0.0.1,::1` and uses local direct
URLs. Without that bypass, a host proxy can return `502 Bad Gateway` for
`127.0.0.1:8011` even when uvicorn is healthy.

Manual backend startup:

```bash
cd vendor/jellyfish/backend
NO_PROXY=localhost,127.0.0.1,::1 no_proxy=localhost,127.0.0.1,::1 \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

3. Confirm backend health.

```bash
NO_PROXY=localhost,127.0.0.1,::1 no_proxy=localhost,127.0.0.1,::1 \
curl --noproxy '*' http://127.0.0.1:8011/health
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
VITE_BACKEND_URL=http://127.0.0.1:8011 npx pnpm@9.15.9 run dev:film-core
```

If there are no projects yet, the project list still shows a Film Core button.
Clicking it opens project creation first because Film Core overview is scoped to
a concrete project.

5. Configure model providers in Jellyfish:

```text
侧边栏 -> 模型管理 -> Providers / Models / Settings
```

At minimum:

1. Add a Provider.
2. Fill `文本/通用 Base URL`.
3. Optionally fill `图片 Base URL` and `视频 Base URL` when a gateway separates
   image and video endpoints.
4. Fill `API Key` and `API Secret` if that provider requires them.
5. Add text/image/video Models and bind each model to a Provider.
6. Open `Settings` and choose default text, image, and video models.

The runtime adapter boundary resolves each model to:

```text
provider_key + category + base_url + api_key_configured + model params
```

Secrets are stored in Jellyfish provider records and are not returned by the
runtime-config API. Built-in provider keys include OpenAI, 火山引擎, 阿里百炼,
ComfyUI, FLUX, SDXL, StoryDiffusion, Kling, Seedance, Veo, Wan2.1, Sora, and
Vidu. The Film Core can plan without credentials, but real generation workers
require valid provider keys and reachable base URLs.

### 12.2 Fast Path: Text To Multi-Episode AI Manju

Use this path for the final product goal:

```text
输入一段文字 -> 生成/扩展小说状态 -> 生成多集漫剧生产状态 -> 进入 Film Core 自动闭环
```

1. Open:

```text
http://localhost:7790/projects
```

2. Click `一键文本生成漫剧`.
3. Fill:

- `项目名称` or leave it blank to use the first sentence
- `原始创意/梗概/正文`
- visual style and project style
- episode count, for example `3`
- shots per episode, for example `6`
- default video ratio, usually `9:16`
- flow switch: `自动推进` or `人工停等`
- `创建角色网络参考采集任务`: leave enabled when the engine should queue
  candidate image/video reference searches for each character. The task records
  collect URL and licensing metadata only; real downloads and commercial use
  still require a later worker or operator approval.

4. Click `创建并进入 Film Core`.

The backend creates:

- one Jellyfish project
- one chapter per episode
- generated novel text in each chapter's `raw_text`
- script outlines in each chapter's `condensed_text`
- storyboard shots for every episode
- `ShotDetail` rows with camera, movement, duration, action beats, frame prompts,
  scene binding, and VFX notes
- character, actor-image slot, costume, scene, prop, and prop-owner records
- shot-to-character, shot-to-scene, shot-to-prop, and shot-to-costume links
- first/key/last frame image slots for each shot
- `CineForgeWorkflowState`
- `cineforge_text_to_drama_intake` task
- one `cineforge_reference_harvest` task per generated character when reference
  harvest is enabled
- `cineforge_text_to_drama_auto_pipeline` task when automation is enabled

You land at:

```text
/projects/{project_id}?tab=filmCore
```

From there, continue with the Film Core sections below. Automatic mode moves
stages forward until a stage is configured as manual. Manual mode creates the
recoverable state and waits for you to approve/edit/regenerate.

### 12.3 Create A Series Project Manually

1. Open `项目列表`.
2. Click `新建空项目`.
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

### 12.4 Build Multiple Episodes Or Chapters

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

### 12.5 Extract Story Graph And Shot Lists

For each chapter:

1. Use the project card's recommended next action or open the chapter shots page.
2. Run shot extraction.
3. Review every shot title, order, and script excerpt.
4. Confirm the shot list before moving to asset preparation.

This creates the Story Graph stage. It is the backbone for long-story
continuity; do not skip it for multi-episode production.

### 12.6 Prepare Characters, Assets, And Director Data

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

### 12.7 Use Film Core Overview

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
2. `拍摄前置门禁`: tells whether render tasks are allowed yet.
3. `创建入口职责`: explains why blank project, one-click text-to-drama, and
   Film Core are separate surfaces.
4. `工业化分数`: tells whether this project is ready for batch production.
5. `一致性健康`: shows identity, scene, prop, and costume readiness.
6. `痛点诊断`: explains why a project is still fragile.
7. `生产闭环`: shows the 11 runtime stages from script to final editing.

If the page says the project has blockers, resolve them in the normal Jellyfish
pages first. Film Core intentionally points back to the right production object
instead of hiding problems behind a one-click button.

### 12.8 Edit, Regenerate, Or Auto-Advance CineForge Workflow State

Use `CineForge 可编辑工作流状态` when the producer or director changes the plan
after seeing the Film Core diagnosis.

1. Select a stage:

```text
workflow_architecture
novel_engine
asset_pipeline
image_runtime
video_runtime
qa_retry_engine
studio_ui
data_schema
final_integration
```

2. Read the JSON preview for that stage. It shows the persisted world bible,
shot graph, image/video runtime policy, QA policy, or integration contract that
the engine will use.
3. Type the reason for the change in the note box.
4. Use `阶段推进开关`:

- `自动`: after the stage is completed, the next stage becomes active
- `人工`: after the stage is completed, the workflow records `waiting_operator`
  and stops for user operation

5. Click `保存阶段编辑` when you want to persist a structured operator override.
6. Click `重生成阶段` when that one stage should be recomputed or handed to a
provider worker again.
7. Click `完成并推进` when this stage's current output is accepted and the switch
should be applied.

The edit action increments the workflow version and creates a
`cineforge_workflow_edit` task. The regenerate action creates a
`cineforge_stage_regenerate` task. Completing a stage creates either
`cineforge_stage_auto_advance` or `cineforge_stage_manual_gate`. All are linked
back to the same workflow state, so approved shots and accepted media do not
need to be thrown away just because one stage changed.

Use this for:

- changing the world bible or cliffhanger rule after producer review
- locking a newly approved costume or prop into the asset pipeline
- changing image runtime policy from one adapter family to another
- asking video runtime to preserve approved outputs while refreshing one stage
- tightening QA/retry policy before batch production

### 12.9 Generate A Closed-Loop Plan

In `Film Core`:

1. Click `生成闭环计划`.
2. Review:

- render queue length
- provider/model boundary
- QA thresholds
- retry candidate count
- post-production steps
- blockers

The plan is a preview. It tells you what the system will queue and why. If the
shooting gate is blocked, the render queue is empty by design; resolve the gate
before attempting production.

### 12.10 Create Production Tasks

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

This button is disabled while `拍摄前置门禁` is blocked. Once the gate is ready,
records are written to Jellyfish `generation_tasks` and
`generation_task_links`. That gives the batch pipeline durable state and makes
the tasks visible in the existing UI.

### 12.11 Generate Media

For each ready shot:

1. Use existing Jellyfish video generation controls when provider credentials
are configured.
2. Check frame references and prompt preview before submitting.
3. Let task center track progress.
4. Adopt the generated video when it passes review.

The industrial task ledger and the normal video generation tasks share the same
task-center substrate. This keeps Film Core orchestration separate from
provider execution.

### 12.12 QA And Retry

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

### 12.13 Final Editing And Export

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

### 12.14 Multi-Episode Continuity Checklist

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

### 12.15 Completion, UI Scope, And Pain-Point Answer

Are the requested document functions done?

- Workflow persistence: done through `cineforge_workflow_states`.
- Edit/regenerate: done through workflow-state `PATCH` and regenerate `POST`.
- Automatic/manual switches: done per stage through `execution_mode`, the Film
  Core switch, and the complete-stage endpoint.
- Text-to-drama entry: done through `POST /api/v1/film/industrial/text-to-drama`
  and the `一键文本生成漫剧` project-list UI. It now generates novel manuscript,
  episode scripts, storyboard shots, asset bibles, frame slots, VFX notes, and
  role reference-harvest tasks.
- Shooting gate: done through Film Core `shooting_gate`; production plans do not
  expose render queues until characters/assets/shot details are ready.
- Runtime adapter isolation: done through Provider/Model settings, category
  base URL overrides, no-secret runtime-config views, and provider registry
  keys for mainstream image/video runtimes.
- QA/retry/task ledger: done as queueable Jellyfish `generation_tasks` and
  `generation_task_links`.

Does this involve page UI operation?

Yes. The operable UI surfaces are:

- `项目列表 -> 一键文本生成漫剧`
- `项目列表/项目卡片/项目速览 -> Film Core`
- `Project Workbench -> Film Core`
- `模型管理 -> Providers / Models / Settings`
- normal Jellyfish chapter, shot, asset, task center, and editor pages

Does it address industry pain points?

Yes at the orchestration and state layer: character/scene/prop/costume
continuity, prompt drift, runtime lock-in, destructive producer edits, retry
chaos, and batch task visibility now have explicit state and task-ledger
contracts. Remaining production work is not architecture; it is binding concrete
provider workers and real CV/CLIP/face/outfit detector implementations.
