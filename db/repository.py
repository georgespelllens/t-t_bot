from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CorporateRequest, OnboardingLog, User


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str,
    role: str,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=role,
        city="",
        organization="",
        referral_source="",
        status="new",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def upsert_user_role(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str,
    role: str,
) -> User:
    user = await get_user(session, telegram_id)
    if user is None:
        return await create_user(session, telegram_id, username, full_name, role)
    user.role = role
    user.username = username
    user.full_name = full_name
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_application(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    city: str,
    organization: str,
    referral_source: str,
) -> None:
    user = await get_user(session, telegram_id)
    if user is None:
        return
    user.full_name = full_name
    user.city = city
    user.organization = organization
    user.referral_source = referral_source
    user.status = "applied"
    user.applied_at = datetime.now(timezone.utc)
    await session.commit()


async def update_status(
    session: AsyncSession,
    telegram_id: int,
    status: str,
) -> User | None:
    user = await get_user(session, telegram_id)
    if user is None:
        return None
    user.status = status
    await session.commit()
    await session.refresh(user)
    return user


async def mark_paid(
    session: AsyncSession,
    telegram_id: int,
    payment_id: str,
) -> User | None:
    user = await get_user(session, telegram_id)
    if user is None:
        return None
    user.status = "paid"
    user.paid_at = datetime.now(timezone.utc)
    user.payment_id = payment_id
    await session.commit()
    await session.refresh(user)
    return user


async def get_incomplete_applications(session: AsyncSession) -> list[User]:
    """Пользователи, начавшие заявку, но не завершившие её (applied_at IS NULL, статус new)."""
    result = await session.execute(
        select(User).where(User.status == "new", User.city == "")
    )
    return list(result.scalars().all())


# ── OnboardingLog ─────────────────────────────────────────────────────────────

async def log_onboarding(
    session: AsyncSession,
    telegram_id: int,
    message_key: str,
) -> OnboardingLog:
    log = OnboardingLog(
        telegram_id=telegram_id,
        message_key=message_key,
        sent_at=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return log


async def has_onboarding_message(
    session: AsyncSession,
    telegram_id: int,
    message_key: str,
) -> bool:
    result = await session.execute(
        select(OnboardingLog).where(
            OnboardingLog.telegram_id == telegram_id,
            OnboardingLog.message_key == message_key,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_paid_users_without_onboarding(
    session: AsyncSession,
    message_key: str,
) -> list[User]:
    sent_subq = (
        select(OnboardingLog.telegram_id)
        .where(OnboardingLog.message_key == message_key)
        .scalar_subquery()
    )
    result = await session.execute(
        select(User).where(
            User.status.in_(["paid", "onboarded"]),
            User.telegram_id.not_in(sent_subq),
        )
    )
    return list(result.scalars().all())


# ── CorporateRequest ──────────────────────────────────────────────────────────

async def create_corporate(
    session: AsyncSession,
    telegram_id: int,
    theater_name: str,
    city: str,
    headcount: int,
    format_: str,
    tasks_text: str,
) -> CorporateRequest:
    req = CorporateRequest(
        telegram_id=telegram_id,
        theater_name=theater_name,
        city=city,
        headcount=headcount,
        format=format_,
        tasks_text=tasks_text,
        created_at=datetime.now(timezone.utc),
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req
