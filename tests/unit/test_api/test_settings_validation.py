"""Tests for settings input validation."""

import pytest
from pydantic import ValidationError

from src.api.routes.settings import SettingsUpdate


class TestPhoneValidation:
    """Test WhatsApp phone number validation."""

    def test_valid_phone_number_accepted(self):
        update = SettingsUpdate(whatsapp_recipient="+972501234567")
        assert update.whatsapp_recipient == "+972501234567"

    def test_valid_phone_without_plus(self):
        update = SettingsUpdate(whatsapp_recipient="972501234567")
        assert update.whatsapp_recipient == "972501234567"

    def test_invalid_phone_rejected(self):
        with pytest.raises(ValidationError, match="Invalid phone number"):
            SettingsUpdate(whatsapp_recipient="abc123")

    def test_too_short_phone_rejected(self):
        with pytest.raises(ValidationError, match="Invalid phone number"):
            SettingsUpdate(whatsapp_recipient="+123")

    def test_empty_string_allowed(self):
        update = SettingsUpdate(whatsapp_recipient="")
        assert update.whatsapp_recipient == ""

    def test_none_allowed(self):
        update = SettingsUpdate(whatsapp_recipient=None)
        assert update.whatsapp_recipient is None


class TestEmailValidation:
    """Test email recipient validation."""

    def test_valid_email_accepted(self):
        update = SettingsUpdate(email_recipient="user@example.com")
        assert update.email_recipient == "user@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            SettingsUpdate(email_recipient="not-an-email")

    def test_empty_string_allowed(self):
        update = SettingsUpdate(email_recipient="")
        assert update.email_recipient == ""

    def test_none_allowed(self):
        update = SettingsUpdate(email_recipient=None)
        assert update.email_recipient is None


class TestNotificationMethodValidation:
    """Test notification method validation."""

    @pytest.mark.parametrize("method", ["email", "whatsapp", "both", "none"])
    def test_valid_methods_accepted(self, method):
        update = SettingsUpdate(notification_method=method)
        assert update.notification_method == method

    def test_invalid_method_rejected(self):
        with pytest.raises(ValidationError, match="Invalid notification method"):
            SettingsUpdate(notification_method="sms")

    def test_none_allowed(self):
        update = SettingsUpdate(notification_method=None)
        assert update.notification_method is None


class TestLanguageValidation:
    """Test summary language validation."""

    @pytest.mark.parametrize("lang", ["auto", "en", "he", "ar"])
    def test_valid_languages_accepted(self, lang):
        update = SettingsUpdate(summary_language=lang)
        assert update.summary_language == lang

    def test_invalid_language_rejected(self):
        with pytest.raises(ValidationError, match="Invalid language code"):
            SettingsUpdate(summary_language="klingon")

    def test_none_allowed(self):
        update = SettingsUpdate(summary_language=None)
        assert update.summary_language is None
