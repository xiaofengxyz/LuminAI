from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.film_engine.demo import build_demo_plan_summary
from src.film_engine.jellyfish_base import JellyfishBaseStatus, inspect_jellyfish_base
from src.film_engine.platform import JELLYFISH_FILM_WORKFLOW


@dataclass
class StudioStage:
    id: str
    label: str
    status: str
    evidence: str
    owner: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "evidence": self.evidence,
            "owner": self.owner,
        }


@dataclass
class IndustrialReviewItem:
    pain_point: str
    production_answer: str
    implementation: str
    status: str
    reference: str

    def as_dict(self) -> dict[str, str]:
        return {
            "pain_point": self.pain_point,
            "production_answer": self.production_answer,
            "implementation": self.implementation,
            "status": self.status,
            "reference": self.reference,
        }


@dataclass
class StudioDashboardPayload:
    summary: dict[str, Any]
    stages: list[StudioStage]
    jellyfish: JellyfishBaseStatus
    review: list[IndustrialReviewItem] = field(default_factory=list)
    actions: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "stages": [stage.as_dict() for stage in self.stages],
            "jellyfish": self.jellyfish.as_dict(),
            "review": [item.as_dict() for item in self.review],
            "actions": list(self.actions),
        }


def build_studio_dashboard_payload() -> StudioDashboardPayload:
    summary = build_demo_plan_summary()
    jellyfish = inspect_jellyfish_base()
    return StudioDashboardPayload(
        summary=summary,
        stages=build_stage_index(summary),
        jellyfish=jellyfish,
        review=build_industrial_review(jellyfish),
        actions=_build_actions(jellyfish),
    )


def build_stage_index(summary: Mapping[str, Any]) -> list[StudioStage]:
    workflow = set(_as_list(summary.get("workflow")))
    metadata = _as_mapping(summary.get("metadata"))
    qa = _as_mapping(summary.get("qa"))
    post = _as_mapping(summary.get("post_production"))
    render_requests = _as_list(summary.get("render_requests"))
    retry_requests = _as_list(summary.get("retry_requests"))

    stage_evidence = {
        "script_breakdown": (
            bool(summary.get("project") and summary.get("chapter")),
            "Project and chapter contract is present.",
        ),
        "shot_preparation": (
            int(metadata.get("shot_count", 0) or 0) > 0,
            f"{metadata.get('shot_count', 0)} generation-ready shots planned.",
        ),
        "asset_consistency": (
            any(_as_mapping(item).get("references") for item in render_requests),
            "Render requests include continuity references.",
        ),
        "film_state": (
            any("outfits=" in str(_as_mapping(item).get("prompt", "")) for item in render_requests),
            "Compiled prompts carry outfit and timeline continuity state.",
        ),
        "prompt_compiler": (
            bool(render_requests),
            f"{len(render_requests)} provider-neutral render requests compiled.",
        ),
        "runtime_adapter": (
            any(_as_mapping(item).get("model") for item in render_requests),
            "Runtime model and provider parameters remain at adapter boundary.",
        ),
        "qa_engine": (
            "passed" in qa,
            f"QA evaluated with passed={qa.get('passed')}.",
        ),
        "retry_engine": (
            "retry_count" in metadata,
            f"{metadata.get('retry_count', 0)} retry requests prepared.",
        ),
        "final_export": (
            bool(post.get("enabled")),
            f"Post-production enabled={post.get('enabled', False)}.",
        ),
    }
    owners = {
        "script_breakdown": "Jellyfish",
        "shot_preparation": "Jellyfish",
        "asset_consistency": "Jellyfish + LuminAI",
        "film_state": "LuminAI Film Core",
        "prompt_compiler": "LuminAI Film Core",
        "runtime_adapter": "LuminAI Runtime",
        "qa_engine": "LuminAI QA",
        "retry_engine": "LuminAI Retry",
        "final_export": "Post Production",
    }
    labels = {
        "script_breakdown": "Script Breakdown",
        "shot_preparation": "Shot Preparation",
        "asset_consistency": "Asset Consistency",
        "film_state": "Film State",
        "prompt_compiler": "Prompt Compiler",
        "runtime_adapter": "Runtime Adapter",
        "qa_engine": "QA Engine",
        "retry_engine": "Retry Engine",
        "final_export": "Final Export",
    }
    stages = []
    for stage_id in JELLYFISH_FILM_WORKFLOW:
        available, evidence = stage_evidence.get(stage_id, (stage_id in workflow, "Workflow node present."))
        status = "done" if available and stage_id in workflow else "blocked"
        stages.append(
            StudioStage(
                id=stage_id,
                label=labels.get(stage_id, stage_id.replace("_", " ").title()),
                status=status,
                evidence=evidence,
                owner=owners.get(stage_id, "LuminAI"),
            )
        )
    return stages


