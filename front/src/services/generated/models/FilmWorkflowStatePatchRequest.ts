/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmWorkflowStatePatchRequest = {
    /**
     * 可选章节 ID；为空时编辑项目级工作流
     */
    chapter_id?: (string | null);
    /**
     * 编辑者标识
     */
    actor?: string;
    /**
     * 本次编辑说明
     */
    note?: string;
    /**
     * 结构化阶段补丁
     */
    patch?: Record<string, any>;
    /**
     * 阶段执行开关；automatic 自动进入下一阶段，manual 阶段结束后停等人工
     */
    execution_mode?: ('automatic' | 'manual' | null);
    /**
     * automatic 模式下是否自动推进下一阶段
     */
    auto_advance?: (boolean | null);
};
