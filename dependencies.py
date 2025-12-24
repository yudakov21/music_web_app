from core import config
from fastapi import Depends, Request, HTTPException, status
from redis.asyncio import Redis
from core.rate_limiter import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_manager import DatabaseManager
from db.database import get_async_session
from services.controller import ArtistController, TrackController, TranslatorController, ChatController
from services.applications.genius import GeniusAPI, GeniusParser
from services.applications.spotify import SpotifyAPI
from services.applications.openai import OpenAIClient


async def get_db_manager(session: AsyncSession = Depends(get_async_session)):
    return DatabaseManager(session=session)


async def get_redis_client() -> Redis:
    redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT,
                         encoding="utf-8", decode_responses=True)
    return redis_client


async def get_rate_limiter(redis_client: Redis = Depends(get_redis_client)):
    rate_limiter = RateLimiter(
        redis_client=redis_client
    )
    return rate_limiter


def rate_limiter_factory(
        *,
        endpoint: str | None = None,
        max_requests: int,
        window_seconds: int,
        
):
    async def dependency(
            request: Request,
            rate_limiter: RateLimiter = Depends(get_rate_limiter)
    ):
        ip = request.client.host

        path = endpoint or request.url.path

        limited = await rate_limiter.is_limited(
            ip_address=ip,
            endpoint=path,
            max_requests=max_requests,
            window_seconds=window_seconds
        )

        if limited:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                                detail="Too many requests")
    
    return dependency


async def get_artist_controller(manager: DatabaseManager = Depends(get_db_manager),
                                redis_client: Redis = Depends(get_redis_client)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS,
                         config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return ArtistController(genius=genius, genius_parser=genius_parser, spotify=spotify,
                            manager=manager, redis_client=redis_client)


async def get_track_controller(manager: DatabaseManager = Depends(get_db_manager)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS,
                         config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return TrackController(genius=genius, genius_parser=genius_parser, spotify=spotify, manager=manager)


async def get_translator_controller(redis_client: Redis = Depends(get_redis_client)):
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return TranslatorController(openai_client, redis_client)


async def get_chat_controller():
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return ChatController(openai_client)
