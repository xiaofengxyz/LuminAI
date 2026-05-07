# QA, Retry, and Batch Workflow

This workflow turns generation from random sampling into a controllable
production loop.

## Batch Graph

`BatchPlanner` builds a graph per series:

```text
story_graph -> director_planner -> film_state -> prompt_compiler
-> runtime_adapter -> qa_engine -> retry_engine -> final_editing
```

Every episode node carries `series_id` and `episode_id`, so downstream systems
can resolve shared characters, scene assets, prompt config, and continuity
state.

## QA Contract

`RuleBasedQAEngine` accepts metrics and thresholds. The default checks are:

- `face_similarity`
- `outfit_similarity`
- `clip_score`

The engine returns a `QAReport` with structured `QAIssue` items. These issues
are machine-readable repair inputs, not prose-only notes.

## Retry Contract

`RetryEngine` converts a failed `QAReport` into a `RetryDecision`:

- whether to retry
- next attempt number
- prompt patches
- parameter patches
- reason

Face drift raises `reference_strength` to `high`, while all repair hints are
kept as prompt patches for the next compiled prompt.

## Runtime Boundary

Runtime adapters receive a compiled render request and return a render result.
They do not own story logic, continuity, or QA policy. This keeps Kling, Wan,
Vidu, Veo-style providers replaceable.

## Closed Loop Planner

`ClosedLoopProductionPlanner` wires the backend contracts into one repeatable
chapter plan:

```text
StudioShot
-> ShotContinuityState
-> DirectorConsistencyEngine
-> PromptCompiler
-> RenderRequest
-> RuleBasedQAEngine
-> RetryEngine
-> optional PostProductionPlanner
```

The planner returns:

- render requests for first-pass generation
- QA reports per shot
- retry requests with prompt and parameter patches
- optional TTS/subtitle/FFmpeg/export post-production plan

This is the backend closure before a Jellyfish UI button or task worker binds
the plan to real execution.
