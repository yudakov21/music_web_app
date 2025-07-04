import json
import asyncio 

from logger import logger
from datetime import datetime, timedelta
from redis import Redis
from hashlib import sha256
from fastapi import HTTPException
from services.applications.openai import OpenAIClient
from services.applications.spotify import SpotifyAPI
from services.applications.genius import GeniusAPI, GeniusParser
from schemas.service_schemas import AllStats, SpotifyTrack, GeniusArtist, SpotifyArtist
from db_manager import DatabaseManager


class ArtistController:
    def __init__(self, genius: GeniusAPI, genius_parser: GeniusParser, spotify: SpotifyAPI,
                manager: DatabaseManager) -> None:
        self.genius = genius
        self.spotify = spotify
        self.genius_parser = genius_parser
        self.manager = manager

    def process_json(self, json_str: str) -> str:
        return json_str.replace('header_photo', 'header_image_url').replace('avatar_photo', 'image_url', 1)

    async def get_artist(self, artist_name: str) -> AllStats:
        genius_id = self.genius.get_artist_id(artist_name)
        genius_artist_id = await asyncio.create_task(genius_id)
        
        artist_ = await self.manager.get_artist(genius_artist_id)
        tracks = await self.manager.get_tracks(genius_artist_id)

        if artist_ and tracks:
            genius_artist_data = json.loads(self.process_json(artist_.json))
            spotify_artist_data = json.loads(artist_.json)
            spotify_tracks= [SpotifyTrack(**track._asdict()).model_dump() for track in tracks]
        
            all_stats = AllStats(
                genius=GeniusArtist(**genius_artist_data["genius"]),
                spotify=SpotifyArtist(**spotify_artist_data["spotify"]),
                spotify_tracks=spotify_tracks,
                most_popular_words=None
            )
            return all_stats
        
        spotify_id = self.spotify.get_artist_id(artist_name)
        spotify_artist_id = await asyncio.create_task(spotify_id)       

        spotify_artist = await self.spotify.get_artist(spotify_artist_id)
        genius_artist = await self.genius.get_artist(genius_artist_id)

        spotify_tracks = await self.spotify.get_artist_top_tracks(spotify_artist_id)

        most_popular_words = None

        all_stats = AllStats(
            genius=genius_artist,
            spotify=spotify_artist,
            spotify_tracks=spotify_tracks,
            most_popular_words=most_popular_words
        )

        data = {
            "genius": genius_artist.model_dump(),
            "spotify": spotify_artist.model_dump()
        }

        await self.manager.add_artist(genius_id=all_stats.genius.id, json=json.dumps(data, ensure_ascii=False))
        await self.manager.add_tracks(artist_id=all_stats.genius.id, tracks=spotify_tracks)

        return all_stats
    

class TrackController:
    def __init__(self, genius: GeniusAPI, genius_parser: GeniusParser, spotify: SpotifyAPI,
                manager: DatabaseManager) -> None:
        self.genius = genius
        self.spotify = spotify
        self.genius_parser = genius_parser
        self.manager = manager

    async def get_track_with_data(self, spotify_song_id: str):
        track = await self.manager.get_one_track(spotify_song_id)
        track_ = track._asdict()

        track_details = await self.manager.get_track_details(spotify_song_id)
        lyrics = await self.manager.get_lyrics(spotify_song_id)
        
        if track_details and lyrics:
            data = {
                "track": track_,
                "details": track_details._asdict(),
                "lyrics": lyrics._asdict()
            }
            return data

        artists = track_.get("artists")
        title = track_.get("title")

        if not artists or not title:
            raise Exception(f"The track does not contain 'artists' or 'title': {track_}")

        track_details = await self.spotify.get_track_details(spotify_song_id)
        if not track_details:
            raise Exception(f"Failed to retrieve track details for ID {spotify_song_id}")

        track_url = await self.genius.get_artist_song(artists, title)

        lyrics = await self.genius_parser.get_songs_text(track_url) 

        await self.manager.add_track_details(spotify_song_id, details=track_details)
        await self.manager.add_lyrics(spotify_song_id, lyrics)

        data = {
            "track": track_,
            "details": track_details,
            "lyrics": lyrics
        }
        return data

    async def get_track_data_without_saving(self, artist_name:str, title: str):
        spotify_song_id = await self.spotify.get_track_id(artist_name, title)

        current_track = await self.spotify.get_current_track(artist_name, title)
        
        track = current_track.model_dump_json()
        
        track_details = await self.spotify.get_track_details(spotify_song_id)
        
        track_url = await self.genius.get_artist_song(artist_name, title)

        lyrics = await self.genius_parser.get_songs_text(track_url)

        data = {
            "track": track,
            "details": track_details,
            "lyrics": lyrics
        }
        return data
    

class TranslatorController:
    def __init__(self, openai_client: OpenAIClient, redis_client: Redis):
        self.openai_client = openai_client
        self.redis_client = redis_client
        
    async def get_text_translation(self, text: str, language: str, level: str):
        text_hash = sha256(text.strip().lower().encode()).hexdigest()
        cache_key = f"result:{text_hash}:{language}:{level}"

        cache_data = await self.redis_client.get(cache_key)
        if cache_data is not None:
            try:
                return json.loads(cache_data)
            except json.JSONDecodeError as e:
                logger.exception(f"Error decoding cached data: {e}")
                # Delete corrupted data from the cache
                await self.redis_client.delete(cache_key)

        try:
            result = self.openai_client.analyze_text(
                text=text, 
                level=level,
                language=language
            )
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

        await self.redis_client.set(cache_key, json.dumps(result), ex=3600)

        return result

class ChatController:
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client

    def get_chat(self, message:str, history: list):
        try:
            result = self.openai_client.chat(
                message=message, history=history)
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return result
    