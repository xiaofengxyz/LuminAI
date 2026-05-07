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
- `tests/test_jellyfish_platform_bridge.py`

Detailed blueprint:

- `docs/jellyfish_base_integration_blueprint.md`
- `docs/project_function_manual.md`

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

## Non-Goals For This Pass

- No giant monolith.
- No hardcoded final cinematic prompts.
- No direct dependency on one runtime provider.
- No duplicate platform UI before Jellyfish base integration is stable.
