/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectStyle } from './ProjectStyle';
import type { ProjectVisualStyle } from './ProjectVisualStyle';
export type FilmTextToDramaRequest = {
    /**
     * 用户输入的一段创意、梗概或原始文本
     */
    source_text: string;
    /**
     * 可选项目 ID；为空则自动生成
     */
    project_id?: (string | null);
    /**
     * 可选项目名称；为空从文本生成
     */
    project_name?: (string | null);
    /**
     * 生成多集漫剧的集数
     */
    episode_count?: number;
    /**
     * 每集初始镜头数
     */
    shots_per_episode?: number;
    /**
     * 项目题材/风格
     */
    style?: ProjectStyle;
    /**
     * 画面表现形式
     */
    visual_style?: ProjectVisualStyle;
    /**
     * 默认视频比例
     */
    default_video_ratio?: string;
    /**
     * 全流程默认开关；automatic 进入自动任务账本，manual 创建后停等人工
     */
    automation_mode?: 'automatic' | 'manual';
    /**
     * 生产计划使用的供应商逻辑名
     */
    provider?: string;
    /**
     * 生产计划使用的模型逻辑名
     */
    model?: string;
};
