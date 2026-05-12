/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ModelCategoryKey } from './ModelCategoryKey';
/**
 * 模型调用时的隔离适配层配置视图（不回显密钥明文）。
 */
export type RuntimeModelConfigRead = {
    /**
     * 模型 ID
     */
    model_id: string;
    /**
     * 模型名称
     */
    model_name: string;
    /**
     * 模型类别
     */
    category: ModelCategoryKey;
    /**
     * 供应商 ID
     */
    provider_id: string;
    /**
     * 供应商稳定键
     */
    provider_key: string;
    /**
     * 供应商展示名
     */
    provider_display_name: string;
    /**
     * 按类别解析后的实际 Base URL
     */
    base_url?: (string | null);
    /**
     * 该供应商是否要求 API Key
     */
    api_key_required?: boolean;
    /**
     * 是否已配置 API Key
     */
    api_key_configured?: boolean;
    /**
     * 该供应商是否要求 API Secret
     */
    api_secret_required?: boolean;
    /**
     * 是否已配置 API Secret
     */
    api_secret_configured?: boolean;
    /**
     * 实际运行时适配器边界
     */
    isolated_adapter: string;
    /**
     * 模型运行参数
     */
    params?: Record<string, any>;
};
