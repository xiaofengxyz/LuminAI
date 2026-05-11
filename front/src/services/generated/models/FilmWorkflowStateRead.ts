/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmWorkflowStageRead } from './FilmWorkflowStageRead';
export type FilmWorkflowStateRead = {
    id: string;
    workflow_key: string;
    version: number;
    status: string;
    scope: Record<string, any>;
    persisted: boolean;
    stage_count: number;
    stages: Array<FilmWorkflowStageRead>;
    stage_data: Record<string, any>;
    stage_status: Record<string, any>;
    edit_log: Array<Record<string, any>>;
    regenerate_log: Array<Record<string, any>>;
    last_task_id?: (string | null);
    edit_contract: Record<string, any>;
    regenerate_contract: Record<string, any>;
};
