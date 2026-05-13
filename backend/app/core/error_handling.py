"""
Error response sanitization.
Nunca expone stack traces, nombres de colecciones ni str(e) crudo al cliente.
"""
from fastapi import HTTPException
from app.core.logger import api_logger as logger


def safe_error_response(exc: Exception, fallback_message: str = "Error interno del servidor") -> dict:
    """
    Genera una respuesta de error segura para el cliente.
    
    - Log completo en servidor (para debugging)
    - Cliente recibe solo error_code + message genérico
    - NUNCA incluye str(e) directo, stack traces, ni nombres de colecciones
    """
    # Log completo en servidor
    logger.error(f"Error interno: {type(exc).__name__}: {exc}", exc_info=True)

    # Si ya es un HTTPException, respetar su detail
    if isinstance(exc, HTTPException):
        return {"error_code": "http_error", "message": str(exc.detail)}

    # Para errores internos, mensaje genérico
    error_code = type(exc).__name__

    # Algunos errores conocidos con mensajes más descriptivos
    known_errors = {
        "CircuitOpenError": ("service_unavailable", "Servicio temporalmente no disponible. Intenta en unos segundos."),
        "ConnectionError": ("connection_error", "Error de conexión con servicios externos."),
        "TimeoutError": ("timeout", "La operación tardó demasiado. Intenta de nuevo."),
        "ValidationError": ("validation_error", "Datos de entrada inválidos."),
    }

    if error_code in known_errors:
        code, message = known_errors[error_code]
        return {"error_code": code, "message": message}

    return {"error_code": "internal_error", "message": fallback_message}
