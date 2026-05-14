# AI 漫剧从零到多集成片操作手册

## 1. 本地服务地址

当前 LuminAI 的 AI 漫剧主工作台使用 Jellyfish：

| 服务 | 地址 | 用途 |
| --- | --- | --- |
| Jellyfish 后端 | `http://127.0.0.1:24731` | API、任务、Film Core、模型配置 |
| Jellyfish 前端 | `http://localhost:24732/projects` | 制片人/导演/资产/分镜操作界面 |
| LuminAI 轻量运行时 | `http://127.0.0.1:8765/` | 工程 smoke 和架构演示，可选 |

说明：`18731/18732` 已检测到被另一个项目 FilmCreator 占用，所以本项目改用
更偏僻的 `24731/24732`，避免端口互相踩踏。

## 2. 配置 `.env`

仓库根目录已有 `.env`。后端启动时会同时读取：

- `./.env`
- `vendor/jellyfish/backend/.env`

阿里百炼 API Key 支持以下变量名，按顺序取第一个非空值：

```env
ALIYUN_BAILIAN_API_KEY=...
BAILIAN_API_KEY=...
DASHSCOPE_API_KEY=...
VITE_API_KEY=...
```

可选覆盖：

```env
ALIYUN_BAILIAN_MODEL=qwen-plus
ALIYUN_BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

启动后系统会自动创建或刷新：

- Provider：`aliyun_bailian`
- 默认文本模型：`aliyun_bailian_text_default`
- 默认文本模型指向：阿里百炼

接口只显示 `api_key_configured=true/false`，不会返回密钥明文。

## 3. 启动服务

推荐一条命令启动后端和前端：

```bash
scripts/start_jellyfish_film_core.sh
```

成功输出类似：

```text
Started Jellyfish backend on http://127.0.0.1:24731
Started Jellyfish frontend on http://localhost:24732/projects
```

如果要手动启动后端：

```bash
cd vendor/jellyfish/backend
NO_PROXY=localhost,127.0.0.1,::1 no_proxy=localhost,127.0.0.1,::1 \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 24731
```

如果要手动启动前端：

```bash
cd vendor/jellyfish/front
VITE_BACKEND_URL=http://127.0.0.1:24731 npx pnpm@9.15.9 run dev:film-core
```

健康检查：

```bash
curl --noproxy '*' http://127.0.0.1:24731/health
```

打开工作台：

```text
http://localhost:24732/projects
```

## 4. 检查百炼模型是否生效

打开 UI：

```text
模型管理 -> Providers / Models / Settings
```

应能看到阿里百炼 Provider 和默认文本模型。

也可以用 API 检查：

```bash
curl --noproxy '*' \
  http://127.0.0.1:24731/api/v1/llm/models/aliyun_bailian_text_default/runtime-config
```

重点看：

```json
{
  "provider_key": "aliyun_bailian",
  "api_key_configured": true
}
```

## 5. 从一句话生成多集 AI 漫剧

1. 打开：

```text
http://localhost:24732/projects
```

2. 点击 `创建 AI 漫剧`。

3. 选择 `自动生成漫剧`。

4. 填写：

- `项目名称`：例如 `霓虹审判`
- `原始创意/梗概/正文`：可以是一句话、短梗概或长正文
- `视觉风格`：例如 `动漫`
- `项目风格`：例如 `国漫`
- `集数`：例如 `3`
- `每集镜头数`：例如 `6`
- `默认视频比例`：竖屏漫剧建议 `9:16`
- `自动推进 / 人工停等`：新手建议先用自动推进
- `角色网络参考采集`：建议开启

5. 如果已有小说文件，点击 `上传小说文件`，选择本地 `.txt` 或 `.md`。
浏览器会读取文本并填入表单，不会把原文件单独上传。

6. 点击创建按钮。创建成功后会自动进入：

```text
/projects/{projectId}?tab=filmCore
```

系统会生成：

- 多集 Chapter
- 每集小说稿和脚本摘要
- Storyboard / Shot Graph
- 镜头动作、景别、机位、运镜、首帧/关键帧/尾帧槽位
- 角色、演员身份参考、服装、道具、场景、VFX 资产圣经
- 角色图片/视频网络参考搜索词和候选 URL 任务
- CineForge 九阶段工作流状态
- Film Core 拍摄门禁和生产计划基础状态

## 6. 从空项目开始

如果你已有剧本、分镜或资产：

1. 打开项目列表。
2. 点击 `创建 AI 漫剧`。
3. 选择 `空项目`。
4. 填写项目名称、风格、seed、画幅。
5. 创建后进入章节页。
6. 手动导入章节、角色、资产、镜头，再进入 Film Core 检查门禁。

## 7. 在 Film Core 判断是否能拍

进入项目后打开：

```text
Project Workbench -> Film Core
```

按顺序检查：

| 面板 | 看什么 | 怎么处理 |
| --- | --- | --- |
| `AI漫剧生产进度` | 项目创建、小说/剧本、分集、资产、参考采集、分镜、镜头准备、生成、QA、后期 | 点模块返回对应页面补齐 |
| `拍摄前置门禁` | 是否 `ready=true` | 不 ready 时先解决 blockers |
| `角色网络参考采集` | 每个角色的图片/视频搜索词和候选 URL | 人工筛选授权素材，不直接商用未授权素材 |
| `CineForge 可编辑工作流状态` | 九阶段是否自动推进、是否需要人工停等 | 可保存阶段编辑或重生成阶段 |
| `生产闭环计划` | render queue、QA、Retry、后期步骤 | ready 后创建生产任务 |

## 8. 创建图片/视频生产任务

当 `拍摄前置门禁` ready 后：

1. 在 Film Core 点击生成/预览生产计划。
2. 检查 render queue 是否包含目标镜头。
3. 点击 `创建生产任务`。
4. 到任务中心查看：

- `industrial_video_render`
- `industrial_qa`
- `industrial_retry_plan`
- `industrial_post_production`

这些任务先进入 Jellyfish 任务账本。真实媒体文件生成由后续 provider worker
执行，架构上与 Film Core 解耦。

## 9. QA、Retry 与后期

生成视频后：

1. Film Core 自动 QA 检查身份、服装、道具、场景、镜头连续性。
2. 失败镜头进入 Retry，不需要整集重做。
3. Retry 生成修复补丁，回写到任务中心。
4. 通过 QA 的镜头进入后期计划：
   - 字幕
   - TTS
   - BGM
   - 转场
   - 多集导出

## 10. 当前功能完成度

已完成：

- 统一 `创建 AI 漫剧` 入口
- 一句话/梗概/小说文件到多集项目
- 小说稿、分集、分镜、资产圣经、VFX、参考采集任务
- Film Core `AI漫剧生产进度`
- 拍摄门禁
- 阿里百炼默认文本模型自动引导
- 独立端口 `24731/24732`
- OpenAPI/generated client/UI 对齐
- 自动 QA / Retry / 后期计划账本
- 自动化测试和 live smoke

仍属于运行时扩展层：

- 真正调用图片/视频供应商生成媒体文件
- 生产级 CV/CLIP/人脸/服装检测器
- 成片文件的实际 FFmpeg/TTS/BGM worker 执行

这些部分不应写进 Film Core 单体，而应继续通过 runtime adapter 和 worker 扩展。
