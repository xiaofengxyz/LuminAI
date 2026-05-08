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
| Industrial service contract | `python3 -m pytest -q -s tests/test_jellyfish_industrial_film_core.py` | Overview maps Jellyfish state into all 11 pipeline stages and plan exposes render, QA, retry, and post-production contracts. |
| Backend route import | `PYTHONPATH=. .venv/bin/python -c "from app.api.v1.routes.film.industrial import router; print(len(router.routes))"` from `vendor/jellyfish/backend` | Prints `2`, covering overview and plan endpoints. |
| Frontend type safety | `npx pnpm@9.15.9 run typecheck` from `vendor/jellyfish/front` | Project Workbench `Film Core` tab, manual service client, and mock handlers typecheck. |
| Manual UI smoke | Open `/projects/{projectId}?tab=filmCore` in Jellyfish frontend | Film Core tab shows stage index, consistency health, pain-point diagnosis, plan button, and reference project breakdown inside the existing Jellyfish workbench. |

## 5. Provider And Runtime Tests

| Case | Command / Test | Expected result |
| --- | --- | --- |
| Provider registry | `python3 -m pytest -q -s tests/test_provider_registry.py` | Runtime families stay behind the registry boundary. |
| Media refs | `python3 -m pytest -q -s tests/test_media_refs.py tests/test_provider_media.py` | Local, URL, and OSS media modes resolve deterministically. |
| Kling routing | `python3 -m pytest -q -s tests/test_kling_provider_routing.py` | Kling requests are routed without leaking story logic into the provider. |
| Vidu routing | `python3 -m pytest -q -s tests/test_vidu_provider_routing.py` | Vidu requests preserve runtime adapter contracts. |

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
- Jellyfish Project Workbench `Film Core` tab renders the industrial pipeline
  inside the existing Jellyfish UI

## 8. Current Known Limits

- Demo QA metrics are deterministic test metrics, not real CV detectors.
- Real provider rendering requires credentials and worker binding.
- Jellyfish now has native Film Core overview and plan preview endpoints; live
  DB/API writeback for generated media, QA reports, retry decisions, and
  post-production outputs is the next product integration step.
- In this session, Jellyfish Docker Compose full-stack startup was blocked by a
  Debian apt mirror `502/404` during backend image build. The verified fallback
  run path is `uv` SQLite backend on port 8000 plus the built frontend image on
  port 7788.
