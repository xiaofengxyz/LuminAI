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
GET  /api/v1/film/industrial/projects/{project_id}/overview
POST /api/v1/film/industrial/projects/{project_id}/plan
```

前端通过 OpenAPI generated `FilmService` 调用接口，`front/src/services/industrialFilm.ts`
只保留类型别名、空响应保护和调用封装。

## Nine-Phase Evidence

`overview` 返回两组状态：

- `implementation_status`: starter-kit 九阶段总完成度，目前为 `9/9 complete`
- `implementation_phases`: Phase 1 到 Phase 9 的 owner、evidence 和代码/测试表面

这些字段渲染为 `Film Core` tab 内的 `九阶段交付状态` 面板。

## Production Pipeline

`overview.pipeline` 是运行时生产闭环状态，当前包含 11 个节点：

```text
Novel / Script -> Story Graph -> Director Planner -> Film Core ->
Prompt Compiler -> Runtime Adapter -> Render Runtime -> Video Models ->
QA Engine -> Retry Engine -> Final Editing
```

九阶段实现状态与 11 节点生产流水线是两个不同视角：前者回答“系统是否已实现”，后者回答“当前项目生产进度到哪里”。
