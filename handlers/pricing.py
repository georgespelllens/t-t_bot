from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.inline import kb_pricing
from texts.ru import TEXTS

router = Router()


@router.callback_query(F.data == "menu_pricing")
async def handle_pricing(callback: CallbackQuery) -> None:
    await callback.message.answer(TEXTS["pricing"], reply_markup=kb_pricing())
    await callback.answer()
