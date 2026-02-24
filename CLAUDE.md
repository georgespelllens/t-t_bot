# T+T Bot — «Театр + Технологии»

## Project Overview
Telegram welcome-bot для образовательной лаборатории «Театр + Технологии».
Авторы: Стелла Лабужская и Лев Бахарев (SPELLLENS × VozDooh).
Стоимость участия: 50 000 ₽. Поток до 40 человек. Старт — весна 2026.

**Цель бота:** автоматизировать путь лида от /start до онбординга после оплаты
без участия куратора.

---

## Stack
- **Language:** Python 3.11
- **Framework:** Aiogram 3.x (webhook mode, NOT polling in production)
- **Database:** PostgreSQL (Railway managed)
- **ORM:** SQLAlchemy 2.x async + asyncpg
- **Scheduler:** APScheduler (AsyncIOScheduler)
- **Sheets integration:** gspread + google-auth
- **HTTP client:** httpx
- **Config:** pydantic-settings (.env файл)
- **Hosting:** Railway (один сервис)
- **VCS:** GitHub

---

## Repository Structure
```
tt-bot/
├── CLAUDE.md
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── Procfile                        # для Railway: web: python main.py
├── main.py                         # entry point, webhook setup
├── config.py                       # pydantic-settings, все ENV переменные
├── texts/
│   └── ru.py                       # ВСЕ пользовательские тексты — только здесь
├── content/
│   ├── 01_welcome.md               # приветствие + 6 ролей
│   ├── 02_program.md               # 4 блока программы
│   ├── 03_faq.md                   # вопросы и ответы
│   ├── 04_pricing.md               # стоимость и форматы
│   ├── 05_experts.md               # Стелла и Лев
│   ├── 06_onboarding.md            # серия сообщений после оплаты
│   ├── 07_curator_notify.md        # шаблоны уведомлений куратору
│   └── 08_corporate.md             # корпоративная ветка
├── handlers/
│   ├── __init__.py
│   ├── start.py                    # /start, выбор роли, главное меню
│   ├── program.py                  # 4 блока программы
│   ├── faq.py                      # 4 вопроса/ответа
│   ├── application.py              # FSM: сбор заявки → ссылка на оплату
│   ├── payment.py                  # webhook от ЮKassa/Robokassa
│   ├── onboarding.py               # серия сообщений после оплаты
│   └── corporate.py                # FSM: корпоративный запрос
├── states/
│   ├── __init__.py
│   ├── application.py              # FSM states для заявки
│   └── corporate.py                # FSM states для корп. запроса
├── db/
│   ├── __init__.py
│   ├── engine.py                   # async engine + session factory
│   ├── models.py                   # SQLAlchemy модели
│   └── repository.py               # ВСЕ запросы к БД — только здесь
├── services/
│   ├── __init__.py
│   ├── sheets.py                   # Google Sheets: запись заявок
│   ├── payment.py                  # генерация ссылки, верификация вебхука
│   └── notifications.py            # отправка уведомлений куратору
└── keyboards/
    ├── __init__.py
    └── inline.py                   # все InlineKeyboardMarkup
```

---

## Database Models

```python
# db/models.py — точная структура, не отступать

class User(Base):
    __tablename__ = "users"
    telegram_id: int          # PK
    username: str | None
    full_name: str
    role: str                 # один из 6 вариантов роли
    city: str
    organization: str
    referral_source: str
    status: str               # new | applied | paid | onboarded
    applied_at: datetime | None
    paid_at: datetime | None
    payment_id: str | None    # ID из ЮKassa для сверки

class OnboardingLog(Base):
    __tablename__ = "onboarding_log"
    id: int                   # PK, autoincrement
    telegram_id: int          # FK → users
    message_key: str          # welcome | doc | invite | reminder_d1 | reminder_d3 | reminder_d7
    sent_at: datetime

class CorporateRequest(Base):
    __tablename__ = "corporate_requests"
    id: int                   # PK, autoincrement
    telegram_id: int
    theater_name: str
    city: str
    headcount: int
    format: str               # online | offline
    tasks_text: str
    created_at: datetime
```

---

## User Flows

### Flow 1 — Основной (физлицо)
```
/start
  → Приветственное сообщение + кнопки выбора роли (6 штук)
    → Персонализированный экран: [боль роли] → [результат после лаборатории]
      → Главное меню:
          [📋 Программа] [❓ FAQ] [💰 Стоимость] [📝 Подать заявку] [🏛 Корпоративный формат]
        → [📝 Подать заявку] → FSM ApplicationStates
            → Шаг 1: имя (текст)
            → Шаг 2: город (текст)
            → Шаг 3: театр / организация (текст)
            → Шаг 4: откуда узнали (кнопки: Лендинг / Telegram / Рекомендация / Другое)
            → Подтверждение: показать собранные данные + [✅ Всё верно] [✏️ Исправить]
            → Сохранить в PostgreSQL (status = applied)
            → Записать строку в Google Sheets
            → Уведомление куратору (CURATOR_CHAT_ID)
            → Отправить ссылку на оплату
        → [Оплата прошла — вебхук от провайдера]
            → Верифицировать HMAC подпись
            → Обновить user: status = paid, записать paid_at + payment_id
            → Запустить onboarding sequence
```

### Flow 2 — Онбординг после оплаты
```
Сразу (D+0):
  → Сообщение "welcome_paid" — поздравление + что дальше
  → Документ с программой (PDF)
  → Одноразовая invite-ссылка в закрытый чат (member_limit=1, expire=+48h)

Отложенные (APScheduler):
  → D+1: что прочитать и установить до старта
  → D+3: список AI-инструментов которые понадобятся на курсе
  → За 7 дней до PROGRAM_START_DATE: напоминание о дате первой сессии + ссылка на созвон
```

