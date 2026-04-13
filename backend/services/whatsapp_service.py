import logging

from twilio.rest import Client

from core.config import settings

logger = logging.getLogger(__name__)

FROM_WHATSAPP = settings.twilio_whatsapp_from
OWNER_WHATSAPP = settings.owner_whatsapp

client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_whatsapp(body: str) -> None:
    client.messages.create(
        from_=FROM_WHATSAPP,
        to=OWNER_WHATSAPP,
        body=body,
    )
    logger.info("WhatsApp sent to owner — %d chars", len(body))
