import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.engine import async_session_factory
from db.repository import create_corporate
from keyboards.inline import kb_corporate_confirm, kb_corporate_format, kb_main_menu
from services.notifications import notify_corporate_request
from states.corporate import CorporateStates
from texts.ru import FORMAT_LABELS, TEXTS

router = Router()
log = logging.getLogger(__name__)


@router.callback_query(F.data == "menu_corporate")
async def start_corporate(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CorporateStates.waiting_theater_name)
    await callback.message.answer(TEXTS["corporate_intro"])
    await callback.message.answer(TEXTS["corporate_step_theater"])
    await callback.answer()


@router.message(CorporateStates.waiting_theater_name)
async def process_theater_name(message: Message, state: FSMContext) -> None:
    await state.update_data(theater_name=message.text.strip())
    await state.set_state(CorporateStates.waiting_city)
    await message.answer(TEXTS["corporate_step_city"])


@router.message(CorporateStates.waiting_city)
async def process_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text.strip())
    await state.set_state(CorporateStates.waiting_headcount)
    await message.answer(TEXTS["corporate_step_headcount"])


@router.message(CorporateStates.waiting_headcount)
async def process_headcount(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer(TEXTS["corporate_headcount_error"])
        return
    await state.update_data(headcount=int(text))
    await state.set_state(CorporateStates.waiting_format)
    await message.answer(TEXTS["corporate_step_format"], reply_markup=kb_corporate_format())


@router.callback_query(
    CorporateStates.waiting_format,
    F.data.in_({"format_online", "format_offline"}),
)
async def process_format(callback: CallbackQuery, state: FSMContext) -> None:
    fmt = "online" if callback.data == "format_online" else "offline"
    await state.update_data(format=fmt)
    await state.set_state(CorporateStates.waiting_tasks)
    await callback.message.answer(TEXTS["corporate_step_tasks"])
    await callback.answer()


@router.message(CorporateStates.waiting_tasks)
async def process_tasks(message: Message, state: FSMContext) -> None:
    await state.update_data(tasks_text=message.text.strip())
    await state.set_state(CorporateStates.confirming)

    data = await state.get_data()
    confirm_text = TEXTS["corporate_confirm"].format(
        theater_name=data["theater_name"],
        city=data["city"],
        headcount=data["headcount"],
        format=FORMAT_LABELS[data["format"]],
        tasks_text=data["tasks_text"],
    )
    await message.answer(confirm_text, reply_markup=kb_corporate_confirm())


@router.callback_query(CorporateStates.confirming, F.data == "corporate_edit")
async def edit_corporate(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CorporateStates.waiting_theater_name)
    await callback.message.answer(TEXTS["corporate_step_theater"])
    await callback.answer()


@router.callback_query(CorporateStates.confirming, F.data == "corporate_confirm")
async def confirm_corporate(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    telegram_id = callback.from_user.id
    username = callback.from_user.username or ""

    async with async_session_factory() as session:
        req = await create_corporate(
            session=session,
            telegram_id=telegram_id,
            theater_name=data["theater_name"],
            city=data["city"],
            headcount=data["headcount"],
            format_=data["format"],
            tasks_text=data["tasks_text"],
        )

    try:
        await notify_corporate_request(req, username)
    except Exception:
        log.exception("Corporate notify failed for user %s", telegram_id)

    await callback.message.answer(
        TEXTS["corporate_success"].format(theater_name=data["theater_name"]),
        reply_markup=kb_main_menu(),
    )
    await callback.answer()
