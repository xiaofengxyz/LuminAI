# System Architecture

## Core Components

- Jellyfish-style AI Studio OS / Workflow Core Bridge
- ECS-inspired Entity System
- Graph-driven Workflow Engine
- State-centric Data Management
- Runtime Abstraction Layer
- Post-production Runtime Planner
- Director Consistency Layer
- Compiler Architecture for Prompts
- Modular System Design
- QA Engine and Retry Engine
- Batch Planner for industrial production

## Data Flow

Novel/Script → Jellyfish Project/Chapter/Shot Workspace → LuminAI Platform Bridge → Story Graph → Director Planner → Film Core → Prompt Compiler → Runtime Adapter → Render Runtime → Video Models → QA Engine → Retry Engine → Final Editing

## Implemented Foundation

| Layer | Module | Responsibility |
| --- | --- | --- |
| Application | `src/apps/comic_gen` | Series, episodes, assets, prompt fallback, media snapshots, provider routing. |
| Platform Bridge | `src/film_engine/platform.py` | Jellyfish-style Project/Chapter/Shot/Asset/Task contracts mapped into Film Core objects. |
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

## Key Principles

- Modularity: Each component is independent and reusable
- Abstraction: Runtime details are abstracted away
- State Management: All state is explicitly managed
- Graph-based: Workflow is represented as graphs
- Compilation: Prompts are compiled from structured data
- Continuity: Character, outfit, lighting, and timeline state are explicit
- Retryability: QA failures become structured retry decisions
