import pytest
import json

from core.logger import logger
from unittest.mock import MagicMock
from schemas.service_schemas import GeniusArtist, SpotifyArtist, SpotifyTrackDetails


@pytest.mark.asyncio
async def test_get_artist(artist_controller, mock_db, mock_genius, mock_spotify, mock_redis):
    genius_id = 1234
    artist_json = {
        "genius": {
            "id": genius_id,
            "name": "Test Artist",
            "alternate_names": [],
            "instagram_name": None,
            "twitter_name": None,
            "followers_count": 1000,
            "header_image_url": "http://image.com/header.jpg",
            "image_url": "http://image.com/avatar.jpg",
            "url": "http://genius.com/artist"
        },
        "spotify": {
            "name": "Test Artist",
            "avatar_photo": "http://spotify.com/photo.jpg",
            "popularity": 80,
            "followers_count": 500000,
            "genres": ["pop"]
        }
    }

    mock_redis.get.return_value = None

    mock_genius.get_artist_id.return_value = genius_id
    mock_db.get_artist.return_value = MagicMock(json=json.dumps(artist_json))
    mock_db.get_tracks.return_value = [
        MagicMock(_asdict=lambda: {
            "spotify_song_id": "id123",
            "artists": "Test Artist",
            "title": "Test Song",
            "release_date": "2024-01-01",
            "cover_url": None,
            "preview_url": None
        }),
        MagicMock(_asdict=lambda: {
            "spotify_song_id": "id456",
            "artists": "Test Artist",
            "title": "Track Two",
            "release_date": "2023-01-01",
            "cover_url": "http://url2.jpg",
            "preview_url": None
        })
    ]

    result = await artist_controller.get_artist("Test Artist")

    res_dict = result.model_dump() 

    assert "genius" in res_dict
    assert "spotify" in res_dict
    assert "spotify_tracks" in res_dict

    # Checks that the method was actually called once
    mock_genius.get_artist_id.assert_awaited_once()
    mock_redis.set.assert_awaited_once_with(
        "test artist", genius_id, 3600
    )

    mock_db.get_artist.assert_awaited_once()
    mock_db.get_tracks.assert_awaited_once()
        
    # Checks that the method was not called at all
    mock_spotify.get_artist.assert_not_called()


@pytest.mark.asyncio
async def test_get_artist_from_api_if_not_in_db(artist_controller, mock_db, mock_genius, mock_spotify, mock_redis):
    genius_id = 1234

    mock_redis.get.return_value = None

    mock_genius.get_artist_id.return_value = genius_id
    mock_db.get_artist.return_value = None
    mock_db.get_tracks.return_value = []
    
    mock_genius.get_artist.return_value = GeniusArtist(
        id=genius_id,
        name="Test Artist",
        alternate_names=[],
        instagram_name=None,
        twitter_name=None,
        followers_count=1000,
        header_image_url="http://header.jpg",
        image_url="http://avatar.jpg",
        url="http://genius.com/artist"
    )

    mock_spotify.get_artist.return_value = SpotifyArtist(
        name="Test Artist",
        avatar_photo="http://spotify.jpg",
        popularity=80,
        followers_count=1000000,
        genres=["pop"]
    )

    mock_spotify.get_artist_top_tracks.return_value = []

    result = await artist_controller.get_artist("Test Artist")
 
    assert result.spotify.name == "Test Artist"

    # Verifying that the APIs were called
    mock_genius.get_artist.assert_awaited_once()
    mock_redis.set.assert_awaited_once_with(
        "test artist", genius_id, 3600
    )

    mock_spotify.get_artist.assert_awaited_once()
    mock_spotify.get_artist_top_tracks.assert_awaited_once()

    # Verify that the base called the save
    mock_db.add_artist.assert_awaited_once()
    mock_db.add_tracks.assert_awaited_once()

    # Let's make sure that the data was obtained from the API, not from the database
    mock_db.get_artist.assert_awaited_once()
    mock_db.get_tracks.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_artist_id_with_redis(artist_controller, mock_db, mock_genius, mock_redis):
    genius_id = 1234
    artist_json = {
        "genius": {
            "id": genius_id,
            "name": "Test Artist",
            "alternate_names": [],
            "instagram_name": None,
            "twitter_name": None,
            "followers_count": 1000,
            "header_image_url": "http://image.com/header.jpg",
            "image_url": "http://image.com/avatar.jpg",
            "url": "http://genius.com/artist"
        },
        "spotify": {
            "name": "Test Artist",
            "avatar_photo": "http://spotify.com/photo.jpg",
            "popularity": 80,
            "followers_count": 500000,
            "genres": ["pop"]
        }
    }

    mock_redis.get.return_value = str(genius_id)

    mock_db.get_artist.return_value = MagicMock(json=json.dumps(artist_json))
    mock_db.get_tracks.return_value = [
        MagicMock(_asdict=lambda: {
            "spotify_song_id": "id123",
            "artists": "Test Artist",
            "title": "Test Song",
            "release_date": "2024-01-01",
            "cover_url": None,
            "preview_url": None
        }),
        MagicMock(_asdict=lambda: {
            "spotify_song_id": "id456",
            "artists": "Test Artist",
            "title": "Track Two",
            "release_date": "2023-01-01",
            "cover_url": "http://url2.jpg",
            "preview_url": None
        })
    ]

    result = await artist_controller.get_artist("Test Artist")

    res_dict = result.model_dump() 

    assert "genius" in res_dict
    assert "spotify" in res_dict
    assert "spotify_tracks" in res_dict

    # Checks that the method was actually called once
    mock_genius.get_artist_id.assert_awaited_once()
    mock_redis.get.assert_awaited_once()

    mock_db.get_artist.assert_awaited_once()
    mock_db.get_tracks.assert_awaited_once()


