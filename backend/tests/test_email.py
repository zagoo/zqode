"""Unit test for the login-code email sender (app/services/email.py).

Isolates the service from its only non-stdlib couplings — app.core.config and
app.core.errors — by stubbing them in sys.modules before import. The real
email.py logic (console vs SMTP branching, message building, the SMTP call
sequence, and failure -> error mapping) runs against those stubs and a fake
SMTP server, so this test needs only the Python standard library (no FastAPI,
SQLAlchemy, or database). It complements the integration smoke_test.py.

    python tests/test_email.py     # from backend/
"""
import asyncio
import logging
import os
import smtplib
import sys
import types

# Make `app` importable regardless of how this script is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StubDeliveryError(Exception):
    """Stand-in for errors.email_delivery_failed()."""


# --- stub app.core.config / app.core.errors so email.py imports stdlib-only ---
_settings = types.SimpleNamespace(
    EMAIL_MODE="console",
    SMTP_HOST="smtp.example.com",
    SMTP_PORT=587,
    SMTP_USERNAME="mailer@example.com",
    SMTP_PASSWORD="secret",
    SMTP_FROM="no-reply@example.com",
    SMTP_FROM_NAME="ZQode Gateway",
    SMTP_STARTTLS=True,
    SMTP_SSL=False,
    SMTP_TIMEOUT_SECONDS=15,
)

_core = types.ModuleType("app.core")
_config = types.ModuleType("app.core.config")
_config.settings = _settings
_errors = types.ModuleType("app.core.errors")
_errors.email_delivery_failed = lambda: StubDeliveryError()
_core.config = _config
_core.errors = _errors
sys.modules["app.core"] = _core
sys.modules["app.core.config"] = _config
sys.modules["app.core.errors"] = _errors

import app.services.email as email_svc  # noqa: E402

# Keep the service's expected error/exception logs (raised by the negative-path
# tests) off the console; the console-mode test attaches its own capture handler.
email_svc.log.propagate = False
email_svc.log.addHandler(logging.NullHandler())


# --- fake SMTP server capturing how email.py drives it ---
class FakeSMTP:
    last = None
    fail_on_send = False

    def __init__(self, host, port, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.kind = "SMTP"
        self.starttls_called = False
        self.login_args = None
        self.sent = []
        self.quit_called = False
        FakeSMTP.last = self

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, msg):
        if FakeSMTP.fail_on_send:
            raise smtplib.SMTPException("boom")
        self.sent.append(msg)

    def quit(self):
        self.quit_called = True


class FakeSMTPSSL(FakeSMTP):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.kind = "SMTP_SSL"


def _reset(**overrides):
    FakeSMTP.last = None
    FakeSMTP.fail_on_send = False
    smtplib.SMTP = FakeSMTP
    smtplib.SMTP_SSL = FakeSMTPSSL
    for key, value in dict(
        EMAIL_MODE="smtp", SMTP_HOST="smtp.example.com",
        SMTP_STARTTLS=True, SMTP_SSL=False,
    ).items():
        setattr(_settings, key, value)
    for key, value in overrides.items():
        setattr(_settings, key, value)


def test_console_mode_does_not_touch_smtp():
    _reset(EMAIL_MODE="console")
    logs = []
    handler = logging.Handler()
    handler.emit = lambda record: logs.append(record.getMessage())
    email_svc.log.addHandler(handler)
    try:
        result = asyncio.run(email_svc.send_login_code("user@corp.com", "483920", 5))
    finally:
        email_svc.log.removeHandler(handler)
    assert result is None
    assert FakeSMTP.last is None, "console mode must not open an SMTP connection"
    assert any("483920" in m for m in logs), "console mode should log the code"
    print("[email] console mode logs code, no SMTP — OK")


def test_smtp_starttls_happy_path():
    _reset()  # EMAIL_MODE=smtp, STARTTLS
    asyncio.run(email_svc.send_login_code("user@corp.com", "123456", 7))
    s = FakeSMTP.last
    assert s is not None and s.kind == "SMTP"
    assert (s.host, s.port) == ("smtp.example.com", 587)
    assert s.starttls_called is True
    assert s.login_args == ("mailer@example.com", "secret")
    assert len(s.sent) == 1 and s.quit_called is True
    msg = s.sent[0]
    assert msg["To"] == "user@corp.com"
    assert msg["From"] == "ZQode Gateway <no-reply@example.com>"
    assert msg.get_content_type() == "multipart/alternative"
    plain = msg.get_body(preferencelist=("plain",))
    html = msg.get_body(preferencelist=("html",))
    assert plain is not None and html is not None
    plain_text = plain.get_content()
    html_text = html.get_content()
    assert html.get_content_type() == "text/html"
    assert "123456" in plain_text, "plain-text fallback must carry the code"
    assert "123456" in html_text and "7 minutes" in html_text
    assert "<html" in html_text.lower() and "#cc785c" in html_text, "HTML must be on-brand"
    print("[email] smtp sends multipart text+HTML carrying the code — OK")


def test_smtp_ssl_skips_starttls():
    _reset(SMTP_SSL=True, SMTP_STARTTLS=False, SMTP_PORT=465)
    asyncio.run(email_svc.send_login_code("user@corp.com", "654321", 5))
    s = FakeSMTP.last
    assert s is not None and s.kind == "SMTP_SSL"
    assert s.port == 465
    assert s.starttls_called is False, "implicit-SSL must not call STARTTLS"
    assert len(s.sent) == 1
    print("[email] smtp SSL path skips STARTTLS — OK")


def test_smtp_send_failure_raises_delivery_error():
    _reset()
    FakeSMTP.fail_on_send = True
    try:
        asyncio.run(email_svc.send_login_code("user@corp.com", "111111", 5))
    except StubDeliveryError:
        print("[email] smtp send failure -> email_delivery_failed — OK")
    else:
        raise AssertionError("expected email_delivery_failed on SMTP failure")


def test_smtp_missing_host_raises_without_connecting():
    _reset(SMTP_HOST="")
    try:
        asyncio.run(email_svc.send_login_code("user@corp.com", "222222", 5))
    except StubDeliveryError:
        assert FakeSMTP.last is None, "must not connect when SMTP_HOST is unset"
        print("[email] smtp with empty host -> error, no connection — OK")
    else:
        raise AssertionError("expected email_delivery_failed when SMTP_HOST is empty")


if __name__ == "__main__":
    test_console_mode_does_not_touch_smtp()
    test_smtp_starttls_happy_path()
    test_smtp_ssl_skips_starttls()
    test_smtp_send_failure_raises_delivery_error()
    test_smtp_missing_host_raises_without_connecting()
    print("\nAll email-sender tests passed.")
