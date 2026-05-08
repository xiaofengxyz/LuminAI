/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmIndustrialOverviewRead } from './FilmIndustrialOverviewRead';
import type { FilmNextActionRead } from './FilmNextActionRead';
import type { FilmPostProductionRead } from './FilmPostProductionRead';
import type { FilmQaPolicyRead } from './FilmQaPolicyRead';
import type { FilmRenderQueueItemRead } from './FilmRenderQueueItemRead';
import type { FilmRetryPolicyRead } from './FilmRetryPolicyRead';
export type FilmIndustrialPlanRead = {
    plan_id: string;
    workflow: Array<string>;
    overview: FilmIndustrialOverviewRead;
    render_queue: Array<FilmRenderQueueItemRead>;
    qa_policy: FilmQaPolicyRead;
    retry_policy: FilmRetryPolicyRead;
    post_production: FilmPostProductionRead;
    blockers: Array<FilmNextActionRead>;
};
