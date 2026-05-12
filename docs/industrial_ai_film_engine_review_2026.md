# Industrial AI Film Engine Review 2026-05-08

> Role lens: senior AI drama producer, product manager, director systems
> architect, and test owner.

## 1. Direct Answer To The Run/UI Gap

Before this pass, LuminAI could run, but it was not operable as a studio UI.
The local server exposed `/health` and `/demo/closed-loop-plan`, so phase
completion was judged by backend contracts, CLI output, HTTP JSON, and tests.
That is not enough for a production operator.

This pass adds an actual dependency-light Studio Dashboard at:

```text
http://127.0.0.1:8765/
```

The dashboard exposes:

- stage completion index
- shot workbench
- QA failures
- retry requests
- render request prompts and references
- Jellyfish base status
- industrial pain-point review

The JSON contracts remain available:

```text
GET /api/studio/status
GET /api/jellyfish/base-status
GET /demo/closed-loop-plan
GET /health
```

## 2. Direct Answer To The Jellyfish Base Gap

Jellyfish is now tracked as the upstream studio base at:

```text
vendor/jellyfish
```

It is added as a git submodule from:

```text
https://github.com/Forget-C/Jellyfish
```

Why submodule instead of copying the whole code into LuminAI:

- Jellyfish should remain the Studio OS / workflow core.
- LuminAI should remain the Film Core, continuity, prompt, QA, retry, and
  runtime abstraction layer.
- A submodule keeps the upstream base auditable, upgradable, and forkable.
- The Film Core can bind to Jellyfish OpenAPI and records without hard-coding a
  fork schema into runtime code.

The base can be inspected with:

```bash
python3 -m src.film_engine.jellyfish_base
```

Recommended Jellyfish Docker run command:

```bash
cd vendor/jellyfish
MYSQL_PORT=3337 REDIS_PORT=6384 RUSTFS_PORT=9010 RUSTFS_CONSOLE_PORT=9011 \
docker compose --env-file deploy/compose/.env.example \
  -f deploy/compose/docker-compose.yml up -d --build
```

Expected Jellyfish ports:

```text
Frontend: http://localhost:7788
Backend:  http://localhost:8000  (Docker Compose)
Docs:     http://localhost:8000/docs
Backend:  http://localhost:8011  (local dev / Film Core default)
Docs:     http://localhost:8011/docs
```

Run note from this session:

- Docker Compose config validated.
- Full Docker Compose startup was attempted, but backend image build hit Debian
  apt mirror `502/404` while installing base system packages.
- Current local fallback run path: Jellyfish backend via SQLite on
  `http://127.0.0.1:8011/openapi.json`, and the Jellyfish frontend through
  `npx pnpm@9.15.9 run dev:film-core` on `http://127.0.0.1:7790/`.

## 3. Current Open Source Baseline

Checked on 2026-05-08:

| Project | Current signal | What LuminAI should take |
| --- | --- | --- |
| Jellyfish | End-to-end AI short drama workspace with project, chapter, shot, asset, task, OpenAPI, UI, Docker Compose, and local dev commands. | Main Studio OS / workflow base. |
| ComfyUI | Large graph/node ecosystem for controllable visual workflows and production APIs. | Graph execution and visual workflow inspiration. |
| MoneyPrinterTurbo | High-popularity one-click short-video factory. | Batch automation, subtitle, and low-cost video production lessons. |
| DiffSynth Studio | Diffusion/video framework with Wan and other video synthesis examples. | Runtime adapters, memory-aware local video pipelines, timeline editing ideas. |
| StoryDiffusion | Long-range consistent image/video generation research and repo. | Character consistency and long-story reference strategy. |

## 4. Product Definition

LuminAI is not a single prompt-to-video tool. It is an industrial AI film engine
for realistic short drama production.

The product must support:

- script and novel ingestion
- story graph construction
- director planning
- shot graph and timeline continuity
- character bible, scene bible, prop bible, costume bible, and voice bible
- prompt compilation from structured state
- replaceable runtime providers
- automatic QA
- automatic retry
- final editing and export
- batch production across episodes

The intended flow is:

```text
Novel / Script
-> Story Graph
-> Director Planner
-> Film Core
-> Prompt Compiler
-> Runtime Adapter
-> Render Runtime
-> Video Models
-> QA Engine
-> Retry Engine
-> Final Editing
```

Jellyfish owns the operator workspace around that flow. LuminAI owns the
industrial intelligence that makes outputs repeatable.

