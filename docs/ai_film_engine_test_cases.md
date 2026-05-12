# AI Film Engine Test Cases

> Scope: Jellyfish base, Studio Dashboard, Film Core planning, QA/retry, and
> local run readiness.

## 1. Jellyfish Base Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| Submodule metadata exists | `git submodule status vendor/jellyfish` | A pinned Jellyfish commit is shown. |
| Base shape is inspectable | `python3 -m src.film_engine.jellyfish_base` | JSON includes upstream URL, path, run commands, ports, and missing list. |
| Compose file validates | `docker compose --env-file deploy/compose/.env.example -f deploy/compose/docker-compose.yml config -q` from `vendor/jellyfish` | Command exits with code 0. |
| Unit contract | `python3 -m pytest -q -s tests/test_jellyfish_base_status.py` | Synthetic Jellyfish shape and stage evidence tests pass. |

## 2. Studio Dashboard Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| UI route | `GET /` | HTML contains `LuminAI Studio Dashboard`, `Stage Index`, and `Shot Workbench`. |
| Studio status API | `GET /api/studio/status` | JSON includes summary, stages, Jellyfish status, review, and actions. |
| Jellyfish status API | `GET /api/jellyfish/base-status` | JSON includes `https://github.com/Forget-C/Jellyfish`. |
| Unit contract | `python3 -m pytest -q -s tests/test_luminai_runtime_entrypoint.py` | Health, plan, UI, and API route tests pass. |

## 3. Closed-Loop Film Core Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| Demo plan summary | `python3 -m src.film_engine.demo --compact` | JSON includes workflow, render requests, retry requests, QA state, and post-production plan. |
| Planner unit tests | `python3 -m pytest -q -s tests/test_closed_loop_production.py` | Closed-loop planning contract passes. |
| Director consistency | `python3 -m pytest -q -s tests/test_director_consistency.py` | Character and scene bible continuity is prepared before prompt compilation. |
| Post production | `python3 -m pytest -q -s tests/test_post_production_planner.py` | TTS, subtitle, FFmpeg compose, concat, and export steps are planned. |

## 4. Jellyfish-Native Industrial Film Core Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| Industrial service contract | `python3 -m pytest -q -s tests/test_jellyfish_industrial_film_core.py` | Overview maps Jellyfish state into all 11 pipeline stages, exposes 9/9 starter-kit implementation phases, plan exposes render/QA/retry/post contracts, and CineForge workflow state exposes persisted edit/regenerate/automation contracts. |
| Workflow state backend contract | `.venv/bin/python -m pytest -q -s tests/test_industrial_workflow_state.py` from `vendor/jellyfish/backend` | Persisted `CineForgeWorkflowState` initializes nine stages; editing creates a succeeded workflow-edit task; regenerating creates a pending stage-regenerate task; completing a stage either auto-activates the next stage or stops with `waiting_operator`; text-to-drama creates project/chapters/shots/workflow tasks. |
| Backend route import | `PYTHONPATH=. .venv/bin/python -c "from app.api.v1.routes.film.industrial import router; print(len(router.routes))"` from `vendor/jellyfish/backend` | Prints `8`, covering text-to-drama, overview, workflow-state load/edit/regenerate/complete, plan, and run endpoints. |
| Frontend type safety | `npx pnpm@9.15.9 run typecheck` from `vendor/jellyfish/front` | Project Workbench `Film Core` tab, OpenAPI generated client wrapper, text-to-drama entry, workflow-state automation controls, and generated types typecheck. |
| Manual UI smoke | Open `/projects/{projectId}?tab=filmCore` in Jellyfish frontend | Film Core tab shows `九阶段交付状态`, persisted `CineForge 可编辑工作流状态`, automatic/manual stage switch, complete/regenerate/edit buttons, 11-node production pipeline, consistency health, pain-point diagnosis, plan button, and reference project breakdown inside the existing Jellyfish workbench. |
| Text-to-drama UI smoke | Open `http://localhost:7790/projects`, click `文本生成漫剧` | A source text can create a project, multiple chapters, shot seeds, workflow state, and task-ledger entries, then navigate to `/projects/{projectId}?tab=filmCore`. |
| Reboot service recovery | Run `scripts/start_jellyfish_film_core.sh` or start backend with `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8011`, then start frontend with `VITE_BACKEND_URL=http://127.0.0.1:8011 npx pnpm@9.15.9 run dev:film-core` | `/health` returns 200 with `curl --noproxy '*'`, `http://localhost:7790/projects` returns the Vite HTML shell, and the Film Core/text-to-drama toolbar buttons remain discoverable even when the project list is empty. |
| CORS and runtime backend | `python3 -m pytest -q -s tests/test_jellyfish_cors_runtime_config.py` | Frontend runtime defaults to Jellyfish backend `8011`; `/api/v1/studio/projects` and `/api/v1/film/tasks?recent_seconds=15&page=1&page_size=50` return CORS headers for local frontend port `7790`. |
| Industrial run writeback | `POST /api/v1/film/industrial/projects/{projectId}/run` | Creates Jellyfish `generation_tasks` and `generation_task_links` for render, QA, retry, post-production, or a blocker gate task. |
| Jellyfish backend regression | `.venv/bin/python -m pytest -q -s` from `vendor/jellyfish/backend` | Full backend suite passes, including CORS middleware, Studio APIs, task center, response envelopes, and video capability mapping. |

