import logging
from logging.handlers import TimedRotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from bot_auth_router import auth_router
from bot_notes_router import notes_router
from bot_config import REDIS_URL, API_TOKEN

logger = logging.getLogger("aiogram_bot")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("logs/bot.log", when="midnight", interval=1, backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

bot = Bot(token=API_TOKEN)
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

async def main():
    dp.include_router(auth_router)
    dp.include_router(notes_router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
