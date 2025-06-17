import config
import time 

from fastapi import Depends
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from user_auth.base_config import fastapi_users, auth_backend
from services.controller import ArtistController, TrackController, TranslatorController, ChatController
from services.applications.genius import GeniusAPI, GeniusParser
from services.applications.spotify import SpotifyAPI
from services.applications.openai import OpenAIClient
from schemas.user_schemas import UserCreate, UserRead
from schemas.service_schemas import Search, SearchSong, Translation, ChatMessage
from db_manager import DatabaseManager
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


app = FastAPI(
    title='Melon'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


async def get_db_manager(session: AsyncSession = Depends(get_async_session)):
    return DatabaseManager(session=session)

async def get_artist_controller(manager: DatabaseManager = Depends(get_db_manager)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS, config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return ArtistController(genius=genius,genius_parser=genius_parser,spotify=spotify,manager=manager)

async def get_track_controller(manager: DatabaseManager = Depends(get_db_manager)):
    genius = GeniusAPI(config.GENIUS_ACCESS)
    genius_parser = GeniusParser()
    spotify = SpotifyAPI(config.SPOTIFY_ACCESS, config.SPOTIFY_ID, config.SPOTIFY_SECRET)

    return TrackController(genius=genius,genius_parser=genius_parser,spotify=spotify,manager=manager)

async def get_redis_client() -> Redis:
    redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_HOST, encoding="utf-8", decode_responses=True)
    return redis_client

async def get_translator_controller(redis_client: Redis = Depends(get_redis_client)):
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return TranslatorController(openai_client=openai_client, redis_client=redis_client)

async def get_chat_controller():
    openai_client = OpenAIClient(config.OPENAI_API_TOKEN)
    return ChatController(openai_client=openai_client)


@app.post("/")
async def get_artist_search(search: Search, artist_controller: ArtistController = Depends(get_artist_controller)):
    start_time = time.perf_counter()  
    try:
        artist = await artist_controller.get_artist(search.artist_name)
        end_time = time.perf_counter() 
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return JSONResponse(content=artist, media_type="application/json")

@app.post("/track/")
async def get_track_search(search: SearchSong, track_controller: TrackController = Depends(get_track_controller)):
    start_time = time.perf_counter() 
    try:
        track = await track_controller.get_track_data_without_saving(search.artist_name, search.title)
        end_time = time.perf_counter()  
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return track

@app.get("/{spotify_song_id}")
async def get_track_with_data(spotify_song_id: str, track_controller: TrackController = Depends(get_track_controller)):
    start_time = time.perf_counter()
    try:
        data = await track_controller.get_track_with_data(spotify_song_id)
        end_time = time.perf_counter()
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return data


@app.post("/translation/")
async def get_translation(translation: Translation,
                    translator_controller: TranslatorController = Depends(get_translator_controller)):
    try:
        data = await translator_controller.get_text_translation(translation.text, translation.language, translation.level)
    except Exception as e:
        return {"error": str(e)}
    return data

@app.post("/chat/")
async def chat_with_gpt(chat_message: ChatMessage, chat_controller: ChatController = Depends(get_chat_controller)):
    try:
        data = chat_controller.get_chat(message=chat_message.message, history=chat_message.history)
    except Exception as e:
        return {"error": str(e)}    
    return data