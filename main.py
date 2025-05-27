import config


from fastapi import FastAPI
from user_auth.base_config import fastapi_users, auth_backend
from services.controller import ArtistController, TrackController
from services.applications.genius import GeniusAPI, GeniusParser
from services.applications.spotify import SpotifyAPI
from schemas.user_schemas import UserCreate, UserRead
from schemas.service_schemas import Search
from db_manager import DatabaseManager
from database import get_async_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware


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


genius = GeniusAPI(config.GENIUS_ACCESS)
genius_parser = GeniusParser()
spotify = SpotifyAPI(config.SPOTIFY_ACCESS, config.SPOTIFY_ID, config.SPOTIFY_SECRET, genius, genius_parser)

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


@app.post("/")
async def get_search(search: Search, session: AsyncSession = Depends(get_async_session)):
    manager = DatabaseManager(session=session)
    artist_controller = ArtistController(
        genius=genius,
        genius_parser=genius_parser,
        spotify=spotify,
        manager=manager
    )
    try:
        artist = await artist_controller.get_artist(search.artist_name)
    except Exception as e:
        return {"error": str(e)}
    return artist


@app.post("/{spotify_song_id}")
async def get_lyrics(spotify_song_id: str, session: AsyncSession = Depends(get_async_session)):
    manager = DatabaseManager(session=session)
    track_controller = TrackController(
        genius=genius,
        genius_parser=genius_parser,
        spotify=spotify,
        manager=manager
    )
    try:
        lyrics = await track_controller.track_with_lyrics(spotify_song_id)
    except Exception as e:
        return {"error": str(e)}
    return lyrics