### Flow 3 — Корпоративный запрос
```
[🏛 Корпоративный формат] → FSM CorporateStates
  → Шаг 1: название театра / организации
  → Шаг 2: город
  → Шаг 3: количество человек
  → Шаг 4: формат [🌐 Онлайн] [✈️ Выездной]
  → Шаг 5: опишите задачи (свободный текст)
  → Подтверждение данных
  → Сохранить в corporate_requests
  → Уведомление куратору со всем брифом
  → Пользователю: «Стелла свяжется в течение 24 часов»
```

### Edge Cases
- Произвольный текст вне FSM → предложить главное меню
- Лид начал заявку, не завершил → через 24ч напоминание (APScheduler)
- Вебхук оплаты пришёл для неизвестного user_id → логировать + уведомить куратора
- Бот не является admin чата → уведомить куратора вместо автоматического invite

---

## Environment Variables

```env
# .env.example — все переменные обязательны если не указано иное

BOT_TOKEN=                        # от BotFather
WEBHOOK_HOST=                     # https://your-app.railway.app
WEBHOOK_PATH=/webhook             # путь для Telegram webhook

CURATOR_CHAT_ID=                  # Telegram ID куратора (целое число)

PAYMENT_LINK=                     # базовая ссылка на оплату (ЮKassa / Robokassa)
PAYMENT_WEBHOOK_SECRET=           # секрет для HMAC верификации вебхука
PAYMENT_WEBHOOK_PATH=/payment     # путь для вебхука от платёжного провайдера

GOOGLE_SHEET_ID=                  # ID таблицы Google Sheets
GOOGLE_CREDENTIALS_JSON=          # JSON service account (base64-encoded строка)

CLOSED_CHAT_ID=                   # ID закрытого Telegram-чата участников

DATABASE_URL=                     # postgresql+asyncpg://user:pass@host/db

PROGRAM_START_DATE=2026-04-07     # ISO формат YYYY-MM-DD, для расчёта scheduler

DEV_MODE=false                    # true → polling вместо webhook (только локально)
```

---

## Key Conventions

1. **Все тексты** — только в `texts/ru.py`. В хэндлерах — только обращение к словарю. Никаких хардкоженных строк в коде.
2. **Все запросы к БД** — только через `db/repository.py`. Никакого прямого SQL или ORM-запросов в хэндлерах.
3. **Все клавиатуры** — только в `keyboards/inline.py`.
4. **Webhook mode** в продакшене. Polling только при `DEV_MODE=true`.
5. **FSM storage** — MemoryStorage для MVP.
6. **Логирование** — стандартный `logging`, уровень INFO в продакшене.
7. **Платёжный вебхук** — всегда верифицировать HMAC подпись до любой обработки данных.
8. **Invite-ссылки** — генерировать через `bot.create_chat_invite_link()` с `member_limit=1` и `expire_date=now+48h`.
9. **Тексты для бота** брать из файлов `content/*.md` и переносить в `texts/ru.py` как строки.

---

## Forbidden

- ❌ Polling в продакшене (`DEV_MODE=false`)
- ❌ Хардкоженные тексты вне `texts/ru.py`
- ❌ Прямые SQL-запросы или ORM в хэндлерах
- ❌ Хранение данных платёжных карт в любом виде
- ❌ Принимать вебхук оплаты без проверки HMAC подписи
- ❌ Один файл для всех хэндлеров
- ❌ Синхронные функции внутри async хэндлеров (использовать asyncio.to_thread если нужно)

---

## Railway Deployment

```
# Procfile
web: python main.py
```

```
# main.py — порядок инициализации:
# 1. Загрузить config (pydantic-settings)
# 2. Инициализировать DB engine, создать таблицы
# 3. Создать Bot + Dispatcher, зарегистрировать все роутеры
# 4. Создать aiohttp.web.Application
# 5. Зарегистрировать путь WEBHOOK_PATH для Telegram updates
# 6. Зарегистрировать путь PAYMENT_WEBHOOK_PATH для ЮKassa events
# 7. Запустить APScheduler
# 8. Запустить на порту PORT (Railway проставляет автоматически через os.environ)
```

**Railway services:**
- `tt-bot` — Python app (Starter plan, 512 MB RAM)
- `tt-db` — PostgreSQL (Railway managed)

---

## Start Here — порядок разработки

Строго соблюдать последовательность:

1. `config.py` — pydantic-settings, загрузка всех ENV переменных
2. `db/models.py` + `db/engine.py` — модели и async подключение к БД
3. `db/repository.py` — все CRUD операции (create_user, update_status, log_onboarding, create_corporate)
4. `texts/ru.py` — перенести все тексты из `content/*.md` в словарь
5. `keyboards/inline.py` — все InlineKeyboardMarkup и ReplyKeyboardMarkup
6. `handlers/start.py` — /start, выбор роли, персонализированный экран, главное меню
7. `handlers/program.py` + `handlers/faq.py` — информационные разделы
8. `handlers/application.py` — FSM заявки (ключевой конверсионный flow)
9. `services/payment.py` + `handlers/payment.py` — генерация ссылки + вебхук оплаты
10. `handlers/onboarding.py` + APScheduler — серия сообщений после оплаты
11. `handlers/corporate.py` — FSM корпоративного запроса
12. `services/sheets.py` — запись заявок в Google Sheets
13. `services/notifications.py` — уведомления куратору
14. `main.py` — сборка приложения, webhook setup, запуск
15. Деплой на Railway, проверка всех env переменных, тест полного флоу
