from fastapi import APIRouter
from app.core.database import db
from typing import Dict

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health Check mejorado.
    Verifica la conectividad real con MongoDB Atlas.
    """
    mongo_status = "unknown"
    
    try:
        # Intentamos hacer un 'ping' a la base de datos
        if db.client:
            await db.client.admin.command('ping')
            mongo_status = "connected 🟢"
        else:
            mongo_status = "disconnected 🔴 (client is None)"
    except Exception as e:
        mongo_status = f"error 🔴: {str(e)}"

    return {
        "status": "active",
        "service": "SPHERE Orchestrator",
        "database": mongo_status
    }