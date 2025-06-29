import time 

from fastapi import Depends
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from user_auth.base_config import fastapi_users, auth_backend
from services.controller import ArtistController, TrackController, TranslatorController, ChatController
from schemas.user_schemas import UserCreate, UserRead
from schemas.service_schemas import Search, SearchSong, Translation, ChatMessage, LyricsUpdateRequest
from models.models import User
from db_manager import DatabaseManager
from dependencies import get_artist_controller,get_db_manager, get_track_controller, get_translator_controller, get_chat_controller


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


@app.post("/")
async def get_artist_search(search: Search, artist_controller: ArtistController = Depends(get_artist_controller)):
    start_time = time.perf_counter()  
    try:
        artist = await artist_controller.get_artist(search.artist_name)
        end_time = time.perf_counter() 
        print(f"Time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        return {"error": str(e)}
    return artist

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


@app.post("/update_lyrics/")
async def update_lyrics(data: LyricsUpdateRequest, manager: DatabaseManager = Depends(get_db_manager)):
    try:
        await manager.update_lyrics(data.id, data.lyrics)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/related_artists/{artist_id}")
async def get_related_artists(artist_id: int, manager: DatabaseManager = Depends(get_db_manager)):
    try:
        artists = await manager.get_artist_by_genres(artist_id=artist_id)
        return {"success": True, "artists": artists }
    except Exception as e:
        return {"success": False, "error": str(e)}
    

@app.post("/like_track/{track_id}")
async def like_track_endpoint(track_id: str, user: User = Depends(fastapi_users.current_user()), 
                              manager: DatabaseManager = Depends(get_db_manager)):
    await manager.like_track(user_id=user.id, track_id=track_id)
    return {"success": True}

@app.post("/like_artist/{artist_id}")
async def like_artist_endpoint(artist_id: int, user: User = Depends(fastapi_users.current_user()), 
                              manager: DatabaseManager = Depends(get_db_manager)):
    await manager.like_artist(user_id=user.id, artist_id=artist_id)
    return {"success": True}


@app.get("/liked_tracks/")
async def get_liked_tracks(user: User = Depends(fastapi_users.current_user()),
                            manager: DatabaseManager = Depends(get_db_manager)):
    liked_tracks = await manager.get_liked_tracks(user.id)
    if liked_tracks is None:
        return []
    return liked_tracks

@app.get("/liked_artists/")
async def get_liked_artists(user: User = Depends(fastapi_users.current_user()), 
                            manager: DatabaseManager = Depends(get_db_manager)):
    liked_artists = await manager.get_liked_artists(user.id)
    if liked_artists is None:
        return []
    return liked_artists


@app.delete("/unlike_track/{track_id}")
async def unlike_track(track_id: str, user: User = Depends(fastapi_users.current_user()), 
                       manager: DatabaseManager = Depends(get_db_manager)):
    await manager.unlike_track(user.id, track_id)
    return {"success": True}

@app.delete("/unlike_artist/{artist_id}")
async def unlike_artist(artist_id: int, user: User = Depends(fastapi_users.current_user()), 
                        manager: DatabaseManager = Depends(get_db_manager)):
    await manager.unlike_artist(user.id, artist_id)
    return {"success": True}