## 5. Industry Pain Points And System Answers

| Pain point | Producer answer | Engineering answer |
| --- | --- | --- |
| Face drift | Lock identity references and negative identity terms before each shot. | `CharacterBible`, continuity references, QA `face_similarity`, retry patches. |
| Outfit drift | Treat costumes as assets, not prompt prose. | `outfit_map`, costume assets, prompt compiler outfit clauses. |
| Scene and lighting mismatch | Scene bible defines lighting, weather, tone, and camera style. | `SceneBible`, scene references, lighting continuity state. |
| Shot discontinuity | Shots must be graph nodes with ordered timeline state. | `WorkflowGraph`, `ShotContinuityState`, Jellyfish bridge workflow. |
| Prompt randomness | Prompts must be compiled from state, not hand-written per shot. | `PromptCompiler` from director DSL plus Film State. |
| Runtime lock-in | Providers must execute render intent, not own story logic. | `RenderRequest`, provider registry, Wan/Kling/Vidu adapters. |
| Endpoint/key sprawl across model vendors | Producers need to swap model gateways without rewriting film logic. | Jellyfish Provider/Model records store base URLs and keys; runtime-config resolves provider/category adapters without returning secrets. |
| Manual QA | Production cannot rely on human review for every retry. | `RuleBasedQAEngine`, structured QA issues, retry decisions. |
| Expensive retry chaos | Retry must patch specific prompts and parameters. | `RetryEngine`, repair hints, attempt limits. |
| No final editing closure | Voice, subtitles, compose, concat, and export must be planned. | `PostProductionPlanner` and FFmpeg step compiler. |
| No operator UI | Operators need stage, shot, QA, retry, and base status in the same production workspace. | Jellyfish Project Workbench `Film Core` tab plus `/api/v1/film/industrial/...`. |
| Destructive rework after producer edits | A producer must be able to edit or regenerate one stage without resetting the episode. | `CineForgeWorkflowState`, workflow-state edit/regenerate APIs, task-ledger mutation history. |
| One prompt cannot become a durable series | Source text must become novel, episodes, assets, shots, workflow, and task state. | `text-to-drama` intake creates generated novel chapters, script outlines, storyboard shots, asset bibles, reference-harvest tasks, CineForge workflow, and task ledger. |
| Shooting before assets exist | A project must not render before characters, identity references, scenes, props, costumes, and shot details exist. | Film Core `shooting_gate` blocks render queues and disables production task creation until prerequisites are ready. |
| Automation without control is risky | Some stages should run through, others should wait for producer approval. | Per-stage `execution_mode` switches auto-advance or halt with `waiting_operator`. |

## 6. Architecture From Zero

Recommended ownership boundary:

```text
Jellyfish Studio OS
    Project / Chapter / Shot / Asset / Task / Media / OpenAPI / UI
        |
        v
LuminAI Platform Bridge
    StudioProject / StudioChapter / StudioShot / StudioAsset / StudioTask
        |
        v
LuminAI Film Core
    ECS / WorkflowGraph / FilmState / DirectorConsistency / PromptCompiler
        |
        v
Runtime Layer
    Wan / Kling / Vidu / Veo / DiffSynth / ComfyUI / FFmpeg / TTS
        |
        v
QA + Retry + Final Editing
    Metrics / Repair Hints / Retry Requests / PostProductionPlan
```

Key design rules:

- The UI can change, but the Film Core contracts must stay stable.
- The runtime provider can change, but story, continuity, and QA state cannot.
- Prompts are compiled artifacts, not the source of truth.
- QA results are data, not comments.
- Retry requests are new render requests with traceable causes.

## 7. Current Implementation Map

