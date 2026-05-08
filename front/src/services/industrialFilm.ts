import { FilmService } from './generated'
import type {
  FilmAssetHealthRead,
  FilmCompiledPromptContractRead,
  FilmImplementationPhaseRead,
  FilmImplementationStatusRead,
  FilmIndustrialOverviewRead,
  FilmIndustrialPlanRead,
  FilmIndustrialPlanRequest,
  FilmNextActionRead,
  FilmPainPointRead,
  FilmPipelineStageRead,
  FilmProjectBriefRead,
  FilmQaRetryRead,
  FilmReferenceProjectRead,
  FilmRenderQueueItemRead,
} from './generated'

export type FilmProjectBrief = FilmProjectBriefRead
export type FilmChapterBrief = NonNullable<FilmIndustrialOverviewRead['chapter']>
export type FilmPipelineStage = FilmPipelineStageRead
export type FilmAssetHealth = FilmAssetHealthRead
export type FilmQaRetry = FilmQaRetryRead
export type FilmPainPoint = FilmPainPointRead
export type FilmReferenceProject = FilmReferenceProjectRead
export type FilmNextAction = FilmNextActionRead
export type FilmImplementationStatus = FilmImplementationStatusRead
export type FilmImplementationPhase = FilmImplementationPhaseRead
export type FilmCompiledPromptContract = FilmCompiledPromptContractRead
export type FilmRenderQueueItem = FilmRenderQueueItemRead
export type FilmIndustrialOverview = FilmIndustrialOverviewRead
export type FilmIndustrialPlan = FilmIndustrialPlanRead
export type { FilmIndustrialPlanRequest }

type FilmApiResponse<T> =
  {
    data?: T | null
    message?: string | null
  }

function requireData<T>(response: FilmApiResponse<T>): T {
  if (!response.data) {
    throw new Error(response.message || 'Film Core response is empty')
  }
  return response.data as T
}

export async function loadIndustrialOverview(projectId: string, chapterId?: string | null) {
  const response = await FilmService.loadIndustrialOverview({ projectId, chapterId })
  return requireData<FilmIndustrialOverview>(response)
}

export async function createIndustrialPlan(projectId: string, body: FilmIndustrialPlanRequest = {}) {
  const response = await FilmService.createIndustrialPlan({ projectId, requestBody: body })
  return requireData<FilmIndustrialPlan>(response)
}
