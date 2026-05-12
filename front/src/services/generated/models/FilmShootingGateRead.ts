/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FilmShootingGateRead = {
    ready: boolean;
    state: string;
    message: string;
    blockers: Array<string>;
    required_before_shooting: Array<string>;
    allowed_runtime_models: Array<string>;
};
