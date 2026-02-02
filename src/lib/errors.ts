/**
 * Sistema de Errores Tipados de SPHERE v2.0
 */

export type ErrorContext = 'fetch_agents' | 'create_session' | 'send_message' | 'load_history' | 'artifact_parser' | 'core_engine';

export class SphereError extends Error {
    constructor(
        public message: string,
        public context: ErrorContext,
        public originalError?: any
    ) {
        super(message);
        this.name = 'SphereError';
    }
}

/**
 * Fallos relacionados con la red o el backend
 */
export class NetworkError extends SphereError {
    constructor(message: string, context: ErrorContext, originalError?: any) {
        super(message, context, originalError);
        this.name = 'NetworkError';
    }
}

/**
 * Errores durante el procesamiento de datos (ej: XML malformado)
 */
export class ParserError extends SphereError {
    constructor(message: string, context: ErrorContext, originalError?: any) {
        super(message, context, originalError);
        this.name = 'ParserError';
    }
}

/**
 * Errores de sesión (expiración, ID no encontrado)
 */
export class SessionError extends SphereError {
    constructor(message: string, context: ErrorContext, originalError?: any) {
        super(message, context, originalError);
        this.name = 'SessionError';
    }
}
