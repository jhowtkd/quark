"""Tests for log_sanitizer module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.log_sanitizer import sanitize_log_message, DEFAULT_MAX_POST_LENGTH, TRUNCATION_SUFFIX


class TestSanitizeLogMessage:
    """Verify log message sanitization rules."""

    def test_email_redaction(self):
        raw = "User login: alice@example.com attempted access"
        result = sanitize_log_message(raw)
        assert "alice@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_multiple_emails(self):
        raw = "Contacts: a@b.com and c@d.org"
        result = sanitize_log_message(raw)
        assert "a@b.com" not in result
        assert "c@d.org" not in result
        assert result.count("[EMAIL_REDACTED]") == 2

    def test_cpf_with_format(self):
        raw = "CPF do usuario: 123.456.789-09"
        result = sanitize_log_message(raw)
        assert "123.456.789-09" not in result
        assert "[CPF_REDACTED]" in result

    def test_cpf_raw(self):
        raw = "CPF raw: 12345678909"
        result = sanitize_log_message(raw)
        assert "12345678909" not in result
        # 11 位数字可能与电话号码重叠，只要被脱敏即可
        assert ("[CPF_REDACTED]" in result or "[PHONE_REDACTED]" in result)

    def test_phone_with_dash(self):
        raw = "Phone: (11) 98765-4321"
        result = sanitize_log_message(raw)
        assert "(11) 98765-4321" not in result
        assert "[PHONE_REDACTED]" in result

    def test_phone_without_dash(self):
        raw = "Phone: 11987654321"
        result = sanitize_log_message(raw)
        assert "11987654321" not in result
        assert "[PHONE_REDACTED]" in result

    def test_truncation(self):
        raw = "x" * (DEFAULT_MAX_POST_LENGTH + 50)
        result = sanitize_log_message(raw)
        assert result.endswith(TRUNCATION_SUFFIX)
        assert len(result) == DEFAULT_MAX_POST_LENGTH + len(TRUNCATION_SUFFIX)

    def test_truncation_with_custom_length(self):
        raw = "hello world"
        result = sanitize_log_message(raw, max_post_length=5)
        assert result == "hello" + TRUNCATION_SUFFIX

    def test_no_truncation_when_short(self):
        raw = "Short message"
        result = sanitize_log_message(raw)
        assert TRUNCATION_SUFFIX not in result
        assert result == raw

    def test_combined_sensitive_data(self):
        raw = "User joao@email.com with CPF 111.222.333-44 and phone (11) 91234-5678 logged in"
        result = sanitize_log_message(raw)
        assert "joao@email.com" not in result
        assert "111.222.333-44" not in result
        assert "(11) 91234-5678" not in result
        assert "[EMAIL_REDACTED]" in result
        assert "[CPF_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result

    def test_non_string_input(self):
        result = sanitize_log_message(12345)
        assert result == "12345"

    def test_empty_string(self):
        result = sanitize_log_message("")
        assert result == ""
