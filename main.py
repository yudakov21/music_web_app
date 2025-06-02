import config
import time 

from fastapi import Depends
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from user_auth.base_config import fastapi_users, auth_backend
from services.controller import ArtistController, TrackController
from services.applications.genius import GeniusAPI, GeniusParser
from services.applications.spotify import SpotifyAPI
from schemas.user_schemas import UserCreate, UserRead
from schemas.service_schemas import Search, SearchSong
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
        track = await track_controller.get_track(search.artist_name, search.title)
        end_time = time.perf_counter()  
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return track

@app.get("/{spotify_song_id}")
async def get_lyrics(spotify_song_id: str, track_controller: TrackController = Depends(get_track_controller)):
    start_time = time.perf_counter()
    try:
        data = await track_controller.get_track_with_data(spotify_song_id)
        end_time = time.perf_counter()
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return data
