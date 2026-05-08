/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmIndustrialRunRequest = {
    /**
     * 可选章节 ID；为空时按项目聚合规划
     */
    chapter_id?: (string | null);
    /**
     * 运行时供应商逻辑名
     */
    provider?: string;
    /**
     * 视频模型逻辑名
     */
    model?: string;
    /**
     * 计划输出目录
     */
    output_dir?: string;
    /**
     * queue_only=只创建任务账本，由现有 worker/人工配置继续执行
     */
    mode?: string;
};
