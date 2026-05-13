"""
Modelo de credenciales OAuth cifradas en reposo.
Cada usuario tiene sus propios tokens por provider.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OAuthCredential(BaseModel):
    user_id: str
    provider: str  # "github", "notion", "slack"
    access_token_enc: bytes  # Cifrado con Fernet
    refresh_token_enc: Optional[bytes] = None
    scopes: list[str] = []
    expires_at: Optional[datetime] = None
    connected_at: datetime
    revoked_at: Optional[datetime] = None


class OAuthCredentialResponse(BaseModel):
    """Respuesta pública (sin tokens)."""
    provider: str
    scopes: list[str] = []
    connected_at: datetime
    expires_at: Optional[datetime] = None
    revoked: bool = False
