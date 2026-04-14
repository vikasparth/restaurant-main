import asyncio
import logging

from core.config import settings
from services.email_service import send_email
from services.whatsapp_service import send_whatsapp

logger = logging.getLogger(__name__)

OWNER_EMAIL = settings.owner_email


async def notify_order(order_data: dict) -> None:
    """Fire customer + owner email and owner WhatsApp for a new order. Never raises."""
    if not settings.notifications_enabled:
        return
    ref = order_data["reference_number"]
    customer_email = order_data["customer_email"]
    subject = f"Order Confirmed — {ref}"

    items_html = "".join(
        f"<li>{item['name']} x{item['quantity']} — ${item['price']:.2f}</li>"
        for item in order_data["line_items"]
    )
    customer_html = f"""
        <h2>Your order is confirmed!</h2>
        <p>Reference: <strong>{ref}</strong></p>
        <p>Type: {order_data['order_type'].capitalize()}</p>
        <p>Scheduled: {order_data['scheduled_time']}</p>
        <ul>{items_html}</ul>
        <p>Total: <strong>${order_data['total_amount']:.2f}</strong></p>
    """

    try:
        await send_email(customer_email, subject, customer_html)
        asyncio.create_task(
            _log_notification("resend", "email", "order_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Order customer email failed: %s", e)
        asyncio.create_task(
            _log_notification("resend", "email", "order_confirmed", ref, False, str(e))
        )

    owner_body = (
        f"New Order — {ref}\n"
        f"Customer: {order_data['customer_name']}\n"
        f"Phone: {order_data['customer_phone']}\n"
        f"Type: {order_data['order_type']}\n"
        f"Scheduled: {order_data['scheduled_time']}\n"
        f"Total: ${order_data['total_amount']:.2f}"
    )
    try:
        await send_email(OWNER_EMAIL, f"[New Order] {ref}", f"<pre>{owner_body}</pre>")
        asyncio.create_task(
            _log_notification("resend", "email", "order_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Order owner email failed: %s", e)
        asyncio.create_task(
            _log_notification("resend", "email", "order_confirmed", ref, False, str(e))
        )

    try:
        await send_whatsapp(owner_body)
        asyncio.create_task(
            _log_notification("twilio", "whatsapp", "order_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Order WhatsApp failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "twilio", "whatsapp", "order_confirmed", ref, False, str(e)
            )
        )


async def notify_reservation(reservation_data: dict) -> None:
    """Fire customer (if email present) + owner email and owner WhatsApp. Never raises."""
    if not settings.notifications_enabled:
        return
    customer_email = reservation_data.get("customer_email")
    ref = reservation_data["reference_number"]
    subject = f"Reservation Confirmed — {ref}"

    if customer_email:
        customer_html = f"""
            <h2>Your reservation is confirmed!</h2>
            <p>Reference: <strong>{ref}</strong></p>
            <p>Date: {reservation_data['reservation_date']}</p>
            <p>Time: {reservation_data['reservation_time']}</p>
            <p>Party size: {reservation_data['party_size']}</p>
        """
        try:
            await send_email(customer_email, subject, customer_html)
            asyncio.create_task(
                _log_notification("resend", "email", "reservation_confirmed", ref, True)
            )
        except Exception as e:
            logger.error("Reservation customer email failed: %s", e)
            asyncio.create_task(
                _log_notification(
                    "resend", "email", "reservation_confirmed", ref, False, str(e)
                )
            )

    owner_body = (
        f"New Reservation — {ref}\n"
        f"Customer: {reservation_data['customer_name']}\n"
        f"Phone: {reservation_data['customer_phone']}\n"
        f"Date: {reservation_data['reservation_date']}\n"
        f"Time: {reservation_data['reservation_time']}\n"
        f"Party size: {reservation_data['party_size']}"
    )
    try:
        await send_email(
            OWNER_EMAIL, f"[New Reservation] {ref}", f"<pre>{owner_body}</pre>"
        )
        asyncio.create_task(
            _log_notification("resend", "email", "reservation_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Reservation owner email failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "resend", "email", "reservation_confirmed", ref, False, str(e)
            )
        )

    try:
        await send_whatsapp(owner_body)
        asyncio.create_task(
            _log_notification("twilio", "whatsapp", "reservation_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Reservation WhatsApp failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "twilio", "whatsapp", "reservation_confirmed", ref, False, str(e)
            )
        )


async def notify_catering(catering_data: dict) -> None:
    """Fire customer + owner email and owner WhatsApp for a catering order. Never raises."""
    if not settings.notifications_enabled:
        return
    ref = catering_data["reference_number"]
    customer_email = catering_data["customer_email"]
    subject = f"Catering Order Confirmed — {ref}"

    items_html = "".join(
        f"<li>{item['name']} — {item['trays']} tray(s) @ ${item['price_per_tray']:.2f}</li>"
        for item in catering_data["line_items"]
    )
    customer_html = f"""
        <h2>Your catering order is confirmed!</h2>
        <p>Reference: <strong>{ref}</strong></p>
        <p>Event date: {catering_data['event_date']} at {catering_data['event_time']}</p>
        <p>Delivery address: {catering_data['delivery_address']}</p>
        <ul>{items_html}</ul>
        <p>Total: <strong>${catering_data['total_amount']:.2f}</strong></p>
        <p><strong>A deposit of ${catering_data['deposit_amount']:.2f} is required.
        Our team will contact you within 24 hours to arrange payment.</strong></p>
    """

    try:
        await send_email(customer_email, subject, customer_html)
        asyncio.create_task(
            _log_notification("resend", "email", "catering_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Catering customer email failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "resend", "email", "catering_confirmed", ref, False, str(e)
            )
        )

    owner_body = (
        f"New Catering Order — {ref}\n"
        f"Customer: {catering_data['customer_name']}\n"
        f"Phone: {catering_data['customer_phone']}\n"
        f"Event: {catering_data['event_date']} at {catering_data['event_time']}\n"
        f"Address: {catering_data['delivery_address']}\n"
        f"Total: ${catering_data['total_amount']:.2f}\n"
        f"Deposit: ${catering_data['deposit_amount']:.2f}"
    )
    try:
        await send_email(
            OWNER_EMAIL, f"[New Catering] {ref}", f"<pre>{owner_body}</pre>"
        )
        asyncio.create_task(
            _log_notification("resend", "email", "catering_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Catering owner email failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "resend", "email", "catering_confirmed", ref, False, str(e)
            )
        )

    try:
        await send_whatsapp(owner_body)
        asyncio.create_task(
            _log_notification("twilio", "whatsapp", "catering_confirmed", ref, True)
        )
    except Exception as e:
        logger.error("Catering WhatsApp failed: %s", e)
        asyncio.create_task(
            _log_notification(
                "twilio", "whatsapp", "catering_confirmed", ref, False, str(e)
            )
        )


async def send_reservation_reminders(db) -> int:
    """Query tomorrow's confirmed reservations, send reminder emails. Returns count sent."""
    from datetime import date, timedelta

    tomorrow = date.today() + timedelta(days=1)
    rows = await db.fetch(
        """
        SELECT reference_number, customer_name, customer_email,
               reserved_date::text, reserved_time, party_size
        FROM   reservations
        WHERE  reserved_date = $1
          AND  status = 'confirmed'
          AND  customer_email IS NOT NULL
        """,
        tomorrow,
    )

    sent = 0
    for row in rows:
        subject = f"Reminder: Your reservation tomorrow at {row['reserved_time']}"
        html = f"""
            <h2>See you tomorrow!</h2>
            <p>Reference: <strong>{row['reference_number']}</strong></p>
            <p>Date: {row['reserved_date']}</p>
            <p>Time: {row['reserved_time']}</p>
            <p>Party size: {row['party_size']}</p>
        """
        try:
            await send_email(row["customer_email"], subject, html)
            sent += 1
            asyncio.create_task(
                _log_notification(
                    "resend",
                    "email",
                    "reservation_reminder",
                    row["reference_number"],
                    True,
                )
            )
        except Exception as e:
            logger.error("Reminder email failed for %s: %s", row["reference_number"], e)
            asyncio.create_task(
                _log_notification(
                    "resend",
                    "email",
                    "reservation_reminder",
                    row["reference_number"],
                    False,
                    str(e),
                )
            )

    return sent


async def _log_notification(
    provider: str,
    channel: str,
    event_type: str,
    reference: str,
    success: bool,
    error_code: str | None = None,
) -> None:
    try:
        from core.database import get_pool

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO notification_logs
                    (provider, channel, event_type, reference, success, error_code)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                provider,
                channel,
                event_type,
                reference,
                success,
                error_code,
            )
    except Exception:
        logger.exception("Failed to write notification log — continuing")
