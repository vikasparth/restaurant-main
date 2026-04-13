import logging

import resend

from core.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key
FROM_EMAIL = settings.resend_from_email


async def send_email(to: str, subject: str, html_body: str) -> None:
    params = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }
    resend.Emails.send(params)
    logger.info("Email sent to %s — subject: %s", to, subject)
