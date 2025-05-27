import asyncio 

from datetime import datetime, timedelta
from services.applications.spotify import SpotifyAPI
from services.applications.genius import GeniusAPI, GeniusParser
from schemas.service_schemas import AllStats, SpotifyTrack
from db_manager import DatabaseManager


class ArtistController:
    def __init__(self, genius: GeniusAPI, genius_parser: GeniusParser, spotify: SpotifyAPI,
                manager: DatabaseManager) -> None:
        self.genius = genius
        self.spotify = spotify
        self.genius_parser = genius_parser
        self.manager = manager

    def is_day_delta(self, date_query: datetime, date_db_query: datetime) -> bool:
        return abs(date_query - date_db_query) <= timedelta(days=1)

    def process_json(self, json_str: str) -> str:
        return json_str.replace('header_photo', 'header_image_url').replace('avatar_photo', 'image_url', 1)

    async def get_artist(self, artist_name: str) -> AllStats:
        genius_id = self.genius.get_artist_id(artist_name)
        spotify_id = self.spotify.get_artist_id(artist_name)

        spotify_artist_id, genius_artist_id = await asyncio.gather(spotify_id, genius_id)

        artist_ = await self.manager.get_artist(genius_artist_id)
        if artist_:
            data = AllStats.parse_raw(self.process_json(artist_.json))
            print(artist_.json)
            return data

        spotify_artist = await self.spotify.get_artist(spotify_artist_id)
        genius_artist = await self.genius.get_artist(genius_artist_id)

        track_links = await self.genius_parser.get_track_links(genius_artist.url)

        tracks_text = [self.genius_parser.get_songs_text(track_link) for track_link in track_links]

        stats = [
            self.spotify.get_artist_top_tracks(spotify_artist_id),
            *tracks_text
        ]
        stats_result = await asyncio.gather(*stats)

        most_popular_words = None

        all_stats = AllStats(
            genius=genius_artist,
            spotify=spotify_artist,
            spotify_tracks=stats_result[0],
            most_popular_words=most_popular_words
        )

        await self.manager.add_artist(genius_id=all_stats.genius.id,
        json=str(all_stats.model_dump_json()))
        return all_stats.model_dump_json()
    

class TrackController:
    def __init__(self, genius: GeniusAPI, genius_parser: GeniusParser, spotify: SpotifyAPI,
                manager: DatabaseManager) -> None:
        self.genius = genius
        self.spotify = spotify
        self.genius_parser = genius_parser
        self.manager = manager
    
    async def track_with_lyrics(self, spotify_song_id: str, track: SpotifyTrack):
        track_details = await self.spotify.get_track_details(spotify_song_id)
        if not track_details:
            raise Exception(f"Failed to retrieve details for track with ID {spotify_song_id}")

        track_url = await self.genius.get_artist_song(track.artist, track.title)
        if track_url:
            lyrics = await self.genius_parser.get_songs_text(track_url) 
        else:
            lyrics = None
        
        await self.manager.add_track_details(spotify_song_id)
        if lyrics:
            await self.manager.add_lyrics(spotify_song_id, lyrics)

        return {
            "spotify_song_id": spotify_song_id,
            "details": track_details,
            "lyrics": lyrics
        }
