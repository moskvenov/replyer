import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
# Webhook imports
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN, ADMIN_IDS, USE_WEBHOOK, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT
from database.db import init_db
from handlers import user, admin
from middlewares.throttling import ThrottlingMiddleware
from middlewares.checks import BanMuteMiddleware
from middlewares.media import MediaSizeMiddleware
from utils.tasks import check_expired_mutes

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Register Middlewares
# 1. Throttling (First to block spam early)
dp.message.middleware(ThrottlingMiddleware(limit=10))
# 2. Ban/Mute Checks
dp.message.middleware(BanMuteMiddleware())
# 3. Media Size Check
dp.message.middleware(MediaSizeMiddleware(limit_mb=50))

# Register Routers
dp.include_router(admin.router)
dp.include_router(user.router)

async def on_startup(bot: Bot):
    await init_db()
    # Start background tasks
    asyncio.create_task(check_expired_mutes())
    
    if USE_WEBHOOK:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"✅ Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    if USE_WEBHOOK:
        await bot.delete_webhook()

async def main():
    if USE_WEBHOOK:
        # Webhook Mode
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        app = web.Application()
        
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path="/webhook")
        
        setup_application(app, dp, bot=bot)
        
        print(f"🚀 Starting Webhook Server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
        await site.start()
        
        # Keep alive
        await asyncio.Event().wait()
    else:
        # Polling Mode
        await init_db()
        asyncio.create_task(check_expired_mutes()) # Start task in polling too
        print("🚀 Starting Polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
