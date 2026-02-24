import logging
import os
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from db.engine import init_db
from handlers import (
    application,
    corporate,
    experts,
    faq,
    onboarding,
    payment,
    pricing,
    program,
    start,
)
from handlers.onboarding import job_send_d1, job_send_d3, job_send_d7
from services import notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def on_startup(app: web.Application) -> None:
    bot: Bot = app["bot"]

    # 1. Init DB
    await init_db()
    log.info("Database initialised")

    # 2. Inject bot into service modules
    notifications.set_bot(bot)
    onboarding.set_bot(bot)

    # 3. Set webhook (skip in dev mode)
    if not settings.dev_mode:
        await bot.set_webhook(
            url=settings.webhook_url,
            drop_pending_updates=True,
        )
        log.info("Webhook set: %s", settings.webhook_url)

    # 4. Start scheduler
    scheduler: AsyncIOScheduler = app["scheduler"]
    scheduler.start()
    log.info("Scheduler started")


async def on_shutdown(app: web.Application) -> None:
    bot: Bot = app["bot"]
    scheduler: AsyncIOScheduler = app["scheduler"]

    scheduler.shutdown(wait=False)
    if not settings.dev_mode:
        await bot.delete_webhook()
    await bot.session.close()
    log.info("Bot shut down")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # D+1 — run daily at 10:00 UTC, check who needs it
    scheduler.add_job(job_send_d1, "cron", hour=10, minute=0, id="onboarding_d1")
    # D+3 — run daily at 10:00 UTC
    scheduler.add_job(job_send_d3, "cron", hour=10, minute=5, id="onboarding_d3")
    # D-7 before program start — run daily at 09:00 UTC
    scheduler.add_job(job_send_d7, "cron", hour=9, minute=0, id="onboarding_d7")

    return scheduler


def create_app() -> web.Application:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order matters for fallback handler in start.py)
    dp.include_router(application.router)
    dp.include_router(corporate.router)
    dp.include_router(program.router)
    dp.include_router(faq.router)
    dp.include_router(pricing.router)
    dp.include_router(experts.router)
    dp.include_router(start.router)   # fallback unknown_message must be last

    scheduler = build_scheduler()

    app = web.Application()
    app["bot"] = bot
    app["scheduler"] = scheduler

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Telegram webhook route
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    # Payment webhook route
    app.router.add_post(settings.payment_webhook_path, payment.handle_payment_webhook)

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    if settings.dev_mode:
        # Local dev: polling
        import asyncio
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage

        async def run_polling() -> None:
            await init_db()
            bot = Bot(token=settings.bot_token)
            dp = Dispatcher(storage=MemoryStorage())
            notifications.set_bot(bot)
            onboarding.set_bot(bot)
            dp.include_router(application.router)
            dp.include_router(corporate.router)
            dp.include_router(program.router)
            dp.include_router(faq.router)
            dp.include_router(pricing.router)
            dp.include_router(experts.router)
            dp.include_router(start.router)
            log.info("Starting polling (DEV_MODE=true)")
            await dp.start_polling(bot, drop_pending_updates=True)

        asyncio.run(run_polling())
    else:
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=port)
