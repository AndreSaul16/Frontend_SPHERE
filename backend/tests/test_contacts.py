"""
Tests del servicio de contacts (whitelist de contactos).
"""
import pytest
from app.core.contacts_service import normalize_contact, validate_contact


class TestNormalizeContact:
    def test_email_lowercased(self):
        assert normalize_contact("email", "User@Example.COM") == "user@example.com"

    def test_email_stripped(self):
        assert normalize_contact("email", "  user@example.com  ") == "user@example.com"

    def test_phone_e164(self):
        assert normalize_contact("phone", "+34 612 345 678") == "+34612345678"

    def test_phone_adds_plus(self):
        assert normalize_contact("phone", "34612345678") == "+34612345678"

    def test_phone_removes_dashes(self):
        assert normalize_contact("phone", "+34-612-345-678") == "+34612345678"

    def test_other_types_stripped(self):
        assert normalize_contact("slack_channel", "  #general  ") == "#general"


class TestValidateContact:
    def test_valid_email(self):
        assert validate_contact("email", "user@example.com") is True

    def test_invalid_email(self):
        assert validate_contact("email", "not-an-email") is False

    def test_valid_phone(self):
        assert validate_contact("phone", "+34612345678") is True

    def test_invalid_phone(self):
        assert validate_contact("phone", "12345") is False

    def test_phone_needs_plus(self):
        assert validate_contact("phone", "34612345678") is False

    def test_other_type_nonempty(self):
        assert validate_contact("slack_channel", "#general") is True

    def test_other_type_empty(self):
        assert validate_contact("slack_channel", "") is False


@pytest.mark.asyncio
async def test_add_and_list_contacts(async_client, clean_test_data):
    """Agrega un contacto y lo lista."""
    from app.core.contacts_service import add_contact, list_contacts

    await add_contact(
        user_id="test_user_a",
        contact_type="email",
        value="team@company.com",
        display_name="Team",
        authorized_for=["calendar_create_event"],
    )

    contacts = await list_contacts("test_user_a")
    assert len(contacts) >= 1
    assert any(c["value"] == "team@company.com" for c in contacts)


@pytest.mark.asyncio
async def test_is_authorized_check(async_client, clean_test_data):
    """Verifica si un contacto está autorizado para un tool."""
    from app.core.contacts_service import add_contact, is_authorized

    await add_contact(
        user_id="test_user_a",
        contact_type="phone",
        value="+34612345678",
        authorized_for=["whatsapp_send_message"],
    )

    assert await is_authorized("test_user_a", "whatsapp_send_message", "+34612345678") is True
    assert await is_authorized("test_user_a", "whatsapp_send_message", "+34000000000") is False
    assert await is_authorized("test_user_a", "calendar_create_event", "+34612345678") is False


@pytest.mark.asyncio
async def test_invalid_email_rejected():
    """Email inválido es rechazado."""
    from app.core.contacts_service import add_contact

    with pytest.raises(ValueError, match="Formato de email inválido"):
        await add_contact(
            user_id="test_user_a",
            contact_type="email",
            value="not-an-email",
        )
