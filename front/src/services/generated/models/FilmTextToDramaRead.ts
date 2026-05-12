/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmChapterBriefRead } from './FilmChapterBriefRead';
import type { FilmProjectBriefRead } from './FilmProjectBriefRead';
import type { FilmQueuedTaskRead } from './FilmQueuedTaskRead';
import type { FilmShootingGateRead } from './FilmShootingGateRead';
import type { FilmWorkflowStateRead } from './FilmWorkflowStateRead';
export type FilmTextToDramaRead = {
    project: FilmProjectBriefRead;
    chapters: Array<FilmChapterBriefRead>;
    created_shot_count: number;
    created_character_count: number;
    created_scene_count: number;
    created_prop_count: number;
    created_costume_count: number;
    reference_harvest_task_count: number;
    shooting_gate: FilmShootingGateRead;
    workflow: FilmWorkflowStateRead;
    tasks: Array<FilmQueuedTaskRead>;
    next_url: string;
    usage: Record<string, any>;
};
