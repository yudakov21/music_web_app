from sqlalchemy import Table, Text, Column, Integer, String, MetaData, Boolean, TIMESTAMP, DateTime, ForeignKey
from sqlalchemy.sql import func
from fastapi_users.db import SQLAlchemyBaseUserTable
from datetime import datetime
from db.database import Base


metadata = MetaData()


artist = Table(
    'artist',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('genius_id', Integer, unique=True),
    Column('parse_date', DateTime, server_default=func.now()),
    Column("json", String)
)

track = Table(
    'track',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('artist_id', Integer, ForeignKey(artist.c.genius_id), nullable=False),
    Column('spotify_song_id', String, unique=True, nullable=False),
    Column('artists', String, nullable=True),
    Column('title', String, nullable=False),
    Column('release_date', DateTime, nullable=True),
    Column('cover_url', String, nullable=True),
    Column('preview_url', String, nullable=True)
)

track_details = Table(
    'track_details',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('spotify_song_id', String, ForeignKey(track.c.spotify_song_id), nullable=False),
    Column('key', String, nullable=True),
    Column('bpm', String, nullable=True),
    Column('camelot', String, nullable=True),
    Column('popularity', String, nullable=True),
    Column('energy', String, nullable=True),
    Column('danceability', String, nullable=True),
    Column('happiness', String, nullable=True)
)

lyrics = Table(
    'lyrics',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('spotify_song_id', String, ForeignKey(track.c.spotify_song_id), nullable=False),
    Column('text', Text, nullable=True)
)

user = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String, nullable=False),
    Column('username', String, nullable=False),
    Column('registered_at', TIMESTAMP, default=datetime),
    Column('hashed_password', String, nullable=False),
    Column('is_active', Boolean, default=True, nullable=False),
    Column('is_superuser', Boolean, default=False, nullable=False),
    Column('is_verified', Boolean, default=False, nullable=False),
)


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime)
    hashed_password: str = Column(String(length=1024), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)


user_liked_artist = Table(
    'user_liked_artist',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey(
        user.c.id, ondelete="CASCADE"), nullable=False),
    Column('artist_id', Integer, ForeignKey(
        artist.c.genius_id, ondelete="CASCADE"), nullable=False),
    Column('liked_at', DateTime, server_default=func.now())
)

user_liked_track = Table(
    'user_liked_track',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey(
        user.c.id, ondelete="CASCADE"), nullable=False),
    Column('track_id', String, ForeignKey(
        track.c.spotify_song_id, ondelete="CASCADE"), nullable=False),
    Column('liked_at', DateTime, server_default=func.now())
)
