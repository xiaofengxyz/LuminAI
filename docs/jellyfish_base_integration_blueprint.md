# Jellyfish Base Integration Blueprint

> Session baseline: 2026-05-08
>
> Goal: use Jellyfish as the AI Studio OS / Workflow Core, then split the best
> capabilities from other AI film projects into reusable LuminAI Film Core
> systems.

---

## 1. Decision

LuminAI will not rebuild a complete studio platform from zero.

The recommended base is:

```text
Jellyfish = AI Studio OS / Workflow Core
LuminAI Film Core = industrial film intelligence layer
Runtime Projects = replaceable execution adapters
```

Jellyfish owns platform primitives:

- project and chapter management
- script understanding and shot preparation
- asset and entity management
- keyframe / reference image / shot workspace
- async task center
- model and prompt infrastructure
- OpenAPI-backed frontend/backend contracts
- studio UI and collaboration surface

LuminAI owns the moat:

- Director DSL
- Shot Graph
- Character Registry
- Scene Registry
- Film State Engine
- CineForge Workflow State Ledger
- Prompt Compiler
- QA Engine
- Retry Engine
- Batch Planner

This keeps Jellyfish as the stable workbench while LuminAI adds film-grade
continuity, QA, retry, and runtime abstraction.

---

## 2. Source Inputs

Local project sources:

- `AGENTS.md`
- `docs/ai_film_engine_starter_kit_final_stable_v_1.md`
- `docs/complete_ai_manjv_open_source_research_report_2026.md`
- `SYSTEM_ARCHITECTURE.md`
- existing `src/film_engine` primitives

External project anchors:

- Jellyfish: https://github.com/Forget-C/Jellyfish
- huobao-drama: https://github.com/chatfire-AI/huobao-drama
- director_ai: https://github.com/freestylefly/director_ai
- BigBanana-AI-Director: https://github.com/shuyu-labs/BigBanana-AI-Director
- waoowaoo: https://github.com/waooAI/waoowaoo
- Toonflow-app: https://github.com/HBAI-Ltd/Toonflow-app
- StoryDiffusion: https://github.com/HVision-NKU/StoryDiffusion
- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- DiffSynth Studio: https://github.com/modelscope/DiffSynth-Studio
- AnimateDiff: https://github.com/guoyww/AnimateDiff

---

## 3. Base Architecture

```text
Jellyfish Studio OS
    Project / Chapter / Shot / Asset / Task / Media / OpenAPI / UI
        ↓
LuminAI Platform Bridge
    StudioProject / StudioChapter / StudioShot / StudioAsset / StudioTask
        ↓
LuminAI Film Core
    ECS Registry / Workflow Graph / Film State / Prompt Compiler
        ↓
Director + Consistency Systems
    Director DSL / Shot Graph / Character Bible / Scene Bible
        ↓
Runtime Abstraction
    Wan / Kling / Vidu / Veo-style providers / FFmpeg / TTS / Subtitle
        ↓
QA + Retry + Batch
    Metrics / Repair Hints / Retry Decisions / Episode Batch Plans
```

The bridge layer added in this session is `src/film_engine/platform.py`.
It models Jellyfish-style platform objects without coupling the Film Core to a
specific Jellyfish fork or database schema.

The upstream Jellyfish base is now tracked at `vendor/jellyfish` as a git
submodule. `src/film_engine/jellyfish_base.py` inspects the base checkout,
reports the pinned commit, exposes Docker/local run commands, and feeds the
Studio Dashboard.

---

## 4. Concept Mapping

| Jellyfish Concept | LuminAI Contract | Film Core Usage |
| --- | --- | --- |
| Project | `StudioProject`, `Series` | Production unit, batch scope, shared asset scope. |
| Chapter | `StudioChapter`, `Script` | Episode/script unit, ordered shot workflow. |
| Shot | `StudioShot`, `StoryboardFrame`, `ShotContinuityState` | Director DSL input, continuity state, render unit. |
| Character / Actor | `StudioAsset(kind="character")`, `Character` | Identity references, voice, outfit, embedding, QA target. |
| Scene | `StudioAsset(kind="scene")`, `Scene` | Lighting, weather, tone, camera style, continuity target. |
| Prop / Costume | `StudioAsset(kind="prop"|"costume")`, `Prop` | Reference media and shot-level consistency constraints. |
| Task | `StudioTask`, `VideoTask`, `RenderRequest` | Async generation, status tracking, retryable runtime request. |
| Generated Media | `reference_media`, `RenderResult` | Reusable input for future shots and QA comparison. |