def build_industrial_review(jellyfish: JellyfishBaseStatus) -> list[IndustrialReviewItem]:
    base_status = "done" if jellyfish.available else "blocked"
    return [
        IndustrialReviewItem(
            pain_point="No operable studio base",
            production_answer="Use Jellyfish as the project, chapter, shot, asset, task, media, and UI workbench.",
            implementation="Tracked upstream Jellyfish as vendor/jellyfish and exposed base status plus run commands.",
            status=base_status,
            reference="Jellyfish",
        ),
        IndustrialReviewItem(
            pain_point="Character and outfit drift",
            production_answer="Treat identity, outfit, voice, and references as locked production assets before generation.",
            implementation="CharacterBible, SceneBible, shot continuity state, reference media propagation, and negative terms.",
            status="done",
            reference="StoryDiffusion + Jellyfish",
        ),
        IndustrialReviewItem(
            pain_point="Shot continuity breaks between cuts",
            production_answer="Make every shot a graph node with explicit timeline, scene, lighting, camera, and dialogue state.",
            implementation="Jellyfish workflow bridge, WorkflowGraph, FilmState, DirectorConsistencyEngine, and compiled prompts.",
            status="done",
            reference="director_ai + ComfyUI",
        ),
        IndustrialReviewItem(
            pain_point="Prompt randomness",
            production_answer="Compile prompts from structured director DSL and continuity state instead of hand-written strings.",
            implementation="PromptCompiler produces provider-neutral text, references, negatives, and runtime parameters.",
            status="done",
            reference="director_ai",
        ),
        IndustrialReviewItem(
            pain_point="Vendor lock-in",
            production_answer="Keep model providers behind runtime adapters and store all render intent as RenderRequest records.",
            implementation="Runtime abstraction supports Wanx, Kling, Vidu, image refs, and future providers.",
            status="done",
            reference="huobao-drama + DiffSynth Studio",
        ),
        IndustrialReviewItem(
            pain_point="Manual QA and repeated bad renders",
            production_answer="Convert visual QA failures into structured retry decisions and patched render requests.",
            implementation="RuleBasedQAEngine, RetryEngine, retry_count metadata, and UI-visible failed shot evidence.",
            status="done",
            reference="MoneyPrinterTurbo + industrial QA patterns",
        ),
        IndustrialReviewItem(
            pain_point="No final-editing closure",
            production_answer="Plan voice, subtitles, FFmpeg composition, concat, and export under the same runtime boundary.",
            implementation="PostProductionPlanner builds runtime-neutral final export steps from approved render results.",
            status="done",
            reference="huobao-drama",
        ),
    ]


