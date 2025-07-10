import pytest
from unittest.mock import AsyncMock
from services.controller import ArtistController, TrackController


@pytest.fixture
def mock_genius():
    return AsyncMock()

@pytest.fixture
def mock_parser():
    return AsyncMock()

@pytest.fixture
def mock_spotify():
    return AsyncMock()

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def artist_controller(mock_genius, mock_parser, mock_spotify, mock_db):
    return ArtistController(
        genius=mock_genius,
        genius_parser=mock_parser,
        spotify=mock_spotify,
        manager=mock_db
    )

@pytest.fixture
def track_controller(mock_genius, mock_parser, mock_spotify, mock_db):
    return TrackController(
        genius=mock_genius,
        genius_parser=mock_parser,
        spotify=mock_spotify,
        manager=mock_db
    )