import redis.asyncio as redis
from bot_config import REDIS_URL

bot_redis = redis.from_url(REDIS_URL)

async def save_token_to_redis(
        user_id: int, 
        token: str,
        ):
    await bot_redis.set(
        f"user:{user_id}:token", 
        token, 
        ex=3600,
        )

async def get_token_from_redis(user_id: int):
    token = await bot_redis.get(f"user:{user_id}:token")
    if token:
        return token.decode("utf-8")
    else:
        return None