import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from config import settings
from db.engine import async_session_factory
from db.models import User
from db.repository import (
    get_paid_users_without_onboarding,
    has_onboarding_message,
    log_onboarding,
    update_status,
)
from services.notifications import notify_invite_failed
from texts.ru import TEXTS

log = logging.getLogger(__name__)

_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


def _format_date(d: datetime | None) -> str:
    if d is None:
        return "7 апреля 2026"
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    }
    return f"{d.day} {months[d.month]} {d.year}"


PROGRAM_DATE_STR = _format_date(
    datetime(
        settings.program_start_date.year,
        settings.program_start_date.month,
        settings.program_start_date.day,
    )
)


async def send_onboarding_d0(user: User) -> None:
    """D+0: поздравление + PDF + invite. Запускается сразу после подтверждения оплаты."""
    assert _bot is not None, "Bot not initialised in onboarding module"

    tid = user.telegram_id

    # 1. Welcome message
    if not await _has_sent(tid, "welcome_paid"):
        await _bot.send_message(
            tid,
            TEXTS["onboarding_welcome_paid"].format(
                full_name=user.full_name,
                program_start_date=PROGRAM_DATE_STR,
            ),
        )
        await _mark_sent(tid, "welcome_paid")
        await asyncio.sleep(1)

    # 2. Program PDF — TODO: положить PDF в /content/program.pdf и раскомментировать
    if not await _has_sent(tid, "doc"):
        await _bot.send_message(tid, TEXTS["onboarding_doc"])
        # await _bot.send_document(tid, FSInputFile("content/program.pdf"))
        await _mark_sent(tid, "doc")
        await asyncio.sleep(1)

    # 3. Invite link
    if not await _has_sent(tid, "invite"):
        await _send_invite(user)


async def _send_invite(user: User) -> None:
    assert _bot is not None
    tid = user.telegram_id
    try:
        expire = datetime.now(timezone.utc) + timedelta(hours=48)
        link = await _bot.create_chat_invite_link(
            chat_id=settings.closed_chat_id,
            member_limit=1,
            expire_date=expire,
        )
        await _bot.send_message(
            tid,
            TEXTS["onboarding_invite"].format(invite_link=link.invite_link),
        )
    except Exception:
        log.exception("Failed to create invite link for user %s", tid)
        await notify_invite_failed(user)
    finally:
        await _mark_sent(tid, "invite")


async def send_reminder_d1(user: User) -> None:
    assert _bot is not None
    if not await _has_sent(user.telegram_id, "reminder_d1"):
        await _bot.send_message(
            user.telegram_id,
            TEXTS["onboarding_reminder_d1"].format(full_name=user.full_name),
        )
        await _mark_sent(user.telegram_id, "reminder_d1")


async def send_reminder_d3(user: User) -> None:
    assert _bot is not None
    if not await _has_sent(user.telegram_id, "reminder_d3"):
        await _bot.send_message(
            user.telegram_id,
            TEXTS["onboarding_reminder_d3"],
        )
        await _mark_sent(user.telegram_id, "reminder_d3")


async def send_reminder_d7(user: User) -> None:
    assert _bot is not None
    if not await _has_sent(user.telegram_id, "reminder_d7"):
        await _bot.send_message(
            user.telegram_id,
            TEXTS["onboarding_reminder_d7"].format(
                full_name=user.full_name,
                program_start_date=PROGRAM_DATE_STR,
            ),
        )
        await _mark_sent(user.telegram_id, "reminder_d7")


# ── Scheduler jobs ────────────────────────────────────────────────────────────

async def job_send_d1() -> None:
    async with async_session_factory() as session:
        users = await get_paid_users_without_onboarding(session, "reminder_d1")
    for user in users:
        try:
            await send_reminder_d1(user)
        except Exception:
            log.exception("D+1 reminder failed for user %s", user.telegram_id)


async def job_send_d3() -> None:
    async with async_session_factory() as session:
        users = await get_paid_users_without_onboarding(session, "reminder_d3")
    for user in users:
        try:
            await send_reminder_d3(user)
        except Exception:
            log.exception("D+3 reminder failed for user %s", user.telegram_id)


async def job_send_d7() -> None:
    async with async_session_factory() as session:
        users = await get_paid_users_without_onboarding(session, "reminder_d7")
    for user in users:
        try:
            await send_reminder_d7(user)
        except Exception:
            log.exception("D-7 reminder failed for user %s", user.telegram_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _has_sent(telegram_id: int, message_key: str) -> bool:
    async with async_session_factory() as session:
        return await has_onboarding_message(session, telegram_id, message_key)


async def _mark_sent(telegram_id: int, message_key: str) -> None:
    async with async_session_factory() as session:
        await log_onboarding(session, telegram_id, message_key)
