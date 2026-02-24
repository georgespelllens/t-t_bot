import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from db.engine import async_session_factory
from db.repository import get_user, update_user_application
from keyboards.inline import (
    kb_application_confirm,
    kb_main_menu,
    kb_payment_link,
    kb_referral_source,
)
from services.notifications import notify_new_application
from states.application import ApplicationStates
from texts.ru import REFERRAL_LABELS, ROLE_LABELS, TEXTS

router = Router()
log = logging.getLogger(__name__)


@router.callback_query(F.data == "menu_apply")
async def start_application(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ApplicationStates.waiting_name)

    async with async_session_factory() as session:
        user = await get_user(session, callback.from_user.id)

    # Pre-fill name from Telegram profile as hint
    name_hint = callback.from_user.full_name or ""
    await state.update_data(prefill_name=name_hint)

    await callback.message.answer(TEXTS["apply_step_name"])
    await callback.answer()


@router.message(ApplicationStates.waiting_name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ApplicationStates.waiting_city)
    await message.answer(TEXTS["apply_step_city"])


@router.message(ApplicationStates.waiting_city)
async def process_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text.strip())
    await state.set_state(ApplicationStates.waiting_organization)
    await message.answer(TEXTS["apply_step_organization"])


@router.message(ApplicationStates.waiting_organization)
async def process_organization(message: Message, state: FSMContext) -> None:
    await state.update_data(organization=message.text.strip())
    await state.set_state(ApplicationStates.waiting_referral)
    await message.answer(TEXTS["apply_step_referral"], reply_markup=kb_referral_source())


@router.callback_query(
    ApplicationStates.waiting_referral,
    F.data.in_({"ref_landing", "ref_telegram", "ref_recommendation", "ref_other"}),
)
async def process_referral(callback: CallbackQuery, state: FSMContext) -> None:
    ref_map = {
        "ref_landing": "landing",
        "ref_telegram": "telegram",
        "ref_recommendation": "recommendation",
        "ref_other": "other",
    }
    referral_key = ref_map[callback.data]
    await state.update_data(referral_source=referral_key)
    await state.set_state(ApplicationStates.confirming)

    data = await state.get_data()
    confirm_text = TEXTS["apply_confirm"].format(
        full_name=data["full_name"],
        city=data["city"],
        organization=data["organization"],
        referral_source=REFERRAL_LABELS[referral_key],
    )
    await callback.message.answer(confirm_text, reply_markup=kb_application_confirm())
    await callback.answer()


@router.callback_query(ApplicationStates.confirming, F.data == "apply_edit")
async def edit_application(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ApplicationStates.waiting_name)
    await callback.message.answer(TEXTS["apply_step_name"])
    await callback.answer()


@router.callback_query(ApplicationStates.confirming, F.data == "apply_confirm")
async def confirm_application(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    telegram_id = callback.from_user.id
    username = callback.from_user.username or ""

    async with async_session_factory() as session:
        await update_user_application(
            session=session,
            telegram_id=telegram_id,
            full_name=data["full_name"],
            city=data["city"],
            organization=data["organization"],
            referral_source=data["referral_source"],
        )
        user = await get_user(session, telegram_id)

    # Notify curator
    try:
        await notify_new_application(user)
    except Exception:
        log.exception("Curator notification failed for user %s", telegram_id)

    await callback.message.answer(TEXTS["apply_success"])
    await callback.message.answer(
        settings.payment_link,
        reply_markup=kb_payment_link(settings.payment_link),
    )
    await callback.answer()
