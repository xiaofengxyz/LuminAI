/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmWorkflowRegenerateRequest = {
    /**
     * 可选章节 ID；为空时重生成项目级工作流阶段
     */
    chapter_id?: (string | null);
    /**
     * 操作者标识
     */
    actor?: string;
    /**
     * 重生成原因
     */
    reason?: string;
    /**
     * 重生成时附加的结构化约束
     */
    patch?: Record<string, any>;
    /**
     * 重生成任务供应商逻辑名
     */
    provider?: string;
    /**
     * 重生成任务模型逻辑名
     */
    model?: string;
};
