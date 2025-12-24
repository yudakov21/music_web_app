from pydantic import BaseModel, Field
from datetime import date
from typing import List, Dict, Optional


class GeniusArtist(BaseModel):
    id: int
    name: str
    alternate_names: list[str] | None
    instagram_name: str | None
    twitter_name: str | None
    followers_count: int
    header_photo: str = Field(alias="header_image_url")
    avatar_photo: str = Field(alias="image_url")
    url: str


class SpotifyArtist(BaseModel):
    name: str
    avatar_photo: str
    popularity: int
    followers_count: int
    genres: list[str]


class SpotifyTrack(BaseModel):
    spotify_song_id: str | None
    artists: str
    title: str 
    release_date: date
    cover_url: str | None
    preview_url: str | None


class SpotifyTrackDetails(BaseModel):
    key: str
    bpm: str
    camelot: str
    popularity: str
    energy: str
    danceability: str
    happiness: str


class Lyrics(BaseModel):
    text: str | None


class LyricsUpdateRequest(BaseModel):
    id: str
    lyrics: str


class AllStats(BaseModel):
    genius: GeniusArtist
    spotify: SpotifyArtist
    spotify_tracks: list[SpotifyTrack]
    most_popular_words: list[str] | None


class Search(BaseModel):
    artist_name: str | None


class SearchSong(BaseModel):
    artist_name: str | None
    title: str | None


class Translation(BaseModel):
    text: str
    level: str
    language: str


class ChatMessage(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


class TrackRead(BaseModel):
    artist_id: int
    spotify_song_id: str
    artists: Optional[str]
    title: str
    cover_url: Optional[str]


class ArtistRead(BaseModel):
    genius_id: int
    name: str
    cover_url: Optional[str]
