"""Login-code delivery — console (dev) logging or SMTP (production) email.

Uses only the Python standard library (smtplib/email), so it adds no
third-party dependency to the locked backend stack. The blocking SMTP call is
offloaded to a worker thread via ``asyncio.to_thread`` so it never blocks the
async request path (ARCHITECTURE §2.2).
"""
import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core import errors
from app.core.config import settings

log = logging.getLogger(__name__)


def _html_body(code: str, expires_minutes: int) -> str:
    """On-brand HTML body. Mail clients don't support CSS custom properties, so
    DESIGN.md tokens are inlined as hex and the licensed brand fonts fall back
    to web-safe stacks. `code` is numeric and `expires_minutes` an int, so no
    HTML escaping is required."""
    sans = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    serif = "Georgia,'Times New Roman',serif"
    mono = "'JetBrains Mono','SF Mono',Consolas,monospace"
    return f"""\
<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background-color:#faf9f5;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#faf9f5;padding:32px 0;">
      <tr><td align="center">
        <table role="presentation" cellpadding="0" cellspacing="0" width="480" style="max-width:480px;background-color:#ffffff;border:1px solid #e6dfd8;border-radius:12px;">
          <tr><td style="padding:32px 40px;font-family:{sans};">
            <div style="font-size:18px;color:#141413;margin-bottom:28px;">
              <span style="color:#cc785c;">&#10043;</span>
              <span style="font-family:{serif};letter-spacing:-0.2px;">&nbsp;ZQode Gateway</span>
            </div>
            <h1 style="margin:0 0 12px;font-family:{serif};font-weight:400;font-size:26px;line-height:1.2;letter-spacing:-0.5px;color:#141413;">Your login code</h1>
            <p style="margin:0 0 24px;font-size:15px;line-height:1.5;color:#3d3d3a;">Use this one-time code to sign in. It expires in {expires_minutes} minutes.</p>
            <div style="background-color:#f5f0e8;border:1px solid #e6dfd8;border-radius:8px;padding:20px;text-align:center;margin-bottom:24px;">
              <span style="font-family:{mono};font-size:34px;font-weight:700;letter-spacing:8px;color:#141413;">{code}</span>
            </div>
            <p style="margin:0;font-size:13px;line-height:1.5;color:#6c6a64;">If you did not try to sign in, you can safely ignore this email.</p>
          </td></tr>
        </table>
        <div style="max-width:480px;margin-top:16px;font-family:{sans};font-size:12px;color:#8e8b82;text-align:center;">ZQode — Internal Enterprise LLM Gateway</div>
      </td></tr>
    </table>
  </body>
</html>"""


def _build_message(to_email: str, code: str, expires_minutes: int) -> EmailMessage:
    sender = settings.SMTP_FROM or settings.SMTP_USERNAME
    msg = EmailMessage()
    msg["Subject"] = "Your ZQode login code"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{sender}>" if settings.SMTP_FROM_NAME else sender
    msg["To"] = to_email
    # Plain-text part first = the fallback for text-only clients; add_alternative
    # then makes this a multipart/alternative message preferring the HTML body.
    msg.set_content(
        f"Your one-time login code is: {code}\n\n"
        f"It expires in {expires_minutes} minutes.\n"
        f"If you did not try to sign in, you can ignore this email."
    )
    msg.add_alternative(_html_body(code, expires_minutes), subtype="html")
    return msg


def _send_via_smtp(msg: EmailMessage) -> None:
    """Blocking SMTP send. Call only through ``asyncio.to_thread``."""
    timeout = settings.SMTP_TIMEOUT_SECONDS
    if settings.SMTP_SSL:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
    try:
        if settings.SMTP_STARTTLS and not settings.SMTP_SSL:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
    finally:
        server.quit()


async def send_login_code(to_email: str, code: str, expires_minutes: int) -> None:
    """Deliver a one-time login code.

    EMAIL_MODE=console (dev): log the code to the backend logs.
    EMAIL_MODE=smtp: email it; raises ``email_delivery_failed`` on any failure
    so the caller can surface a retryable error instead of silently dropping
    the code.
    """
    if settings.EMAIL_MODE != "smtp":
        log.warning("email.console login_code=%s email=%s", code, to_email)
        return

    if not settings.SMTP_HOST:
        log.error("EMAIL_MODE=smtp but SMTP_HOST is not configured")
        raise errors.email_delivery_failed()

    try:
        await asyncio.to_thread(_send_via_smtp, _build_message(to_email, code, expires_minutes))
    except Exception:
        log.exception("email.smtp delivery failed email=%s", to_email)
        raise errors.email_delivery_failed()
    log.info("email.smtp login code delivered email=%s", to_email)