@pytest.mark.asyncio 
async def test_get_track_data_without_saving(track_controller, mock_spotify, mock_genius, mock_parser):
    mock_spotify.get_track_id.return_value = "id123"
    mock_track = MagicMock()
    mock_track.model_dump_json.return_value = '{"title": "Test Song"}'
    mock_spotify.get_current_track.return_value = mock_track
    mock_spotify.get_track_details.return_value = SpotifyTrackDetails(
        key="C#m",
        bpm="120",
        camelot="12A",
        popularity="85",
        energy="85",
        danceability="85",
        happiness="85"
    )
    mock_genius.get_artist_song.return_value = "http://genius.com/test-song"
    mock_parser.get_songs_text.return_value = "These are the lyrics"

    result = await track_controller.get_one_track("Test Artist", "Test Track")
    
    assert "track" in result
    assert "details" in result
    assert "lyrics" in result 
    assert result["lyrics"] == "These are the lyrics"

    logger.info(result)

    mock_spotify.get_current_track.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_track_with_data_from_db(track_controller, mock_db):
    mock_track = MagicMock() 
    mock_track._asdict.return_value = {
        "spotify_song_id": "id123",
        "artists": "Test Artist",
        "title": "Test Song"
    }
    mock_db.get_one_track.return_value = mock_track
    
    mock_track_details = MagicMock()
    mock_track_details._asdict.return_value = {"bpm": 122}
    mock_db.get_track_details.return_value = mock_track_details
    
    mock_lyrics = MagicMock()
    mock_lyrics._asdict.return_value = {"lyrics": "These are the lyrics"}
    mock_db.get_lyrics.return_value = mock_lyrics

    result = await track_controller.get_track_with_data("id123")

    assert "track" in result
    assert result["track"]["artists"] == "Test Artist"

    logger.info(result)

    assert "details" in result
    assert "lyrics" in result 
    
    mock_db.get_one_track.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_track_with_data_from_api(track_controller, mock_spotify, mock_genius, mock_parser, mock_db):
    mock_track = MagicMock() 
    mock_track._asdict.return_value = {
        "spotify_song_id": "id123",
        "artists": "Test Artist",
        "title": "Test Song"
    }
    mock_db.get_one_track.return_value = mock_track
   
    mock_db.get_track_details.return_value = None
    mock_db.get_lyrics.return_value = None

    mock_spotify.get_track_details.return_value = {"bpm": 122}
    mock_genius.get_artist_song.return_value = "http://genius.com/song"
    mock_parser.get_songs_text.return_value = "Lyrics from API"

    result = await track_controller.get_track_with_data("id123")

    logger.info(result)

    assert result["lyrics"] == "Lyrics from API"

    mock_spotify.get_track_details.assert_awaited_once()
    mock_genius.get_artist_song.assert_awaited_once()
    mock_parser.get_songs_text.assert_awaited_once()

    mock_db.add_track_details.assert_awaited_once()
    mock_db.add_lyrics.assert_awaited_once()