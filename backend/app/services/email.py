from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_mail_config() -> ConnectionConfig:
    """Build ConnectionConfig at call time to always pick up the latest env vars."""
    username = os.getenv("MAIL_USERNAME", "")
    password = os.getenv("MAIL_PASSWORD", "")
    return ConnectionConfig(
        MAIL_USERNAME=username,
        MAIL_PASSWORD=password,
        MAIL_FROM=(
            os.getenv("MAIL_FROM")
            or username
            or "no-reply@example.com"
        ),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_STARTTLS=_as_bool(os.getenv("MAIL_STARTTLS"), True),
        MAIL_SSL_TLS=_as_bool(os.getenv("MAIL_SSL_TLS"), False),
        USE_CREDENTIALS=bool(username and password),
        SUPPRESS_SEND=_as_bool(os.getenv("MAIL_SUPPRESS_SEND"), False),
    )


async def send_ticket_email(
    email_to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None
):
    conf = _get_mail_config()
    logger.info(
        f"[EMAIL] Sending to={email_to!r} via {conf.MAIL_SERVER}:{conf.MAIL_PORT} "
        f"from={conf.MAIL_FROM!r} ssl={conf.MAIL_SSL_TLS} starttls={conf.MAIL_STARTTLS} "
        f"credentials={'yes' if conf.USE_CREDENTIALS else 'NO — check MAIL_PASSWORD'}"
    )
    fm = FastMail(conf)
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html",
        attachments=attachments or []
    )
    try:
        await fm.send_message(message)
        logger.info(f"[EMAIL] ✅ Successfully sent to {email_to!r}")
    except Exception as exc:
        logger.error(f"[EMAIL] ❌ Failed to send email to {email_to!r}: {exc}", exc_info=True)


