# System Architecture

## Core Components

- Jellyfish-style AI Studio OS / Workflow Core Bridge
- Jellyfish upstream base checkout and run-status inspector
- Local Studio Dashboard for stage evidence, QA, retry, and base status
- ECS-inspired Entity System
- Graph-driven Workflow Engine
- State-centric Data Management
- Persisted CineForge Workflow State Ledger
- Text-To-Drama Intake Ledger
- Runtime Abstraction Layer
- Post-production Runtime Planner
- Director Consistency Layer
- Compiler Architecture for Prompts
- Modular System Design
- QA Engine and Retry Engine
- Batch Planner for industrial production

## Data Flow

Source Text → Text-To-Drama Intake → Generated Novel → Episode Scripts → Asset Bible / Reference Harvest → Jellyfish Project/Chapter/Shot Workspace → Story Graph → Director Planner → Film Core Shooting Gate → Prompt Compiler → Runtime Adapter → Render Runtime → Video Models → QA Engine → Retry Engine → Final Editing

## Implemented Foundation

| Layer | Module | Responsibility |
| --- | --- | --- |
| Application | `src/apps/comic_gen` | Series, episodes, assets, prompt fallback, media snapshots, provider routing. |
| Platform Bridge | `src/film_engine/platform.py` | Jellyfish-style Project/Chapter/Shot/Asset/Task contracts mapped into Film Core objects. |
| Jellyfish Base | `vendor/jellyfish`, `src/film_engine/jellyfish_base.py` | Upstream Jellyfish Studio OS submodule plus base status, run commands, ports, and missing-file checks. |
| Studio Dashboard | `src/film_engine/studio.py`, `src/film_engine/server.py` | Local dependency-light UI and status APIs for stage completion, shot QA, retry, and Jellyfish base readiness. |
| Film Core | `src/film_engine` | ECS entities, workflow graph, film state, prompt compiler, QA, retry, batch planning. |
| Director Consistency | `src/film_engine/director.py` | Director DSL validation, character bibles, scene bibles, continuity preparation, and prompt-context handoff. |
| Post-production | `src/film_engine/post_production.py` | Runtime-neutral TTS, subtitle, FFmpeg compose, concat, and final export planning. |
| Runtime | `src/models` | Wanx/DashScope, Kling vendor, Vidu vendor, and Wan image reference adapters. |
| Utilities | `src/utils` | Media ref classification, local/OSS resolution, provider family registry. |

## Jellyfish Base Direction

Jellyfish is the target Studio OS / Workflow Core. It should own project,
chapter, shot preparation, asset confirmation, media management, task tracking,
OpenAPI contracts, and studio UI.

LuminAI Film Core should attach below that platform boundary and own continuity,
Director DSL, prompt compilation, runtime abstraction, QA, retry, and batch
production. The bridge keeps the fork/API schema replaceable.

The tracked upstream base lives at `vendor/jellyfish`. LuminAI still exposes a
small local dashboard for run-readiness, and the production-facing Film Core
overview now lives inside Jellyfish through `/api/v1/film/industrial/...` and
the Project Workbench `Film Core` tab. The same tab surfaces both the starter-kit
`9/9` implementation completion evidence and the 11-node industrial production
pipeline, and it can write queueable render/QA/retry/post-production task
records into Jellyfish `generation_tasks` and `generation_task_links`.

The CineForge workflow ledger persists the nine Prompt-derived stages inside
Jellyfish with `cineforge_workflow_states`. Operators can edit a single stage,
increment the workflow version, and queue stage-specific regeneration tasks.
Those mutation events also reuse `generation_tasks` and `generation_task_links`,
so edit/regenerate history is recoverable through the existing task center
instead of a parallel runtime.

Each CineForge stage now carries an explicit `execution_mode` switch. In
`automatic` mode, completing a stage records the output and activates the next
stage. In `manual` mode, completion records `waiting_operator` so a producer can
review, edit, or regenerate before the graph advances. The
`/api/v1/film/industrial/text-to-drama` endpoint creates a Jellyfish project,
generated novel chapters, per-episode script outlines, storyboard shots,
character/actor/costume/scene/prop assets, VFX notes, frame slots, role web
reference-harvest tasks, workflow state, and task-ledger entries from one source
text input. Film Core then exposes a `shooting_gate`; render queues stay empty
until script, shot graph, characters, identity references, scenes, props,
costumes, shot details, and ready shots exist.

Model execution stays behind the Jellyfish provider/model adapter boundary:
providers store `base_url`, optional image/video base URL overrides, and
`api_key`/`api_secret`; runtime config APIs expose only the resolved adapter,
base URL, and key-present flags. Built-in registry keys include OpenAI,
Volcengine, ComfyUI, FLUX, SDXL, StoryDiffusion, Kling, Seedance, Veo, Wan2.1,
Sora, and Vidu, while concrete workers remain replaceable modules.

## Key Principles

- Modularity: Each component is independent and reusable
- Abstraction: Runtime details are abstracted away
- State Management: All state is explicitly managed
- Graph-based: Workflow is represented as graphs
- Compilation: Prompts are compiled from structured data
- Continuity: Character, outfit, lighting, and timeline state are explicit
- Retryability: QA failures become structured retry decisions
- Editability: workflow stages can be patched or regenerated without resetting
  approved project state
- Controllability: automatic stages advance through the graph, while manual
  stages halt with recoverable `waiting_operator` state
