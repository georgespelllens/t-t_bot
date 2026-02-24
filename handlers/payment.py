import logging
from datetime import datetime, timezone

from aiohttp import web

from config import settings
from db.engine import async_session_factory
from db.repository import get_user, mark_paid
from services.notifications import notify_payment_confirmed, notify_unknown_payment
from services.payment import verify_payment_webhook

log = logging.getLogger(__name__)


async def handle_payment_webhook(request: web.Request) -> web.Response:
    """
    Вебхук от ЮKassa / Robokassa.
    Всегда верифицировать HMAC до любой обработки данных.
    """
    body = await request.read()
    signature = request.headers.get("X-Payment-Signature", "")

    if not verify_payment_webhook(body, signature, settings.payment_webhook_secret):
        log.warning("Payment webhook: invalid signature")
        return web.Response(status=400, text="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        log.exception("Payment webhook: failed to parse JSON")
        return web.Response(status=400, text="Invalid JSON")

    payment_id = payload.get("id") or payload.get("payment_id", "")
    # Адаптируйте поле под реальный формат провайдера
    telegram_id_raw = payload.get("metadata", {}).get("telegram_id")

    if not telegram_id_raw:
        log.warning("Payment webhook: no telegram_id in metadata, payment_id=%s", payment_id)
        await notify_unknown_payment(
            payment_id=payment_id,
            telegram_id="unknown",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return web.Response(status=200, text="ok")

    telegram_id = int(telegram_id_raw)

    async with async_session_factory() as session:
        user = await mark_paid(session, telegram_id, payment_id)

    if user is None:
        log.warning(
            "Payment webhook: user not found, telegram_id=%s payment_id=%s",
            telegram_id,
            payment_id,
        )
        await notify_unknown_payment(
            payment_id=payment_id,
            telegram_id=str(telegram_id),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return web.Response(status=200, text="ok")

    log.info("Payment confirmed: user=%s payment_id=%s", telegram_id, payment_id)

    # Notify curator
    try:
        await notify_payment_confirmed(user)
    except Exception:
        log.exception("Curator payment notification failed for user %s", telegram_id)

    # Trigger onboarding (imported here to avoid circular deps)
    from handlers.onboarding import send_onboarding_d0
    try:
        await send_onboarding_d0(user)
    except Exception:
        log.exception("Onboarding D+0 failed for user %s", telegram_id)

    return web.Response(status=200, text="ok")
