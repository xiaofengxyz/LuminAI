import { FilmService } from './generated'
import type {
  FilmAssetHealthRead,
  FilmCompiledPromptContractRead,
  FilmImplementationPhaseRead,
  FilmImplementationStatusRead,
  FilmIndustrialOverviewRead,
  FilmIndustrialPlanRead,
  FilmIndustrialPlanRequest,
  FilmIndustrialRunRead,
  FilmIndustrialRunRequest,
  FilmTextToDramaRead,
  FilmTextToDramaRequest,
  FilmWorkflowMutationRead,
  FilmWorkflowRegenerateRequest,
  FilmWorkflowStageCompleteRequest,
  FilmWorkflowStageRead,
  FilmWorkflowStatePatchRequest,
  FilmWorkflowStateRead,
  FilmNextActionRead,
  FilmPainPointRead,
  FilmPipelineStageRead,
  FilmProjectBriefRead,
  FilmQaRetryRead,
  FilmQueuedTaskRead,
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
export type FilmQueuedTask = FilmQueuedTaskRead
export type FilmIndustrialOverview = FilmIndustrialOverviewRead
export type FilmIndustrialPlan = FilmIndustrialPlanRead
export type FilmIndustrialRun = FilmIndustrialRunRead
export type FilmTextToDrama = FilmTextToDramaRead
export type FilmWorkflowStage = FilmWorkflowStageRead
export type FilmWorkflowState = FilmWorkflowStateRead
export type FilmWorkflowMutation = FilmWorkflowMutationRead
export type {
  FilmIndustrialPlanRequest,
  FilmIndustrialRunRequest,
  FilmTextToDramaRequest,
  FilmWorkflowStatePatchRequest,
  FilmWorkflowRegenerateRequest,
  FilmWorkflowStageCompleteRequest,
}

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

export async function createTextToDrama(body: FilmTextToDramaRequest) {
  const response = await FilmService.createTextToDrama({ requestBody: body })
  return requireData<FilmTextToDrama>(response)
}

export async function loadWorkflowState(projectId: string, chapterId?: string | null) {
  const response = await FilmService.loadWorkflowState({ projectId, chapterId })
  return requireData<FilmWorkflowState>(response)
}

export async function editWorkflowState(
  projectId: string,
  stageKey: string,
  body: FilmWorkflowStatePatchRequest,
) {
  const response = await FilmService.editWorkflowState({ projectId, stageKey, requestBody: body })
  return requireData<FilmWorkflowMutation>(response)
}

export async function regenerateWorkflowStage(
  projectId: string,
  stageKey: string,
  body: FilmWorkflowRegenerateRequest,
) {
  const response = await FilmService.regenerateWorkflowStage({ projectId, stageKey, requestBody: body })
  return requireData<FilmWorkflowMutation>(response)
}

export async function completeWorkflowStage(
  projectId: string,
  stageKey: string,
  body: FilmWorkflowStageCompleteRequest,
) {
  const response = await FilmService.completeWorkflowStage({ projectId, stageKey, requestBody: body })
  return requireData<FilmWorkflowMutation>(response)
}

export async function createIndustrialPlan(projectId: string, body: FilmIndustrialPlanRequest = {}) {
  const response = await FilmService.createIndustrialPlan({ projectId, requestBody: body })
  return requireData<FilmIndustrialPlan>(response)
}

export async function createIndustrialRun(projectId: string, body: FilmIndustrialRunRequest = {}) {
  const response = await FilmService.createIndustrialRun({ projectId, requestBody: body })
  return requireData<FilmIndustrialRun>(response)
}
