# AI Manju Engine Execution Plan

This plan converts the research report and Jellyfish starter-kit direction into
an implementation path for LuminAI.

## Platform Base Decision

Use Jellyfish as the AI Studio OS / Workflow Core:

- project, chapter, shot, asset, media, task, OpenAPI, and studio UI base
- no rewrite from zero
- no heavy modification of one runtime project
- Film Core attaches through stable bridge contracts

Implemented bridge:

- `src/film_engine/platform.py`
- `src/film_engine/jellyfish_base.py`
- `tests/test_jellyfish_platform_bridge.py`
- `tests/test_jellyfish_base_status.py`

Detailed blueprint:

- `docs/jellyfish_base_integration_blueprint.md`
- `docs/project_function_manual.md`
- `docs/industrial_ai_film_engine_review_2026.md`
- `docs/ai_film_engine_test_cases.md`

## Research Findings

The report identifies the real moat for a 2-3 person AI manju team as a reusable content factory, not a one-click video demo. The highest-value systems are:

- Character asset registry: reference images, outfit state, voice identity, embeddings, and reuse rules.
- Director DSL and shot graph: structured camera language, pacing, shot transitions, and emotional escalation.
- Film state continuity: explicit continuity for characters, outfits, scenes, lighting, timeline, and generated assets.
- Runtime abstraction: route work to Kling, Wan, Vidu, Veo-style providers without coupling the film core to vendor APIs.
- Automatic QA and retry: detect drift and produce repair instructions before retrying expensive renders.
- Batch production: repeatable episode/series pipeline for high-frequency short drama output.

## Implementation Phases

| Phase | Delivery |
| --- | --- |
| Phase 1 | Python package skeleton, Pydantic domain models, provider registry, and media reference resolver. |
| Phase 2 | Comic generation pipeline: series/episode asset inheritance, prompt fallback, local media snapshots, and provider routing. |
| Phase 3 | Runtime adapters for Wan/DashScope, Kling vendor, Vidu vendor, and Wan image references. |
| Phase 4 | Industrial film engine primitives: ECS-inspired registries, graph workflow, prompt compiler, QA reports, retry planner, and batch planner. |
| Phase 5 | Jellyfish platform bridge: StudioProject, StudioChapter, StudioShot, StudioAsset, StudioTask, continuity mapping, workflow mapping, and render request boundary. |
| Phase 6 | Jellyfish fork/API integration: map real Jellyfish project/chapter/shot/asset/task records to bridge contracts. |
| Phase 7 | Runtime grafting: add huobao-drama-style FFmpeg, subtitle, TTS, stitching, and export services under runtime abstraction. |
| Phase 8 | Director and consistency layers: director_ai DSL, BigBanana cinematic rules, StoryDiffusion reference workflow, character/scene bibles. |
| Phase 9 | QA, retry, batch UI, documentation, samples, tests, cleanup, commit, and push. |

## Current Follow-up Implementation Status

| Phase | Status | Evidence |
| --- | --- | --- |
| Phase 6 | Done | `src/film_engine/jellyfish.py` maps Jellyfish OpenAPI/ORM-shaped project, chapter, shot/detail, asset, frame, dialogue, and task records to bridge contracts. |
| Phase 7 | Done | `src/film_engine/post_production.py` plans TTS, subtitles, FFmpeg single-shot compose, multi-shot concat, and final export as runtime-neutral steps. |
| Phase 8 | Done | `src/film_engine/director.py` validates Director DSL and prepares character/scene bible continuity context for prompt compilation. |
| Phase 9 | Done | `src/film_engine/production.py` builds closed-loop chapter plans with render requests, QA reports, retry requests, and optional post-production planning. |
| Phase 10 | Done | `vendor/jellyfish` tracks the real upstream Jellyfish base; `src/film_engine/studio.py` and `src/film_engine/server.py` expose the Studio Dashboard plus status APIs. |

## 2026-05-08 Run Readiness Review Plan

| Finding | Action | Status |
| --- | --- | --- |
| Previous backend phases are implemented, but the repository only documented tests and did not expose a run-ready local entrypoint. | Add a dependency-light CLI/HTTP demo for health and closed-loop production plan smoke checks. | Done |
| Jellyfish blueprint status drifted after later implementation phases. | Mark Film Core attachment, director consistency, QA/retry/batch closure, and run-readiness endpoints as done; move real Jellyfish API binding to the next product phase. | Done |
| Verification must be fixed in code, not only described. | Add tests for the demo summary and HTTP endpoints, then run targeted and full pytest. | Done |
| The project must be run locally in this session. | Start the HTTP server and query `/health` plus `/demo/closed-loop-plan`. | Done |
| The previous run path had no UI and no real Jellyfish checkout. | Track Jellyfish as a submodule, add base inspection, expose `/` as Studio Dashboard, and add `/api/studio/status` plus `/api/jellyfish/base-status`. | Done |

## Next Product Work After This Pass

| Priority | Delivery |
| --- | --- |
| 1 | Bind `JellyfishRecordMapper` and `ClosedLoopProductionPlanner` to a real Jellyfish fork/API client. |
| 2 | Persist generated media, QA reports, retry decisions, and post-production results back into Jellyfish records. |
| 3 | Add provider workers for `RenderRequest` and `PostProductionStep` execution. |
| 4 | Move the lightweight LuminAI dashboard controls into the Jellyfish studio frontend. |

## Non-Goals For This Pass

- No giant monolith.
- No hardcoded final cinematic prompts.
- No direct dependency on one runtime provider.
- No duplicate platform UI before Jellyfish base integration is stable.
