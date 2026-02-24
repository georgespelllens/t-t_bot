import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from db.engine import async_session_factory
from db.repository import upsert_user_role
from keyboards.inline import kb_main_menu, kb_roles
from texts.ru import TEXTS

router = Router()
log = logging.getLogger(__name__)

ROLE_CALLBACKS = {
    "role_artistic_director",
    "role_director",
    "role_set_designer",
    "role_producer",
    "role_pr_marketing",
    "role_tech_expert",
}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(TEXTS["welcome"], reply_markup=kb_roles())


@router.callback_query(F.data.in_(ROLE_CALLBACKS))
async def handle_role_selection(callback: CallbackQuery) -> None:
    role = callback.data  # e.g. "role_director"
    role_key = role  # same as text key in TEXTS

    async with async_session_factory() as session:
        await upsert_user_role(
            session=session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            role=role,
        )

    await callback.message.edit_text(
        TEXTS[role_key],
        reply_markup=None,
    )
    await callback.message.answer(TEXTS["main_menu"], reply_markup=kb_main_menu())
    await callback.answer()


@router.callback_query(F.data == "menu_main")
async def handle_main_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(TEXTS["main_menu"], reply_markup=kb_main_menu())
    await callback.answer()


@router.message()
async def handle_unknown(message: Message) -> None:
    await message.answer(TEXTS["unknown_message"], reply_markup=kb_main_menu())
