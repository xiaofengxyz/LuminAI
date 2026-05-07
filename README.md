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
133 passed
```

## Development Direction

The current implementation establishes the backend foundation. Product work
should use Jellyfish as the studio OS / workflow base, then attach LuminAI Film
Core as the continuity, prompt, QA, retry, and runtime abstraction layer.

Reference docs:

- `docs/jellyfish_base_integration_blueprint.md`
- `docs/project_function_manual.md`

Next product layers should build on these systems instead of bypassing them:

1. Character asset registry with references, outfits, voices, embeddings, and
   identity QA metrics.
2. Director DSL and shot graph templates for controllable camera language.
3. Film state continuity across episodes and batches.
4. Runtime adapters for additional providers without changing the film core.
5. QA-driven retry loops before final editing and delivery.