| Layer | Implemented files |
| --- | --- |
| Jellyfish base | `.gitmodules`, `vendor/jellyfish`, `src/film_engine/jellyfish_base.py` |
| Studio dashboard | `src/film_engine/studio.py`, `src/film_engine/server.py` |
| Platform bridge | `src/film_engine/platform.py`, `src/film_engine/jellyfish.py` |
| Director consistency | `src/film_engine/director.py` |
| Film state | `src/film_engine/state.py` |
| Prompt compiler | `src/film_engine/prompt_compiler.py` |
| Runtime boundary | `src/film_engine/runtime.py`, `src/models/` |
| QA and retry | `src/film_engine/qa.py`, `src/film_engine/retry.py` |
| Closed-loop planning | `src/film_engine/production.py`, `src/film_engine/demo.py` |
| Final editing | `src/film_engine/post_production.py` |
| Batch planning | `src/film_engine/batch.py` |
| Jellyfish-native industrial API | `vendor/jellyfish/backend/app/services/industrial_film_core.py`, `vendor/jellyfish/backend/app/api/v1/routes/film/industrial.py` |
| Text-to-drama blueprint compiler | `vendor/jellyfish/backend/app/services/film/text_to_drama.py` |
| CineForge workflow persistence | `vendor/jellyfish/backend/app/models/industrial.py`, workflow-state endpoints, `vendor/jellyfish/backend/tests/test_industrial_workflow_state.py` |
| Jellyfish-native Film Core UI | `vendor/jellyfish/front/src/pages/aiStudio/project/ProjectWorkbench/tabs/FilmCoreTab.tsx`, `vendor/jellyfish/front/src/services/industrialFilm.ts` |
| Text-to-drama intake | `POST /api/v1/film/industrial/text-to-drama`, `ProjectLobby.tsx` `一键文本生成漫剧` modal |
| Runtime adapter config | Jellyfish `Provider`/`Model` records, `/api/v1/llm/models/{model_id}/runtime-config`, provider registry bootstrap |

## 8. What Is Still Not Claimed Done

The current repository now has an operable dashboard and a real Jellyfish base
checkout, but it is not yet a fully integrated production deployment.

Done in the Jellyfish-native pass:

- exposed a typed industrial Film Core overview endpoint inside Jellyfish
- exposed a closed-loop production plan preview endpoint inside Jellyfish
- exposed persisted CineForge workflow state load/edit/regenerate endpoints
- added a Project Workbench `Film Core` tab instead of a separate UI
- surfaced pipeline stage evidence, consistency health, QA/retry readiness,
  pain-point diagnosis, reference project breakdown, workflow-stage editing,
  targeted stage regeneration, and plan preview
- added deterministic text-to-novel/storyboard/asset blueprint generation,
  role web reference-harvest task creation, and a hard shooting gate before
  render queues are exposed

Still required for true industrial deployment:

- execute real video renders through production credentials
- replace demo QA metrics with CV/CLIP/face/outfit/light detectors
- persist generated media and final provider retry results in Jellyfish media
  and shot tables after workers complete
- add auth, project permissions, multi-user review, and queue governance

## 9. Acceptance Criteria For This Pass

This pass is acceptable when:

- `vendor/jellyfish` is tracked as a real upstream base.
- `python3 -m src.film_engine.jellyfish_base` reports base status.
- `python3 -m src.film_engine.server --host 127.0.0.1 --port 8765` serves a UI.
- `/api/studio/status` exposes stage completion evidence.
- `/api/jellyfish/base-status` exposes Jellyfish path, commit, commands, and ports.
- `/api/v1/film/industrial/projects/{project_id}/overview` exposes the full
  Novel/Script to Final Editing industrial pipeline state.
- `/api/v1/film/industrial/projects/{project_id}/workflow-state` persists and
  returns the nine-stage CineForge workflow state.
- `/api/v1/film/industrial/text-to-drama` creates project, generated novel
  chapters, script outlines, storyboard shots, character/actor/costume/scene/prop
  records, frame slots, reference-harvest tasks, workflow, and task-ledger state
  from one source text.
- `PATCH /workflow-state/{stage_key}` saves stage edits and creates a
  `cineforge_workflow_edit` task ledger event.
- `POST /workflow-state/{stage_key}/regenerate` queues a targeted
  `cineforge_stage_regenerate` task without discarding approved stages.
- `POST /workflow-state/{stage_key}/complete` applies automatic/manual stage
  gates and records either auto-advance or `waiting_operator`.
- `/api/v1/film/industrial/projects/{project_id}/plan` returns render queue,
  QA policy, retry policy, post-production steps, and blockers; render queue is
  empty when `shooting_gate.ready=false`.
- `/api/v1/llm/models/{model_id}/runtime-config` resolves provider/model
  runtime adapter state without exposing secret values.
- Jellyfish Project Workbench includes a `Film Core` tab and the dashboard links
  into it.
- tests cover the UI route, status APIs, Jellyfish base inspection, and stage
  evidence logic, plus Jellyfish-native industrial Film Core contracts.
- full pytest passes.
- Docker Compose config for Jellyfish validates.
