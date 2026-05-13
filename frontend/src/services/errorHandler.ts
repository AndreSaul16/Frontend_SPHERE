/**
 * Handler central de errores estructurados del backend.
 *
 * El backend devuelve respuestas con shape:
 * {
 *   "error": "billing.insufficient_credits",   // code machine-readable
 *   "message": "Has agotado tus mensajes...",  // string humano
 *   "details": { plan_id: "free", ... }        // contexto
 * }
 *
 * Este módulo:
 * 1. Parsea cualquier respuesta de error (estructurada o no).
 * 2. Mapea códigos a acciones (paywall, toast, redirect, etc.).
 * 3. Devuelve un objeto AppError uniforme para que componentes muestren mensaje.
 */

import { useBillingStore } from '../store/useBillingStore';

export type ErrorCode =
    // auth
    | 'auth.missing_token'
    | 'auth.invalid_token'
    | 'auth.expired_token'
    | 'auth.user_disabled'
    // perm
    | 'perm.not_owner'
    | 'perm.plan_not_allowed'
    // billing
    | 'billing.insufficient_credits'
    | 'billing.invalid_plan'
    | 'billing.stripe_error'
    | 'billing.no_customer'
    | 'billing.webhook_invalid_signature'
    | 'billing.webhook_invalid_payload'
    // rag
    | 'rag.quota_exceeded'
    | 'rag.file_too_large'
    | 'rag.file_type_unsupported'
    | 'rag.file_empty'
    | 'rag.agent_files_limit'
    | 'rag.doc_not_found'
    // agents
    | 'agents.quota_exceeded'
    | 'agents.not_found'
    | 'agents.invalid_model'
    // llm
    | 'llm.upstream_error'
    | 'llm.timeout'
    | 'llm.context_too_long'
    // session
    | 'session.not_found'
    | 'session.locked'
    // tools
    | 'tool.not_authorized'
    | 'tool.invalid_args'
    | 'tool.upstream_error'
    // genéricos
    | 'common.bad_request'
    | 'common.internal_error'
    | 'common.rate_limited'
    | 'common.unknown';

export interface AppError {
    code: ErrorCode;
    message: string;
    details: Record<string, any>;
    status: number;
}

/**
 * Parsea la respuesta de error del backend.
 * Tolera respuestas no estructuradas (compat con HTTPException legacy).
 */
export async function parseError(response: Response): Promise<AppError> {
    let body: any = null;
    try {
        body = await response.json();
    } catch {
        // No-JSON, devolvemos error genérico.
        return {
            code: 'common.unknown',
            message: response.statusText || `HTTP ${response.status}`,
            details: {},
            status: response.status,
        };
    }

    // Cuerpo FastAPI: { "detail": { error, message, details } } o { "detail": "string" }
    const detail = body?.detail ?? body;

    if (typeof detail === 'object' && detail?.error) {
        return {
            code: detail.error as ErrorCode,
            message: detail.message ?? response.statusText,
            details: detail.details ?? {},
            status: response.status,
        };
    }

    // Legacy: detail es string.
    return {
        code: inferCodeFromStatus(response.status),
        message: typeof detail === 'string' ? detail : response.statusText,
        details: {},
        status: response.status,
    };
}

function inferCodeFromStatus(status: number): ErrorCode {
    switch (status) {
        case 401:
            return 'auth.invalid_token';
        case 402:
            return 'billing.insufficient_credits';
        case 403:
            return 'perm.plan_not_allowed';
        case 404:
            return 'common.bad_request';
        case 429:
            return 'common.rate_limited';
        case 502:
        case 504:
            return 'llm.upstream_error';
        default:
            return status >= 500 ? 'common.internal_error' : 'common.bad_request';
    }
}

/**
 * Aplica la acción asociada al código (abrir paywall, toast, etc.).
 * Devuelve el error para que el caller pueda usarlo (mostrar en UI, etc.).
 */
export function handleError(err: AppError): AppError {
    const billing = useBillingStore.getState();

    switch (err.code) {
        case 'billing.insufficient_credits':
            billing.openPaywall('402');
            break;
        case 'rag.quota_exceeded':
            billing.openPaywall('rag_full');
            break;
        case 'agents.quota_exceeded':
            billing.openPaywall('agents_full');
            break;
        case 'perm.plan_not_allowed':
            billing.openPaywall('upgrade_cta');
            break;
        case 'auth.invalid_token':
        case 'auth.expired_token':
            // Redirect a login. Mejor que reload pero por ahora simple.
            if (typeof window !== 'undefined') {
                window.location.href = '/';
            }
            break;
        case 'common.rate_limited':
            // Toast: "demasiadas peticiones, espera unos segundos".
            // (Si no hay sistema de toast aún, se queda como console.warn.)
            console.warn('Rate limited:', err.message);
            break;
        default:
            // Sin acción específica. Caller decide qué mostrar.
            break;
    }
    return err;
}

/**
 * Conveniente: parsea + handle en un paso.
 */
export async function handleResponseError(response: Response): Promise<AppError> {
    const err = await parseError(response);
    return handleError(err);
}
