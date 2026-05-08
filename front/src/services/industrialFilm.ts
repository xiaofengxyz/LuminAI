import { get, post } from './http'

export type FilmApiResponse<T> = {
  code: number
  message: string
  data: T | null
  meta?: Record<string, unknown> | null
}

export type FilmProjectBrief = {
  id: string
  name: string
  style: string
  visual_style: string
  seed: number
  unify_style: boolean
}

export type FilmChapterBrief = {
  id: string | null
  title: string | null
  index: number | null
}

export type FilmPipelineStage = {
  key: string
  title: string
  owner: string
  description: string
  status: string
  evidence: string
  next_action: string
}

export type FilmAssetHealth = {
  identity_score: number
  scene_score: number
  prop_score: number
  costume_score: number
  pending_candidate_count: number
  pending_dialogue_count: number
  summary: string
}

export type FilmQaRetry = {
  qa_ready: boolean
  generated_or_accepted_videos: number
  planned_retry_candidates: number
  risk_level: string
  automatic_retry_enabled: boolean
  post_production_ready: boolean
}

export type FilmPainPoint = {
  key: string
  title: string
  severity: string
  diagnosis: string
  solution: string
}

export type FilmReferenceProject = {
  name: string
  url: string
  adopted_layer: string
  rule: string
}

export type FilmNextAction = {
  severity: string
  action: string
}

export type FilmIndustrialOverview = {
  workflow_mode: string
  project: FilmProjectBrief
  chapter: FilmChapterBrief | null
  industrial_score: number
  pipeline: FilmPipelineStage[]
  asset_health: FilmAssetHealth
  qa_retry: FilmQaRetry
  pain_points: FilmPainPoint[]
  reference_projects: FilmReferenceProject[]
  operator_next_actions: FilmNextAction[]
}

export type FilmRenderQueueItem = {
  slot: number
  shot_ref: string
  provider: string
  model: string
  output_path: string
  references_required: string[]
  compiled_prompt_contract: {
    source: string
    must_include: string[]
  }
}

export type FilmIndustrialPlan = {
  plan_id: string
  workflow: string[]
  overview: FilmIndustrialOverview
  render_queue: FilmRenderQueueItem[]
  qa_policy: {
    face_similarity_min: number
    outfit_similarity_min: number
    clip_score_min: number
    continuity_checks: string[]
  }
  retry_policy: {
    max_attempts: number
    planned_retry_candidates: number
    repair_patch_contract: string[]
  }
  post_production: {
    enabled: boolean
    steps: string[]
    write_back_targets: string[]
  }
  blockers: FilmNextAction[]
}

export type FilmIndustrialPlanRequest = {
  chapter_id?: string | null
  provider?: string
  model?: string
  output_dir?: string
}

function requireData<T>(response: FilmApiResponse<T>): T {
  if (!response.data) {
    throw new Error(response.message || 'Film Core response is empty')
  }
  return response.data
}

export async function loadIndustrialOverview(projectId: string, chapterId?: string | null) {
  const response = await get<FilmApiResponse<FilmIndustrialOverview>>(
    `/v1/film/industrial/projects/${encodeURIComponent(projectId)}/overview`,
    chapterId ? { params: { chapter_id: chapterId } } : undefined,
  )
  return requireData(response)
}

export async function createIndustrialPlan(projectId: string, body: FilmIndustrialPlanRequest = {}) {
  const response = await post<FilmApiResponse<FilmIndustrialPlan>>(
    `/v1/film/industrial/projects/${encodeURIComponent(projectId)}/plan`,
    body,
  )
  return requireData(response)
}
