/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmWorkflowAutomationRead = {
    mode: 'automatic' | 'manual';
    auto_advance: boolean;
    stop_after_stage: boolean;
    manual_allowed?: boolean;
    next_stage_key?: (string | null);
};
