# AI Manju Engine Execution Plan

This plan converts the research report into an implementation path for LuminAI.

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
| Phase 5 | Documentation, samples, tests, cleanup, commit, and push. |

## Non-Goals For This Pass

- No giant monolith.
- No hardcoded final cinematic prompts.
- No direct dependency on one runtime provider.
- No UI build until the backend foundation is stable.
