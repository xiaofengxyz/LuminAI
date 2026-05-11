/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiResponse_FilmIndustrialOverviewRead_ } from '../models/ApiResponse_FilmIndustrialOverviewRead_';
import type { ApiResponse_FilmIndustrialPlanRead_ } from '../models/ApiResponse_FilmIndustrialPlanRead_';
import type { ApiResponse_FilmIndustrialRunRead_ } from '../models/ApiResponse_FilmIndustrialRunRead_';
import type { ApiResponse_FilmWorkflowMutationRead_ } from '../models/ApiResponse_FilmWorkflowMutationRead_';
import type { ApiResponse_FilmWorkflowStateRead_ } from '../models/ApiResponse_FilmWorkflowStateRead_';
import type { ApiResponse_GenerationTaskLinkRead_ } from '../models/ApiResponse_GenerationTaskLinkRead_';
import type { ApiResponse_NoneType_ } from '../models/ApiResponse_NoneType_';
import type { ApiResponse_PaginatedData_GenerationTaskLinkRead__ } from '../models/ApiResponse_PaginatedData_GenerationTaskLinkRead__';
import type { ApiResponse_PaginatedData_TaskListItemRead__ } from '../models/ApiResponse_PaginatedData_TaskListItemRead__';
import type { ApiResponse_TaskCancelRead_ } from '../models/ApiResponse_TaskCancelRead_';
import type { ApiResponse_TaskCreated_ } from '../models/ApiResponse_TaskCreated_';
import type { ApiResponse_TaskLinkAdoptRead_ } from '../models/ApiResponse_TaskLinkAdoptRead_';
import type { ApiResponse_TaskResultRead_ } from '../models/ApiResponse_TaskResultRead_';
import type { ApiResponse_TaskStatusRead_ } from '../models/ApiResponse_TaskStatusRead_';
import type { ApiResponse_VideoPromptPreviewResponse_ } from '../models/ApiResponse_VideoPromptPreviewResponse_';
import type { FilmIndustrialPlanRequest } from '../models/FilmIndustrialPlanRequest';
import type { FilmIndustrialRunRequest } from '../models/FilmIndustrialRunRequest';
import type { FilmWorkflowRegenerateRequest } from '../models/FilmWorkflowRegenerateRequest';
import type { FilmWorkflowStatePatchRequest } from '../models/FilmWorkflowStatePatchRequest';
import type { GenerationTaskLinkCreate } from '../models/GenerationTaskLinkCreate';
import type { GenerationTaskLinkUpdate } from '../models/GenerationTaskLinkUpdate';
import type { ShotFramePromptRequest } from '../models/ShotFramePromptRequest';
import type { TaskCancelRequest } from '../models/TaskCancelRequest';
import type { TaskLinkAdoptRequest } from '../models/TaskLinkAdoptRequest';
import type { TaskStatus } from '../models/TaskStatus';
import type { VideoGenerationTaskRequest } from '../models/VideoGenerationTaskRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FilmService {
    /**
     * 工业电影级 Film Core 总览
     * Return Film Core readiness, pipeline state, and nine-phase delivery evidence.
     * @returns ApiResponse_FilmIndustrialOverviewRead_ Successful Response
     * @throws ApiError
     */
    public static loadIndustrialOverview({
        projectId,
        chapterId,
    }: {
        projectId: string,
        /**
         * 可选章节 ID；为空时按项目聚合
         */
        chapterId?: (string | null),
    }): CancelablePromise<ApiResponse_FilmIndustrialOverviewRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/industrial/projects/{project_id}/overview',
            path: {
                'project_id': projectId,
            },
            query: {
                'chapter_id': chapterId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 读取 CineForge 可编辑工作流状态
     * Load or initialize the persisted CineForge workflow state for this scope.
     * @returns ApiResponse_FilmWorkflowStateRead_ Successful Response
     * @throws ApiError
     */
    public static loadWorkflowState({
        projectId,
        chapterId,
    }: {
        projectId: string,
        /**
         * 可选章节 ID；为空时按项目聚合
         */
        chapterId?: (string | null),
    }): CancelablePromise<ApiResponse_FilmWorkflowStateRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/industrial/projects/{project_id}/workflow-state',
            path: {
                'project_id': projectId,
            },
            query: {
                'chapter_id': chapterId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 编辑 CineForge 工作流阶段
     * Merge an operator patch into one persisted workflow stage and ledger it.
     * @returns ApiResponse_FilmWorkflowMutationRead_ Successful Response
     * @throws ApiError
     */
    public static editWorkflowState({
        projectId,
        stageKey,
        requestBody,
    }: {
        projectId: string,
        stageKey: string,
        requestBody: FilmWorkflowStatePatchRequest,
    }): CancelablePromise<ApiResponse_FilmWorkflowMutationRead_> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}',
            path: {
                'project_id': projectId,
                'stage_key': stageKey,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 重生成 CineForge 工作流阶段
     * Queue a targeted regeneration task while preserving approved workflow state.
     * @returns ApiResponse_FilmWorkflowMutationRead_ Successful Response
     * @throws ApiError
     */
    public static regenerateWorkflowStage({
        projectId,
        stageKey,
        requestBody,
    }: {
        projectId: string,
        stageKey: string,
        requestBody: FilmWorkflowRegenerateRequest,
    }): CancelablePromise<ApiResponse_FilmWorkflowMutationRead_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/industrial/projects/{project_id}/workflow-state/{stage_key}/regenerate',
            path: {
                'project_id': projectId,
                'stage_key': stageKey,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 生成工业闭环生产计划预览
     * Return a render, QA, retry, and post-production plan without executing runtime work.
     * @returns ApiResponse_FilmIndustrialPlanRead_ Successful Response
     * @throws ApiError
     */
    public static createIndustrialPlan({
        projectId,
        requestBody,
    }: {
        projectId: string,
        requestBody: FilmIndustrialPlanRequest,
    }): CancelablePromise<ApiResponse_FilmIndustrialPlanRead_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/industrial/projects/{project_id}/plan',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 创建工业闭环生产任务账本
     * Create Jellyfish task/link records for render, QA, retry, and post-production work.
     * @returns ApiResponse_FilmIndustrialRunRead_ Successful Response
     * @throws ApiError
     */
    public static createIndustrialRun({
        projectId,
        requestBody,
    }: {
        projectId: string,
        requestBody: FilmIndustrialRunRequest,
    }): CancelablePromise<ApiResponse_FilmIndustrialRunRead_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/industrial/projects/{project_id}/run',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 视频提示词预览
     * 预览视频生成的提示词与自动关联参考图。
     * @returns ApiResponse_VideoPromptPreviewResponse_ Successful Response
     * @throws ApiError
     */
    public static previewVideoGenerationPromptApiV1FilmTasksVideoPreviewPromptPost({
        requestBody,
    }: {
        requestBody: VideoGenerationTaskRequest,
    }): CancelablePromise<ApiResponse_VideoPromptPreviewResponse_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/tasks/video/preview-prompt',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 视频生成（任务版）
     * 创建视频生成任务并后台执行，结果通过 /tasks/{task_id}/result 获取。
     * @returns ApiResponse_TaskCreated_ Successful Response
     * @throws ApiError
     */
    public static createVideoGenerationTaskApiV1FilmTasksVideoPost({
        requestBody,
    }: {
        requestBody: VideoGenerationTaskRequest,
    }): CancelablePromise<ApiResponse_TaskCreated_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/tasks/video',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 镜头分镜帧提示词生成（任务版）
     * @returns ApiResponse_TaskCreated_ Successful Response
     * @throws ApiError
     */
    public static createShotFramePromptTaskApiV1FilmTasksShotFramePromptsPost({
        requestBody,
    }: {
        requestBody: ShotFramePromptRequest,
    }): CancelablePromise<ApiResponse_TaskCreated_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/tasks/shot-frame-prompts',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 全局任务列表（任务中心）
     * @returns ApiResponse_PaginatedData_TaskListItemRead__ Successful Response
     * @throws ApiError
     */
    public static listTasksApiV1FilmTasksGet({
        statuses,
        taskKind,
        relationType,
        relationEntityId,
        recentSeconds = 300,
        page = 1,
        pageSize = 20,
    }: {
        /**
         * 按任务状态过滤，可多选
         */
        statuses?: (Array<TaskStatus> | null),
        /**
         * 按 task_kind 过滤
         */
        taskKind?: (string | null),
        /**
         * 按 relation_type 过滤
         */
        relationType?: (string | null),
        /**
         * 按 relation_entity_id 过滤
         */
        relationEntityId?: (string | null),
        /**
         * 默认返回最近结束任务的时间窗口（秒）
         */
        recentSeconds?: number,
        /**
         * 页码
         */
        page?: number,
        /**
         * 每页条数
         */
        pageSize?: number,
    }): CancelablePromise<ApiResponse_PaginatedData_TaskListItemRead__> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/tasks',
            query: {
                'statuses': statuses,
                'task_kind': taskKind,
                'relation_type': relationType,
                'relation_entity_id': relationEntityId,
                'recent_seconds': recentSeconds,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 查询任务状态/进度（轮询）
     * @returns ApiResponse_TaskStatusRead_ Successful Response
     * @throws ApiError
     */
    public static getTaskStatusApiV1FilmTasksTaskIdStatusGet({
        taskId,
    }: {
        taskId: string,
    }): CancelablePromise<ApiResponse_TaskStatusRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/tasks/{task_id}/status',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 获取任务结果
     * @returns ApiResponse_TaskResultRead_ Successful Response
     * @throws ApiError
     */
    public static getTaskResultApiV1FilmTasksTaskIdResultGet({
        taskId,
    }: {
        taskId: string,
    }): CancelablePromise<ApiResponse_TaskResultRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/tasks/{task_id}/result',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 请求取消任务
     * @returns ApiResponse_TaskCancelRead_ Successful Response
     * @throws ApiError
     */
    public static cancelTaskApiV1FilmTasksTaskIdCancelPost({
        taskId,
        requestBody,
    }: {
        taskId: string,
        requestBody: TaskCancelRequest,
    }): CancelablePromise<ApiResponse_TaskCancelRead_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/tasks/{task_id}/cancel',
            path: {
                'task_id': taskId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 更新任务关联的采用状态（仅可正向变更）
     * 将指定任务链接的状态设为 accepted；已采用不可改为未采用。
     * @returns ApiResponse_TaskLinkAdoptRead_ Successful Response
     * @throws ApiError
     */
    public static adoptTaskLinkApiV1FilmTaskLinksAdoptPatch({
        requestBody,
    }: {
        requestBody: TaskLinkAdoptRequest,
    }): CancelablePromise<ApiResponse_TaskLinkAdoptRead_> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/film/task-links/adopt',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 生成任务关联列表（分页，支持多条件过滤）
     * @returns ApiResponse_PaginatedData_GenerationTaskLinkRead__ Successful Response
     * @throws ApiError
     */
    public static listTaskLinksApiV1FilmTaskLinksGet({
        resourceType,
        relationType,
        relationEntityId,
        status,
        taskId,
        order,
        isDesc = true,
        page = 1,
        pageSize = 10,
    }: {
        /**
         * 按 resource_type 过滤
         */
        resourceType?: (string | null),
        /**
         * 按 relation_type 过滤
         */
        relationType?: (string | null),
        /**
         * 按 relation_entity_id 过滤
         */
        relationEntityId?: (string | null),
        /**
         * 按关联状态过滤（accepted/todo/rejected）
         */
        status?: (string | null),
        /**
         * 按 task_id 过滤
         */
        taskId?: (string | null),
        /**
         * 排序字段：updated_at/created_at/id/status
         */
        order?: (string | null),
        /**
         * 是否倒序；默认 true
         */
        isDesc?: boolean,
        /**
         * 页码
         */
        page?: number,
        /**
         * 每页条数
         */
        pageSize?: number,
    }): CancelablePromise<ApiResponse_PaginatedData_GenerationTaskLinkRead__> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/task-links',
            query: {
                'resource_type': resourceType,
                'relation_type': relationType,
                'relation_entity_id': relationEntityId,
                'status': status,
                'task_id': taskId,
                'order': order,
                'is_desc': isDesc,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 创建生成任务关联
     * @returns ApiResponse_GenerationTaskLinkRead_ Successful Response
     * @throws ApiError
     */
    public static createTaskLinkApiV1FilmTaskLinksPost({
        requestBody,
    }: {
        requestBody: GenerationTaskLinkCreate,
    }): CancelablePromise<ApiResponse_GenerationTaskLinkRead_> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/film/task-links',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 获取生成任务关联详情
     * @returns ApiResponse_GenerationTaskLinkRead_ Successful Response
     * @throws ApiError
     */
    public static getTaskLinkApiV1FilmTaskLinksLinkIdGet({
        linkId,
    }: {
        linkId: number,
    }): CancelablePromise<ApiResponse_GenerationTaskLinkRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/film/task-links/{link_id}',
            path: {
                'link_id': linkId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 更新生成任务关联（不支持直接修改 is_adopted）
     * @returns ApiResponse_GenerationTaskLinkRead_ Successful Response
     * @throws ApiError
     */
    public static updateTaskLinkApiV1FilmTaskLinksLinkIdPatch({
        linkId,
        requestBody,
    }: {
        linkId: number,
        requestBody: GenerationTaskLinkUpdate,
    }): CancelablePromise<ApiResponse_GenerationTaskLinkRead_> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/film/task-links/{link_id}',
            path: {
                'link_id': linkId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 删除生成任务关联
     * @returns ApiResponse_NoneType_ Successful Response
     * @throws ApiError
     */
    public static deleteTaskLinkApiV1FilmTaskLinksLinkIdDelete({
        linkId,
    }: {
        linkId: number,
    }): CancelablePromise<ApiResponse_NoneType_> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/film/task-links/{link_id}',
            path: {
                'link_id': linkId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
