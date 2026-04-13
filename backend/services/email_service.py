import logging
import os

import resend

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

async def send_email(to: str, subject: str, html_body: str) -> None:
    params = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }
    resend.Emails.send(params)
    logger.info("Email sent to %s — subject: %s", to, subject)
