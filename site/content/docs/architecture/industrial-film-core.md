---
title: "Industrial Film Core"
weight: 7
description: "Jellyfish Project Workbench 中已生效的 Film Core 入口、接口与九阶段状态展示。"
---

> 本文记录当前真实实现，不记录未来计划。

## UI Entry Points

Film Core 现在是项目工作台内的原生能力，不是独立外部页面。

```text
Projects -> project card Film Core
Projects -> project preview Film Core Status
Project Workbench -> Film Core
Direct URL -> /projects/{project_id}?tab=filmCore
```

项目工作台顶部也有 `Film Core` 按钮，即使横向标签折叠，也能直接进入。

## API Contract

```text
POST  /api/v1/film/industrial/text-to-drama
GET   /api/v1/film/industrial/projects/{project_id}/overview
GET   /api/v1/film/industrial/projects/{project_id}/workflow-state
PATCH /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}
POST  /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/regenerate
POST  /api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/complete
POST  /api/v1/film/industrial/projects/{project_id}/plan
POST  /api/v1/film/industrial/projects/{project_id}/run
```

前端通过 OpenAPI generated `FilmService` 调用接口，`front/src/services/industrialFilm.ts`
只保留类型别名、空响应保护和调用封装。

## Nine-Phase Evidence

`overview` 返回两组状态：

- `implementation_status`: starter-kit 九阶段总完成度，目前为 `9/9 complete`
- `implementation_phases`: Phase 1 到 Phase 9 的 owner、evidence 和代码/测试表面

这些字段渲染为 `Film Core` tab 内的 `九阶段交付状态` 面板。

## Text To Drama And Workflow Gates

项目列表页提供 `文本生成漫剧` 入口。该入口把一段原始创意/梗概/正文写成：

- Jellyfish Project
- 多个 Chapter（按集数）
- 每集 Shot seeds
- `CineForgeWorkflowState`
- `cineforge_text_to_drama_intake` / `cineforge_text_to_drama_auto_pipeline` 任务账本

Film Core tab 内的 `CineForge 可编辑工作流状态` 面板当前支持：

- 选择九个 Prompt-derived stage
- 保存阶段编辑
- 针对单阶段重生成
- 设置 `automatic` / `manual`
- 完成阶段并根据开关自动进入下一阶段或停在 `waiting_operator`

## Production Pipeline

`overview.pipeline` 是运行时生产闭环状态，当前包含 11 个节点：

```text
Novel / Script -> Story Graph -> Director Planner -> Film Core ->
Prompt Compiler -> Runtime Adapter -> Render Runtime -> Video Models ->
QA Engine -> Retry Engine -> Final Editing
```

九阶段实现状态与 11 节点生产流水线是两个不同视角：前者回答“系统是否已实现”，后者回答“当前项目生产进度到哪里”。
