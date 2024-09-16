import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from bot_auth_router import auth_router
from bot_notes_router import notes_router
from bot_config import REDIS_URL, API_TOKEN


logging.basicConfig(level=logging.INFO)

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
