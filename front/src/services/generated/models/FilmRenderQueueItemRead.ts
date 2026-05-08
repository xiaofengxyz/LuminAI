/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FilmCompiledPromptContractRead } from './FilmCompiledPromptContractRead';
export type FilmRenderQueueItemRead = {
    slot: number;
    shot_ref: string;
    provider: string;
    model: string;
    output_path: string;
    references_required: Array<string>;
    compiled_prompt_contract: FilmCompiledPromptContractRead;
};