---

## 5. Capability Split From Other Projects

| Source Project | Take | Add To Jellyfish Base As | Keep Out Of Core |
| --- | --- | --- | --- |
| huobao-drama | Render pipeline, FFmpeg orchestration, subtitle pipeline, TTS workflow, stitching logic, provider adapters. | Runtime Layer under Jellyfish task center. | Main UI and primary workflow ownership. |
| director_ai | Director DSL, shot abstraction, camera grammar, scene timeline, transition metadata. | Director Layer that compiles shot intent into structured prompt inputs. | Experimental app shell. |
| BigBanana-AI-Director | Keyframe-driven thinking, pacing rules, emotion-to-camera mapping, cinematic rhythm, asset-constrained generation. | Cinematic Rule Layer and keyframe policy before runtime. | Closed or heavy platform assumptions. |
| waoowaoo | Workflow graph, context orchestration, memory flow, Hollywood-style production roles. | Orchestration Layer and long-story memory contracts. | Over-heavy platform rebuild. |
| Toonflow-app | Storyboard UI, timeline editing, shot editing interactions. | Storyboard UI Layer inside Jellyfish studio. | Duplicate backend workflow. |
| StoryDiffusion | Character consistency, reference image flow, long-story image continuity. | Character Consistency Layer and reference selection rules. | Model-specific internals in Film Core. |
| ComfyUI | Node graph architecture and reusable workflow execution. | Future graph runtime inspiration for visual workflow editing. | Hard dependency on a single graph engine. |
| DiffSynth Studio | Timeline and shot-based diffusion editing. | Timeline orchestration and video edit adapters. | Vendor/model-specific timeline assumptions. |
| AnimateDiff | Motion modules and controllable animation workflow. | Optional local motion runtime adapter. | Motion logic inside Director DSL. |

---

## 6. Current Implementation Status

Implemented in this repository:

- `src/film_engine/ecs.py`: ECS-inspired entity registry.
- `src/film_engine/graph.py`: workflow graph and topological execution order.
- `src/film_engine/state.py`: shot continuity state.
- `src/film_engine/prompt_compiler.py`: structured prompt compilation.
- `src/film_engine/runtime.py`: runtime adapter boundary.
- `src/film_engine/qa.py`: rule-based QA report contract.
- `src/film_engine/retry.py`: retry decision contract.
- `src/film_engine/batch.py`: industrial batch plan.
- `src/film_engine/platform.py`: Jellyfish-style platform bridge.
- `src/film_engine/jellyfish.py`: dependency-free mapper for Jellyfish
  OpenAPI/ORM-shaped project, chapter, shot, asset, and task records.
- `src/film_engine/jellyfish_base.py`: upstream Jellyfish base inspector and
  run-command manifest.
- `src/film_engine/director.py`: Director DSL validation plus character and
  scene bible consistency preparation.
- `src/film_engine/post_production.py`: huobao-style TTS, subtitle, FFmpeg
  compose, concat, and export planning under runtime abstraction.
- `src/apps/comic_gen`: current series/episode/asset/task pipeline.
- `src/film_engine/demo.py`: closed-loop demo plan for run-readiness smoke
  testing.
- `src/film_engine/server.py`: dependency-light local HTTP runtime with health
  demo plan endpoints, Studio Dashboard UI, and status APIs.
- `src/film_engine/studio.py`: stage index, industrial review payload, and
  local dashboard renderer.
- `vendor/jellyfish`: pinned upstream Jellyfish Studio OS base.
- `vendor/jellyfish/backend/app/models/industrial.py`: persisted
  `CineForgeWorkflowState` table for stage edits and regeneration history.
- `vendor/jellyfish/backend/app/api/v1/routes/film/industrial.py`:
  text-to-drama, overview, workflow-state load/edit/regenerate/complete, plan,
  and run endpoints.
- `vendor/jellyfish/backend/app/services/film/text_to_drama.py`: deterministic
  text-to-novel, episode script, storyboard, asset bible, VFX, and role
  reference-harvest blueprint compiler.
- `vendor/jellyfish/backend/app/services/llm/manage.py`: runtime-config
  adapter views for provider/model base URL and key state without exposing
  secrets.

The current bridge defines this workflow order:

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

