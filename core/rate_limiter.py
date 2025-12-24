import random

from time import time
from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def is_limited(self, ip_address: str, endpoint: str,
                         max_requests: int, window_seconds: int) -> bool:
        key = f"rate_limited:{endpoint}:{ip_address}"

        current_ms = time() * 1000

        current_request = f"{current_ms}-{random.randint(0, 100_000)}"

        window_start_ms = current_ms - window_seconds * 1000

        async with self.redis_client.pipeline() as pipe:
            await pipe.zremrangebyscore(key, 0, window_start_ms)

            await pipe.zadd(key, {current_request: current_ms})

            await pipe.zcard(key)

            await pipe.expire(key, window_seconds)

            res = await pipe.execute()

        _, _, current_count, _ = res

        return current_count >= max_requests
