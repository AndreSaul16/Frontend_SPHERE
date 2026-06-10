"""
A35 (auditoría 2026-06-10): rotación de FERNET_KEY sin perder credenciales.

Verifica que CredentialsService usa MultiFernet: cifra con la clave activa y
descifra con cualquiera de las claves configuradas, de modo que rotar la clave
no deja ilegibles las credenciales ya guardadas.
"""
from unittest.mock import patch

from cryptography.fernet import Fernet

from app.core.credentials import CredentialsService, _key_version


def _new_service(keys_csv: str) -> CredentialsService:
    """Crea un CredentialsService con FERNET_KEYS parcheado."""
    with patch("app.core.credentials.settings") as mock_settings:
        mock_settings.fernet_keys_list = [
            k.strip() for k in keys_csv.split(",") if k.strip()
        ]
        return CredentialsService()


def test_roundtrip_single_key():
    key = Fernet.generate_key().decode()
    svc = _new_service(key)
    enc = svc._encrypt("secreto-123")
    assert svc._decrypt(enc) == "secreto-123"
    assert svc.key_version == _key_version(key)


def test_old_data_decrypts_after_rotation():
    """Datos cifrados con la clave vieja siguen siendo legibles tras anteponer una nueva."""
    old = Fernet.generate_key().decode()
    new = Fernet.generate_key().decode()

    # 1. Servicio con solo la clave vieja cifra un token
    old_svc = _new_service(old)
    enc_old = old_svc._encrypt("token-antiguo")

    # 2. Rotamos: nueva al frente, vieja detrás
    rotated_svc = _new_service(f"{new},{old}")

    # La credencial vieja todavía se descifra
    assert rotated_svc._decrypt(enc_old) == "token-antiguo"
    # Y los datos nuevos se cifran con la clave nueva (versión activa = new)
    assert rotated_svc.key_version == _key_version(new)
    enc_new = rotated_svc._encrypt("token-nuevo")
    assert rotated_svc._decrypt(enc_new) == "token-nuevo"


def test_decrypt_fails_when_old_key_dropped():
    """Si se elimina la clave que cifró un dato, descifrar lanza ValueError (no datos basura)."""
    old = Fernet.generate_key().decode()
    new = Fernet.generate_key().decode()

    enc_old = _new_service(old)._encrypt("token-antiguo")

    only_new = _new_service(new)
    import pytest

    with pytest.raises(ValueError):
        only_new._decrypt(enc_old)


def test_dev_mode_without_keys_is_passthrough():
    """Sin claves (dev), cifrar/descifrar es identidad y no rompe."""
    svc = _new_service("")
    enc = svc._encrypt("plano")
    assert svc._decrypt(enc) == "plano"
    assert svc.key_version == "plain"
