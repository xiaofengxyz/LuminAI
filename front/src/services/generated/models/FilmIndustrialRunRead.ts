/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmIndustrialOverviewRead } from './FilmIndustrialOverviewRead';
import type { FilmQueuedTaskRead } from './FilmQueuedTaskRead';
export type FilmIndustrialRunRead = {
    run_id: string;
    mode: string;
    plan_id: string;
    created_task_count: number;
    render_task_count: number;
    qa_task_count: number;
    retry_task_count: number;
    post_task_count: number;
    tasks: Array<FilmQueuedTaskRead>;
    write_back_summary: Record<string, any>;
    overview: FilmIndustrialOverviewRead;
};
