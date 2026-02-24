from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.inline import kb_experts
from texts.ru import TEXTS

router = Router()


@router.callback_query(F.data == "menu_experts")
async def handle_experts(callback: CallbackQuery) -> None:
    await callback.message.answer(TEXTS["experts_intro"])
    await callback.message.answer(TEXTS["experts_stella"])
    await callback.message.answer(TEXTS["experts_lev"])
    await callback.message.answer(TEXTS["experts_speakers"], reply_markup=kb_experts())
    await callback.answer()