## 5. Provider And Runtime Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| Provider registry | `python3 -m pytest -q -s tests/test_provider_registry.py` | Runtime families stay behind the registry boundary. |
| Media refs | `python3 -m pytest -q -s tests/test_media_refs.py tests/test_provider_media.py` | Local, URL, and OSS media modes resolve deterministically. |
| Kling routing | `python3 -m pytest -q -s tests/test_kling_provider_routing.py` | Kling requests are routed without leaking story logic into the provider. |
| Vidu routing | `python3 -m pytest -q -s tests/test_vidu_provider_routing.py` | Vidu requests preserve runtime adapter contracts. |
| Jellyfish runtime model config | `.venv/bin/python -m pytest -q -s tests/test_llm_manage.py` from `vendor/jellyfish/backend` | Provider registry includes cinematic runtime gateways; model runtime config resolves category-specific base URL and key-configured state without leaking secrets. |

## 6. Full Regression

Run:

```bash
python3 -m pytest -q -s
```

Expected:

```text
All tests pass.
```

## 7. Manual Smoke Run

Start LuminAI:

```bash
python3 -m src.film_engine.server --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

Check:

- stage index renders nine workflow stages
- shot workbench renders two demo render requests
- one retry request is visible through the failed shot
- Jellyfish base panel shows path, commit, ports, and Docker command
- `npx pnpm@9.15.9 run dev:film-core` serves the Jellyfish UI at
  `http://localhost:7790/projects`
- Jellyfish project cards, preview side panel, and workbench header expose direct
  Film Core entry points
- Empty project lists still expose a Film Core button that opens project
  creation first, because Film Core overview needs a project id
- Jellyfish Project Workbench `Film Core` tab renders 9/9 implementation
  phases plus the industrial production pipeline inside the existing Jellyfish UI
- `CineForge 可编辑工作流状态` renders nine persisted stages; saving a stage
  edit creates a `cineforge_workflow_edit` ledger task and stage regeneration
  creates a `cineforge_stage_regenerate` ledger task
- The stage switch can set `automatic` or `manual`; completing an automatic
  stage activates the next stage, and completing a manual stage records
  `waiting_operator`
- The project list `文本生成漫剧` entry creates multiple chapters and ready shot
  seeds from one text input, then opens Film Core
- Clicking `创建生产任务` writes industrial task records into the Jellyfish task
  center; projects without ready shots get an `industrial_gate` blocker record

## 8. Current Known Limits

- Demo QA metrics are deterministic test metrics, not real CV detectors.
- Real provider rendering requires credentials and worker binding.
- Jellyfish now has native Film Core overview, text-to-drama intake, plan
  preview, and task writeback endpoints plus persisted workflow-state
  edit/regenerate/complete endpoints. Actual
  provider media files and production CV/CLIP/face/outfit QA detectors still
  require provider/runtime worker integration.
- In an earlier session, Jellyfish Docker Compose full-stack startup was blocked by a
  Debian apt mirror `502/404` during backend image build. The verified fallback
  local run path is SQLite backend on port 8011 plus `dev:film-core` frontend on
  port 7790.
