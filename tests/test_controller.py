import pytest
import json

from unittest.mock import MagicMock
from services.controller import ArtistController
from schemas.service_schemas import AllStats, GeniusArtist, SpotifyArtist, SpotifyTrack, SpotifyTrackDetails


@pytest.mark.asyncio
async def test_get_artist(mock_db, mock_genius, mock_parser, mock_spotify):
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

    controller = ArtistController(
        genius=mock_genius,
        genius_parser=mock_parser,
        spotify=mock_spotify,
        manager=mock_db
    )

    result = await controller.get_artist("Test Artist")

    res_dict = result.model_dump() # to dict

    assert "genius" in res_dict
    assert "spotify" in res_dict
    assert "spotify_tracks" in res_dict

    # Checks that the method was actually called once
    mock_genius.get_artist_id.assert_awaited_once()
    mock_db.get_artist.assert_awaited_once()
    mock_db.get_tracks.assert_awaited_once()
        
    # Checks that the method was not called at all
    mock_spotify.get_artist.assert_not_called()


@pytest.mark.asyncio
async def test_get_artist_from_api_if_not_in_db(mock_db, mock_genius, mock_parser, mock_spotify):
    genius_id = 1234
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

    controller = ArtistController(
        genius=mock_genius,
        genius_parser=mock_parser,
        spotify=mock_spotify,
        manager=mock_db
    )

    result = await controller.get_artist("Test Artist")
 
    assert result.spotify.name == "Test Artist"

    # Verifying that the APIs were called
    mock_genius.get_artist.assert_awaited_once()
    mock_spotify.get_artist.assert_awaited_once()
    mock_spotify.get_artist_top_tracks.assert_awaited_once()

    # Verify that the base called the save
    mock_db.add_artist.assert_awaited_once()
    mock_db.add_tracks.assert_awaited_once()

    # Verify that the old data was not actually used
    mock_db.get_artist.assert_awaited_once()
    mock_db.get_tracks.assert_awaited_once()


