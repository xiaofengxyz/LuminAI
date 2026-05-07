# System Architecture

## Core Components

- ECS-inspired Entity System
- Graph-driven Workflow Engine
- State-centric Data Management
- Runtime Abstraction Layer
- Compiler Architecture for Prompts
- Modular System Design
- QA Engine and Retry Engine
- Batch Planner for industrial production

## Data Flow

Novel/Script → Story Graph → Director Planner → Film Core → Prompt Compiler → Runtime Adapter → Render Runtime → Video Models → QA Engine → Retry Engine → Final Editing

## Implemented Foundation

| Layer | Module | Responsibility |
| --- | --- | --- |
| Application | `src/apps/comic_gen` | Series, episodes, assets, prompt fallback, media snapshots, provider routing. |
| Film Core | `src/film_engine` | ECS entities, workflow graph, film state, prompt compiler, QA, retry, batch planning. |
| Runtime | `src/models` | Wanx/DashScope, Kling vendor, Vidu vendor, and Wan image reference adapters. |
| Utilities | `src/utils` | Media ref classification, local/OSS resolution, provider family registry. |

## Key Principles

- Modularity: Each component is independent and reusable
- Abstraction: Runtime details are abstracted away
- State Management: All state is explicitly managed
- Graph-based: Workflow is represented as graphs
- Compilation: Prompts are compiled from structured data
- Continuity: Character, outfit, lighting, and timeline state are explicit
- Retryability: QA failures become structured retry decisions