This order keeps Jellyfish preparation states ahead of LuminAI Film Core
generation, QA, and retry.

---

## 7. Implementation Phases

| Phase | Status | Delivery |
| --- | --- | --- |
| Phase 0 | Done | Read AGENTS and starter kit, confirmed Jellyfish as base, reviewed current code and docs. |
| Phase 1 | Done | Added `StudioPlatformBridge` contracts and tests. |
| Phase 2 | Done | Documented Jellyfish base strategy, capability split, and project manual. |
| Phase 3 | Done | Added `JellyfishRecordMapper` to map Jellyfish API/ORM-shaped project, chapter, shot/detail, asset, frame, dialogue, and task records to `StudioProject`, `StudioChapter`, `StudioShot`, `StudioAsset`, and `StudioTask` without importing Jellyfish runtime code. |
| Phase 4 | Done | Attached Film Core planning to Jellyfish-style shot readiness through `ClosedLoopProductionPlanner`, producing continuity, director context, prompt compilation, render requests, QA reports, and retry requests. |
| Phase 5 | Done | Added runtime-neutral post-production planning for TTS, subtitles, FFmpeg single-shot compose, multi-shot concat, and final export. |
| Phase 6 | Done | Added backend director rules, character/scene bible consistency contracts, QA/retry/batch closure, and dependency-light run-readiness endpoints before UI binding. |
| Phase 7 | Done | Added a real upstream Jellyfish submodule, Jellyfish base inspector, local Studio Dashboard UI, and status APIs. |
| Phase 8 | Done | Added Jellyfish-native industrial Film Core overview and plan-preview APIs plus a Project Workbench `Film Core` tab. The tab now surfaces the starter-kit `9/9` implementation evidence and the 11-node production pipeline. |
| Phase 9 | Done | Added Film Core `run` API and UI action that writes render, QA, retry, post-production, or blocker-gate records into live Jellyfish `generation_tasks` and `generation_task_links`. |
| Phase 10 | Done | Added persisted CineForge workflow-state load/edit/regenerate APIs and Film Core tab controls; edits and targeted regeneration requests are versioned and written to the Jellyfish task ledger. |
| Phase 11 | Done | Added text-to-drama intake, per-stage automatic/manual switches, stage completion gates, and generic cinematic runtime provider registry/config views. |
| Phase 12 | Done | Upgraded text-to-drama from shot seeding to generated novel chapters, episode scripts, storyboard details, character/actor/costume/scene/prop assets, VFX notes, frame slots, role web reference-harvest tasks, creation-entry semantics, and a Film Core shooting gate that blocks render queues until prerequisites exist. |
| Product Follow-up | Next | Bind provider/runtime workers to execute those task records and attach real generated media, QA reports, retry outcomes, and exports. |

The starter-kit nine implementation phases are complete. Their evidence is
available in the Jellyfish `Film Core` tab through the
`implementation_status` and `implementation_phases` overview fields.

---

## 8. Engineering Rules

Do:

- keep Jellyfish as the studio platform boundary
- keep Film Core provider-agnostic
- compile prompts from structured DSL and state
- store continuity as data, not prose
- use QA output as machine-readable retry input
- make runtime providers replaceable
- preserve edit/regenerate history as versioned workflow data

Do not:

- hardcode final prompts into workflow code
- put runtime API calls inside Director DSL or Film State
- make one model provider own the architecture
- bury continuity in natural-language prompt fragments
- replace Jellyfish UI before the Film Core contracts are stable

---

## 9. Acceptance Criteria

The Jellyfish-based LuminAI platform is acceptable when:

- a Jellyfish project/chapter/shot can map into Film Core without schema leakage
- a shot can compile from structured director data plus continuity state
- a runtime request can route to Wan/Kling/Vidu/Veo-style adapters
- QA failures produce structured repair hints
- retry decisions patch prompts and parameters without manual prompt rewriting
- batch production can process multiple chapters with shared assets and state
- workflow stages can be edited or regenerated without resetting approved
  project state
- generated media writes back to the platform as reusable references
- the local Studio Dashboard can start and expose health, stage evidence,
  Jellyfish base status, QA failures, retry requests, and a closed-loop demo
  plan without provider credentials
- the existing Jellyfish Project Workbench exposes Film Core pipeline state,
  consistency health, QA/retry readiness, and closed-loop plan preview without
  launching a separate UI
