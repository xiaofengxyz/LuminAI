/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmWorkflowStageCompleteRequest = {
    /**
     * 可选章节 ID；为空时推进项目级工作流
     */
    chapter_id?: (string | null);
    /**
     * 操作者标识
     */
    actor?: string;
    /**
     * 阶段执行结果摘要
     */
    result?: Record<string, any>;
    /**
     * 本次完成时临时覆盖阶段执行开关
     */
    execution_mode?: ('automatic' | 'manual' | null);
};
