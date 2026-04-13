import logging
import os

from twilio.rest import Client

logger = logging.getLogger(__name__)

_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
FROM_WHATSAPP = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
OWNER_WHATSAPP = os.environ.get("OWNER_WHATSAPP", "")

client = Client(_account_sid, _auth_token)


async def send_whatsapp(body: str) -> None:
    client.messages.create(
        from_=FROM_WHATSAPP,
        to=OWNER_WHATSAPP,
        body=body,
    )
    logger.info("WhatsApp sent to owner — %d chars", len(body))
