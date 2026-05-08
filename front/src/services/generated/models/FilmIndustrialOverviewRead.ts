/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmAssetHealthRead } from './FilmAssetHealthRead';
import type { FilmChapterBriefRead } from './FilmChapterBriefRead';
import type { FilmImplementationPhaseRead } from './FilmImplementationPhaseRead';
import type { FilmImplementationStatusRead } from './FilmImplementationStatusRead';
import type { FilmNextActionRead } from './FilmNextActionRead';
import type { FilmPainPointRead } from './FilmPainPointRead';
import type { FilmPipelineStageRead } from './FilmPipelineStageRead';
import type { FilmProjectBriefRead } from './FilmProjectBriefRead';
import type { FilmQaRetryRead } from './FilmQaRetryRead';
import type { FilmReferenceProjectRead } from './FilmReferenceProjectRead';
export type FilmIndustrialOverviewRead = {
    workflow_mode: string;
    project: FilmProjectBriefRead;
    chapter?: (FilmChapterBriefRead | null);
    industrial_score: number;
    pipeline: Array<FilmPipelineStageRead>;
    asset_health: FilmAssetHealthRead;
    qa_retry: FilmQaRetryRead;
    pain_points: Array<FilmPainPointRead>;
    reference_projects: Array<FilmReferenceProjectRead>;
    operator_next_actions: Array<FilmNextActionRead>;
    implementation_status: FilmImplementationStatusRead;
    implementation_phases: Array<FilmImplementationPhaseRead>;
};
