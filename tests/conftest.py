import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_genius():
    return AsyncMock()

@pytest.fixture
def mock_spotify():
    return AsyncMock()

@pytest.fixture
def mock_parser():
    return AsyncMock()

@pytest.fixture
def mock_db():
    return AsyncMock()