def render_studio_dashboard(payload: StudioDashboardPayload | Mapping[str, Any]) -> str:
    data = payload.as_dict() if isinstance(payload, StudioDashboardPayload) else dict(payload)
    embedded = json.dumps(data, sort_keys=True).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LuminAI Studio Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #19212a;
      --muted: #637083;
      --line: #d9e1ea;
      --panel: #ffffff;
      --bg: #f5f7fa;
      --accent: #0b6fcb;
      --ok: #1f8a4c;
      --warn: #b45b00;
      --bad: #b3261e;
      --soft: #eaf2fb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    button, a.button {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 6px;
      padding: 9px 12px;
      font: inherit;
      cursor: pointer;
      text-decoration: none;
      min-height: 38px;
    }}
    button.primary, a.primary {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .shell {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 18px;
    }}
    h1 {{
      font-size: 30px;
      line-height: 1.15;
      margin: 0 0 8px;
      letter-spacing: 0;
    }}
    h2 {{
      font-size: 16px;
      line-height: 1.3;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    .subtitle {{
      color: var(--muted);
      max-width: 780px;
      line-height: 1.5;
      margin: 0;
    }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(260px, 0.9fr) minmax(420px, 1.6fr) minmax(320px, 1fr);
      gap: 16px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }}
    .metric-row {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 84px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .metric strong {{
      font-size: 24px;
      letter-spacing: 0;
    }}
    .stage {{
      display: grid;
      grid-template-columns: 26px minmax(0, 1fr);
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
    }}
    .stage:last-child {{ border-bottom: 0; }}
    .dot {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      margin-top: 2px;
      background: var(--bad);
      border: 3px solid #fff;
      box-shadow: 0 0 0 1px var(--line);
    }}
    .dot.done {{ background: var(--ok); }}
    .stage-title {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: baseline;
      font-weight: 700;
      line-height: 1.2;
    }}
    .stage-owner, .muted {{
      color: var(--muted);
      font-size: 12px;
    }}
    .evidence {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      margin-top: 5px;
    }}
    .shot {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      background: #fbfcfe;
    }}
    .shot-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
    }}
    .shot-title {{
      font-weight: 700;
      line-height: 1.25;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      line-height: 1.3;
      background: var(--soft);
      color: var(--accent);
      white-space: nowrap;
    }}
    .chip.warn {{
      background: #fff1df;
      color: var(--warn);
    }}
    .chip.ok {{
      background: #e5f5eb;
      color: var(--ok);
    }}
    code, pre {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 12px;
    }}
    pre {{
      overflow: auto;
      white-space: pre-wrap;
      background: #111923;
      color: #eff6ff;
      border-radius: 8px;
      padding: 12px;
      max-height: 260px;
    }}
    .review-item {{
      border-top: 1px solid var(--line);
      padding: 12px 0;
    }}
    .review-item:first-child {{ border-top: 0; padding-top: 0; }}
    .review-title {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .review-copy {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 4px 0;
    }}
    .base-list {{
      display: grid;
      gap: 8px;
      margin: 0 0 12px;
    }}
    .base-row {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 8px;
      min-width: 0;
    }}
    .base-row span:last-child {{
      text-align: right;
      overflow-wrap: anywhere;
    }}
    @media (max-width: 1120px) {{
      .grid {{ grid-template-columns: 1fr 1fr; }}
      .grid .panel:last-child {{ grid-column: 1 / -1; }}
      .metric-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 760px) {{
      .shell {{ padding: 16px; }}
      .topbar {{ display: block; }}
      .actions {{ justify-content: flex-start; margin-top: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .metric-row {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 24px; }}
      .shot-head, .review-title, .base-row {{ display: block; }}
      .chip {{ margin-top: 6px; }}
    }}
  </style>
</head>
<body>
  <script id="studio-data" type="application/json">{embedded}</script>
  <main class="shell">
    <section class="topbar">
      <div>
        <h1>LuminAI Studio Dashboard</h1>
        <p class="subtitle" id="projectLine"></p>
      </div>
      <nav class="actions" aria-label="Studio actions">
        <button class="primary" id="refreshButton" type="button">Refresh Status</button>
        <a class="button" href="/demo/closed-loop-plan">Plan JSON</a>
        <a class="button" href="/api/jellyfish/base-status">Jellyfish JSON</a>
      </nav>
    </section>
    <section class="metric-row" id="metrics"></section>
    <section class="grid">
      <section class="panel">
        <h2>Stage Index</h2>
        <div id="stages"></div>
      </section>
      <section class="panel">
        <h2>Shot Workbench</h2>
        <div id="shots"></div>
      </section>
      <aside class="panel">
        <h2>Jellyfish Base</h2>
        <div id="jellyfish"></div>
      </aside>
      <section class="panel" style="grid-column: 1 / -1;">
        <h2>Industrial Review</h2>
        <div id="review"></div>
      </section>
    </section>
  </main>
  <script>
    const dataNode = document.getElementById("studio-data");
    let state = JSON.parse(dataNode.textContent);

    function esc(value) {{
      return String(value ?? "").replace(/[&<>"']/g, (item) => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }}[item]));
    }}

    function render(payload) {{
      const summary = payload.summary;
      const metadata = summary.metadata || {{}};
      const qa = summary.qa || {{}};
      const post = summary.post_production || {{}};
      document.getElementById("projectLine").textContent =
        `${{summary.project.title}} / ${{summary.chapter.title}} - ${{summary.project.description}}`;
      document.getElementById("metrics").innerHTML = [
        ["Shots", metadata.shot_count ?? 0],
        ["Render Requests", (summary.render_requests || []).length],
        ["Retry Requests", (summary.retry_requests || []).length],
        ["Final Export", post.enabled ? "Planned" : "Blocked"],
      ].map(([label, value]) => `<div class="metric"><span>${{esc(label)}}</span><strong>${{esc(value)}}</strong></div>`).join("");

      document.getElementById("stages").innerHTML = payload.stages.map((stage) => `
        <div class="stage">
          <div class="dot ${{stage.status === "done" ? "done" : ""}}"></div>
          <div>
            <div class="stage-title"><span>${{esc(stage.label)}}</span><span class="stage-owner">${{esc(stage.owner)}}</span></div>
            <div class="evidence">${{esc(stage.evidence)}}</div>
          </div>
        </div>
      `).join("");

      const failed = new Map((qa.failed_shots || []).map((item) => [item.shot_id, item]));
      document.getElementById("shots").innerHTML = (summary.render_requests || []).map((request, index) => {{
        const fail = failed.get(request.shot_id);
        const status = fail ? "Review" : "Approved";
        const issues = fail ? fail.issues.map((issue) => `${{issue.code}}: ${{issue.repair_hint}}`).join("\\n") : "QA passed";
        return `
          <article class="shot">
            <div class="shot-head">
              <div class="shot-title">${{index + 1}}. ${{esc(request.shot_id)}}</div>
              <span class="chip ${{fail ? "warn" : "ok"}}">${{status}}</span>
            </div>
            <div class="muted">Model: ${{esc(request.model)}} | References: ${{(request.references || []).length}}</div>
            <pre>${{esc(request.prompt)}}\\n\\n${{esc(issues)}}</pre>
          </article>
        `;
      }}).join("");

      const jellyfish = payload.jellyfish || {{}};
      const command = (jellyfish.run_commands || [])[0] || {{}};
      document.getElementById("jellyfish").innerHTML = `
        <div class="base-list">
          <div class="base-row"><span class="muted">Available</span><span>${{jellyfish.available ? "Yes" : "No"}}</span></div>
          <div class="base-row"><span class="muted">Path</span><span>${{esc(jellyfish.path)}}</span></div>
          <div class="base-row"><span class="muted">Commit</span><span>${{esc(jellyfish.commit || "not initialized")}}</span></div>
          <div class="base-row"><span class="muted">Frontend</span><span>${{esc((jellyfish.ports || {{}}).frontend)}}</span></div>
          <div class="base-row"><span class="muted">Backend</span><span>${{esc((jellyfish.ports || {{}}).backend)}}</span></div>
        </div>
        <pre>${{esc(command.command || "git submodule update --init --recursive")}}</pre>
      `;

      document.getElementById("review").innerHTML = (payload.review || []).map((item) => `
        <div class="review-item">
          <div class="review-title"><span>${{esc(item.pain_point)}}</span><span class="chip ${{item.status === "done" ? "ok" : "warn"}}">${{esc(item.status)}}</span></div>
          <p class="review-copy">${{esc(item.production_answer)}}</p>
          <p class="review-copy">${{esc(item.implementation)}}</p>
          <p class="muted">${{esc(item.reference)}}</p>
        </div>
      `).join("");
    }}

    document.getElementById("refreshButton").addEventListener("click", async () => {{
      const response = await fetch("/api/studio/status", {{ headers: {{ "Accept": "application/json" }} }});
      state = await response.json();
      render(state);
    }});

    render(state);
  </script>
</body>
</html>
"""


def _build_actions(jellyfish: JellyfishBaseStatus) -> list[dict[str, str]]:
    actions = [
        {"label": "Open LuminAI Dashboard", "url": "http://127.0.0.1:8765/"},
        {"label": "Open LuminAI Plan API", "url": "http://127.0.0.1:8765/demo/closed-loop-plan"},
    ]
    if jellyfish.available:
        actions.extend(
            [
                {"label": "Open Jellyfish Frontend", "url": jellyfish.ports["frontend"]},
                {"label": "Open Jellyfish Backend Docs", "url": jellyfish.ports["backend_docs"]},
            ]
        )
    return actions


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
