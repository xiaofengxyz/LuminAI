import { OpenAPI } from './generated'
import { getBackendBaseUrl } from './runtimeConfig'

/**
 * 初始化由 OpenAPI 生成的请求客户端。
 *
 * 说明：
 * - 生成接口的路径已包含 `/api/v1/...`，因此 BASE 默认应为空串（同源）或完整后端地址。
 * - 本地开发默认直连 `http://localhost:24731`。
 */
export function initOpenAPI(base: string = getBackendBaseUrl()) {
  OpenAPI.BASE = base
}

initOpenAPI()
