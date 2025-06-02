from models.models import artist, track, track_details, lyrics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from schemas.service_schemas import SpotifyTrack, SpotifyTrackDetails

class DatabaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_artist(self, genius_id: int, json: str):
        stmt = insert(artist).values(
            genius_id = genius_id,
            json = json
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_artist(self, artist_id: int):
        query = select(artist).where(artist.c.genius_id == artist_id)
        res = await self.session.execute(query)
        artist_record =  res.fetchone()
        return artist_record._mapping if artist_record else None
    

    async def add_tracks(self, artist_id: int, tracks: list[SpotifyTrack]):
        track_ids = [track_.spotify_song_id for track_ in tracks]

        query = select(track.c.spotify_song_id).where(track.c.spotify_song_id.in_(track_ids))
        result = await self.session.execute(query)
        existing_ids = {row[0] for row in result.fetchall()}

        new_tracks = [
            {
                "artist_id": artist_id,
                "spotify_song_id": track_.spotify_song_id,
                "artists": track_.artists,
                "title": track_.title,
                "release_date": track_.release_date,
                "cover_url": track_.cover_url,
                "preview_url": track_.preview_url
            }
            for track_ in tracks if track_.spotify_song_id not in existing_ids
        ]

        if new_tracks:
            stmt = insert(track)
            await self.session.execute(stmt, new_tracks)
            await self.session.commit()


    async def add_track(self, artist_id: int, track: SpotifyTrack):
        stmt = insert(track).values(
            artist_id = artist_id,
            **track.model_dump()
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_tracks(self, artist_id: int):
        query = select(track).where(track.c.artist_id == artist_id)
        res = await self.session.execute(query)
        return res.fetchall()
    
    async def get_one_track(self, track_id: str):
        query = select(track).where(track.c.spotify_song_id == track_id)
        res = await self.session.execute(query)
        return res.fetchone()


    async def add_track_details(self, track_id: int, details: SpotifyTrackDetails):
        stmt = insert(track_details).values(
            track_id=track_id,
            **details.model_dump()
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_track_details(self, track_id: int):
        query = select(track_details).where(track_details.c.track_id == track_id)
        res = await self.session.execute(query)
        return res.fetchone()
    

    async def add_lyrics(self, track_id: int, lyrics_text: str):
        stmt = insert(lyrics).values(
            track_id=track_id,
            text=lyrics_text
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_lyrics(self, track_id: int):
        query = select(lyrics).where(lyrics.c.track_id == track_id)
        res = await self.session.execute(query)
        return res.fetchone()