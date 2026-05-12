/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmWorkflowAutomationRead } from './FilmWorkflowAutomationRead';
export type FilmWorkflowStageRead = {
    key: string;
    title: string;
    owner: string;
    prompt_file: string;
    editable: boolean;
    regeneratable: boolean;
    qa_gate: string;
    default_execution_mode: 'automatic' | 'manual';
    automation: FilmWorkflowAutomationRead;
    status: Record<string, any>;
    data: Record<string, any>;
};
