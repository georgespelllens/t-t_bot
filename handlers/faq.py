from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.inline import kb_faq_answer, kb_faq_list
from texts.ru import TEXTS

router = Router()

FAQ_CALLBACKS = {"faq_1", "faq_2", "faq_3", "faq_4"}


@router.callback_query(F.data == "menu_faq")
async def handle_faq_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(TEXTS["faq_intro"], reply_markup=kb_faq_list())
    await callback.answer()


@router.callback_query(F.data.in_(FAQ_CALLBACKS))
async def handle_faq_answer(callback: CallbackQuery) -> None:
    key = callback.data  # "faq_1" … "faq_4"
    await callback.message.answer(TEXTS[key], reply_markup=kb_faq_answer())
    await callback.answer()
