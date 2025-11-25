import config

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_manager import DatabaseManager
from database import get_async_session
from services.controller import ArtistController, TrackController, TranslatorController, ChatController
from services.applications.genius import GeniusAPI, GeniusParser
from services.applications.spotify import SpotifyAPI
from services.applications.openai import OpenAIClient
from redis.asyncio import Redis


async def get_db_manager(session: AsyncSession = Depends(get_async_session)):
    return DatabaseManager(session=session)

async def get_redis_client() -> Redis:
    redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, encoding="utf-8", decode_responses=True)
    return redis_client

async def get_artist_controller(manager: DatabaseManager = Depends(get_db_manager),
                                redis_client: Redis = Depends(get_redis_client)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS, config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return ArtistController(genius=genius,genius_parser=genius_parser,spotify=spotify,
                            manager=manager, redis_client=redis_client)

async def get_track_controller(manager: DatabaseManager = Depends(get_db_manager)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS, config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return TrackController(genius=genius,genius_parser=genius_parser,spotify=spotify,manager=manager)

async def get_translator_controller(redis_client: Redis = Depends(get_redis_client)):
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return TranslatorController(openai_client, redis_client)

async def get_chat_controller():
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return ChatController(openai_client)