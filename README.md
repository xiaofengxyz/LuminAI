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
- a dependency-light Studio Dashboard for run readiness, stage evidence, QA,
  retry, and Jellyfish base status

## Repository Layout

```text
src/apps/comic_gen/     Series, episode, asset, prompt, and video-task pipeline
src/film_engine/        Reusable graph/ECS/state/compiler/QA/retry/batch systems
src/film_engine/platform.py
                        Jellyfish-style studio OS bridge
src/film_engine/jellyfish_base.py
                        Real Jellyfish upstream base inspection and run commands
src/film_engine/studio.py
                        Local Studio Dashboard payload and HTML renderer
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
All tests pass.
```

## Run The Project

Start the dependency-light LuminAI runtime server and Studio Dashboard:

```bash
python3 -m src.film_engine.server --host 127.0.0.1 --port 8765
```

Open the UI:

```text
http://127.0.0.1:8765/
```

Smoke endpoints:

```text
GET http://127.0.0.1:8765/health
GET http://127.0.0.1:8765/api/studio/status
GET http://127.0.0.1:8765/api/jellyfish/base-status
GET http://127.0.0.1:8765/demo/closed-loop-plan
```

For a one-shot CLI run of the closed-loop demo plan:

```bash
python3 -m src.film_engine.demo
```

## Jellyfish Base

Jellyfish is tracked as the Studio OS / workflow base:

```bash
git submodule update --init --recursive
python3 -m src.film_engine.jellyfish_base
```

The submodule is based on upstream `https://github.com/Forget-C/Jellyfish` and
is hosted on the LuminAI `vendor-jellyfish-industrial-film-core` branch so this
repo can carry Jellyfish-native Film Core changes without requiring write access
to the upstream project.

Run the Jellyfish Docker stack when local ports are free, or use the included
port overrides:

```bash
cd vendor/jellyfish
MYSQL_PORT=3337 REDIS_PORT=6384 RUSTFS_PORT=9010 RUSTFS_CONSOLE_PORT=9011 \
docker compose --env-file deploy/compose/.env.example \
  -f deploy/compose/docker-compose.yml up -d --build
```

Expected Jellyfish URLs:

```text
Frontend: http://localhost:7788
Backend:  http://localhost:8000
Docs:     http://localhost:8000/docs
```

## Development Direction

The current implementation uses Jellyfish as the studio OS / workflow base and
adds a native Project Workbench `Film Core` tab plus industrial Film Core APIs
for continuity, prompt, QA, retry, and runtime abstraction planning.

Reference docs:

- `docs/jellyfish_base_integration_blueprint.md`
- `docs/project_function_manual.md`
- `docs/industrial_ai_film_engine_review_2026.md`
- `docs/ai_film_engine_test_cases.md`

Next product layers should build on these systems instead of bypassing them:

1. Write approved outputs, QA reports, retry outcomes, and post-production
   results back into Jellyfish media/task/shot records.
2. Add provider-specific workers that execute `RenderRequest` and
   `PostProductionStep` records while keeping Film Core runtime-neutral.
