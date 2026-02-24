import logging
from datetime import datetime, timezone

from aiogram import Bot

from config import settings
from db.models import CorporateRequest, User
from texts.ru import FORMAT_LABELS, ROLE_LABELS, TEXTS

log = logging.getLogger(__name__)

_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M UTC")


async def notify_new_application(user: User) -> None:
    assert _bot is not None
    text = TEXTS["notify_new_application"].format(
        full_name=user.full_name,
        role=ROLE_LABELS.get(user.role, user.role),
        city=user.city,
        organization=user.organization,
        referral_source=user.referral_source,
        username=user.username or "—",
        telegram_id=user.telegram_id,
        applied_at=_fmt_dt(user.applied_at),
    )
    await _bot.send_message(settings.curator_chat_id, text)


async def notify_payment_confirmed(user: User) -> None:
    assert _bot is not None
    text = TEXTS["notify_payment_confirmed"].format(
        full_name=user.full_name,
        username=user.username or "—",
        role=ROLE_LABELS.get(user.role, user.role),
        organization=user.organization,
        city=user.city,
        payment_id=user.payment_id or "—",
        paid_at=_fmt_dt(user.paid_at),
    )
    await _bot.send_message(settings.curator_chat_id, text)


async def notify_corporate_request(req: CorporateRequest, username: str) -> None:
    assert _bot is not None
    text = TEXTS["notify_corporate_request"].format(
        theater_name=req.theater_name,
        city=req.city,
        headcount=req.headcount,
        format=FORMAT_LABELS.get(req.format, req.format),
        tasks_text=req.tasks_text,
        username=username or "—",
        telegram_id=req.telegram_id,
        created_at=_fmt_dt(req.created_at),
    )
    await _bot.send_message(settings.curator_chat_id, text)


async def notify_unknown_payment(
    payment_id: str,
    telegram_id: str,
    timestamp: str,
) -> None:
    assert _bot is not None
    text = TEXTS["notify_unknown_payment"].format(
        payment_id=payment_id,
        telegram_id=telegram_id,
        timestamp=timestamp,
    )
    await _bot.send_message(settings.curator_chat_id, text)


async def notify_invite_failed(user: User) -> None:
    assert _bot is not None
    text = TEXTS["notify_invite_failed"].format(
        full_name=user.full_name,
        username=user.username or "—",
        paid_at=_fmt_dt(user.paid_at),
    )
    await _bot.send_message(settings.curator_chat_id, text)


async def notify_abandoned_application(user: User) -> None:
    assert _bot is not None
    text = TEXTS["notify_abandoned_application"].format(
        full_name=user.full_name,
        username=user.username or "—",
        role=ROLE_LABELS.get(user.role, user.role),
        started_at=_fmt_dt(user.created_at),
    )
    await _bot.send_message(settings.curator_chat_id, text)
