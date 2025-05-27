from pydantic import BaseModel, Field
from datetime import date

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

class SpotifyTrackDetails(BaseModel):
    key: str
    bpm: str
    camelot: str
    popularity: str
    energy: str
    danceability: str
    happiness: str

class SpotifyTrack(BaseModel):
    spotify_song_id: str | None
    artist: str
    title: str 
    release_date: date
    cover_url: str 
    preview_url: str | None

class Lyrics(BaseModel):
    text: str | None

class AllStats(BaseModel):
    genius: GeniusArtist
    spotify: SpotifyArtist
    spotify_tracks: list[SpotifyTrack]
    most_popular_words: list[str] | None

class Search(BaseModel):
    artist_name: str | None

class SearchSong(BaseModel):
    song_name: str | None