from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.inline import kb_program
from texts.ru import TEXTS

router = Router()


@router.callback_query(F.data == "menu_program")
async def handle_program(callback: CallbackQuery) -> None:
    await callback.message.answer(TEXTS["program_intro"])
    await callback.message.answer(TEXTS["program_act1"])
    await callback.message.answer(TEXTS["program_act2"])
    await callback.message.answer(TEXTS["program_act3"])
    await callback.message.answer(TEXTS["program_act4"])
    await callback.message.answer(TEXTS["program_tools"], reply_markup=kb_program())
    await callback.answer()
