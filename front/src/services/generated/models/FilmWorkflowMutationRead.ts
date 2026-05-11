/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmQueuedTaskRead } from './FilmQueuedTaskRead';
import type { FilmWorkflowStateRead } from './FilmWorkflowStateRead';
export type FilmWorkflowMutationRead = {
    workflow: FilmWorkflowStateRead;
    task?: (FilmQueuedTaskRead | null);
    event: Record<string, any>;
};
