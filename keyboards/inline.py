from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── Выбор роли ────────────────────────────────────────────────────────────────

def kb_roles() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    roles = [
        ("🎬 Художественный руководитель", "role_artistic_director"),
        ("🎭 Режиссёр", "role_director"),
        ("🎨 Художник-постановщик", "role_set_designer"),
        ("💼 Продюсер", "role_producer"),
        ("📣 PR и маркетолог", "role_pr_marketing"),
        ("💻 Эксперт по цифровым технологиям", "role_tech_expert"),
    ]
    for text, callback in roles:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    return builder.as_markup()


# ── Главное меню ──────────────────────────────────────────────────────────────

def kb_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        ("📋 Программа", "menu_program"),
        ("❓ FAQ", "menu_faq"),
        ("💰 Стоимость и форматы", "menu_pricing"),
        ("👥 Эксперты", "menu_experts"),
        ("📝 Подать заявку", "menu_apply"),
        ("🏛 Корпоративный формат", "menu_corporate"),
    ]
    for text, callback in buttons:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    return builder.as_markup()


# ── Программа ─────────────────────────────────────────────────────────────────

def kb_program() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_apply"))
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()


# ── FAQ ───────────────────────────────────────────────────────────────────────

def kb_faq_list() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    questions = [
        ("Зачем мне это, если мы успешно ставим классику?", "faq_1"),
        ("Я далёк от технологий — это не для меня", "faq_2"),
        ("Цифровизация убьёт «магию» театра?", "faq_3"),
        ("Зачем лаборатория, если в сети полно курсов?", "faq_4"),
    ]
    for text, callback in questions:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()


def kb_faq_answer() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="← Другой вопрос", callback_data="menu_faq"))
    builder.row(InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_apply"))
    return builder.as_markup()


# ── Стоимость ─────────────────────────────────────────────────────────────────

def kb_pricing() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Подать заявку (50 000 ₽)", callback_data="menu_apply"))
    builder.row(InlineKeyboardButton(text="🏛 Корпоративный формат", callback_data="menu_corporate"))
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()


# ── Эксперты ──────────────────────────────────────────────────────────────────

def kb_experts() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_apply"))
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()


# ── FSM: Заявка ───────────────────────────────────────────────────────────────

def kb_referral_source() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sources = [
        ("Лендинг", "ref_landing"),
        ("Telegram", "ref_telegram"),
        ("Рекомендация", "ref_recommendation"),
        ("Другое", "ref_other"),
    ]
    for text, callback in sources:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    return builder.as_markup()


def kb_application_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Всё верно", callback_data="apply_confirm"))
    builder.row(InlineKeyboardButton(text="✏️ Исправить", callback_data="apply_edit"))
    return builder.as_markup()


def kb_payment_link(payment_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_link))
    return builder.as_markup()


# ── FSM: Корпоративный формат ─────────────────────────────────────────────────

def kb_corporate_format() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌐 Онлайн", callback_data="format_online"))
    builder.row(InlineKeyboardButton(text="✈️ Выездной", callback_data="format_offline"))
    return builder.as_markup()


def kb_corporate_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Отправить", callback_data="corporate_confirm"))
    builder.row(InlineKeyboardButton(text="✏️ Исправить", callback_data="corporate_edit"))
    return builder.as_markup()


# ── Главное меню (кнопка-ссылка) ─────────────────────────────────────────────

def kb_to_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()


def kb_apply_or_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_apply"))
    builder.row(InlineKeyboardButton(text="← Главное меню", callback_data="menu_main"))
    return builder.as_markup()
