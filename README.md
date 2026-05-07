# LuminAI

LuminAI is an industrial AI manju / AI film engine foundation.

It is designed for repeatable content production rather than one-off prompt
demos:

- Jellyfish-style studio platform bridge for project/chapter/shot/asset/task
  workflows
- graph-driven episode workflows
- ECS-inspired asset and state primitives
- character, scene, prop, and shot continuity
- prompt compiler architecture
- runtime abstraction for Wan/DashScope, Kling, Vidu, and future providers
- automatic QA, retry planning, and batch production scaffolding

## Repository Layout

```text
src/apps/comic_gen/     Series, episode, asset, prompt, and video-task pipeline
src/film_engine/        Reusable graph/ECS/state/compiler/QA/retry/batch systems
src/film_engine/platform.py
                        Jellyfish-style studio OS bridge
src/models/             Runtime adapters for Wanx, Kling, Vidu, and Wan image refs
src/utils/              Provider registry, media reference resolver, OSS facade
docs/                   Research, execution plan, architecture notes
samples/                Reusable workflow and asset examples
tests/                  Contract tests for pipeline and provider behavior
```

## Current Verification

```bash
python3 -m pytest -q -s
```

Expected result:

```text
135 passed
```

## Run The Project

Start the dependency-light LuminAI runtime server:

```bash
python3 -m src.film_engine.server --host 127.0.0.1 --port 8765
```

Smoke endpoints:

```text
GET http://127.0.0.1:8765/health
GET http://127.0.0.1:8765/demo/closed-loop-plan
```

For a one-shot CLI run of the closed-loop demo plan:

```bash
python3 -m src.film_engine.demo
```

## Development Direction

The current implementation establishes the backend foundation. Product work
should use Jellyfish as the studio OS / workflow base, then attach LuminAI Film
Core as the continuity, prompt, QA, retry, and runtime abstraction layer.

Reference docs:

- `docs/jellyfish_base_integration_blueprint.md`
- `docs/project_function_manual.md`

Next product layers should build on these systems instead of bypassing them:

1. Bind the bridge to a real Jellyfish fork/API client.
2. Write approved outputs, QA reports, retry outcomes, and post-production
   results back into Jellyfish media/task/shot records.
3. Expose closed-loop QA, retry, post-production, and batch controls in the
   studio UI.
4. Add provider-specific workers that execute `RenderRequest` and
   `PostProductionStep` records while keeping Film Core runtime-neutral.
