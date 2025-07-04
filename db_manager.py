import json

from logger import logger
from typing import List
from models.models import artist, track, track_details, lyrics, user_liked_artist, user_liked_track
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from schemas.service_schemas import SpotifyTrack, SpotifyTrackDetails, TrackRead, ArtistRead


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
        if not tracks:
            return
        
        stmt = pg_insert(track).values([
            {
                "artist_id": artist_id,
                "spotify_song_id": track_.spotify_song_id,
                "artists": track_.artists,
                "title": track_.title,
                "release_date": track_.release_date,
                "cover_url": track_.cover_url,
                "preview_url": track_.preview_url
            } for track_ in tracks
        ])

        do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=["spotify_song_id"])
        await self.session.execute(do_nothing_stmt)
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
    

    async def add_track_details(self, spotify_song_id: str, details: SpotifyTrackDetails):
        stmt = insert(track_details).values(
            spotify_song_id=spotify_song_id,
            **details.model_dump()
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_track_details(self, track_id: str):
        query = select(track_details).where(track_details.c.spotify_song_id == track_id)
        res = await self.session.execute(query)
        return res.fetchone()
    

    async def add_lyrics(self, track_id: str, lyrics_text: str):
        stmt = insert(lyrics).values(
            spotify_song_id=track_id,
            text=lyrics_text
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_lyrics(self, track_id: str, lyrics_text: str):
        stmt = update(lyrics).where(lyrics.c.spotify_song_id == track_id).values(text = lyrics_text)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_lyrics(self, track_id: str):
        query = select(lyrics).where(lyrics.c.spotify_song_id == track_id)
        res = await self.session.execute(query)
        return res.fetchone()
    
    
    async def get_artist_by_genres(self, artist_id: int):
        base_artist_row = await self.get_artist(artist_id)

        if not base_artist_row:
            return []
        
        base_json = base_artist_row['json']
        base_genres = json.loads(base_json)['spotify'].get('genres', [])

        if not base_genres:
            return []
        
        query = select(artist).where(artist.c.genius_id != artist_id)
        res = await self.session.execute(query)
        rows = res.fetchall()
        
        similar = []

        for row in rows:
            data = json.loads(row._mapping['json'])
            other_genres = data.get('spotify', {}).get('genres', [])
            
            if set(base_genres) & set(other_genres):
                similar.append(row._mapping)
        return similar


    async def like_track(self, user_id:int, track_id: str):
        stmt = insert(user_liked_track).values(user_id=user_id, track_id=track_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def unlike_track(self, user_id:int, track_id: str):
        stmt = delete(user_liked_track).where(
            user_liked_track.c.user_id == user_id,
            user_liked_track.c.track_id == track_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_liked_tracks(self, user_id: int) -> List[TrackRead]:
        try:
            query = select(track).where(
                track.c.spotify_song_id.in_(
                    select(user_liked_track.c.track_id).where(user_liked_track.c.user_id == user_id)
                )
            )
            
            res = await self.session.execute(query)
            rows = res.mappings().all()

            if not rows:
                return []

            tracks = [TrackRead(
                artist_id=row['artist_id'],
                spotify_song_id=row['spotify_song_id'],
                artists=row['artists'],
                title=row['title'],
                cover_url=row['cover_url'],
            ) for row in rows]

            return tracks

        except Exception as e:
            logger.exception(f"Error: {e}")
            return []
        

    async def like_artist(self, user_id:int, artist_id: int):
        stmt = insert(user_liked_artist).values(user_id=user_id, artist_id=artist_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def unlike_artist(self, user_id:int, artist_id: int):
        stmt = delete(user_liked_artist).where(
            user_liked_artist.c.user_id == user_id,
            user_liked_artist.c.artist_id == artist_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_liked_artists(self, user_id: int) -> List[ArtistRead]:
        try:
            query = select(artist).where(
                artist.c.genius_id.in_(
                    select(user_liked_artist.c.artist_id).where(user_liked_artist.c.user_id == user_id)
                )
            )

            res = await self.session.execute(query)
            rows = res.mappings().all()

            if not rows:
                return []

            artists = []
            for row in rows:
                try:
                    artist_data = json.loads(row['json']) if row.get('json') else {}
                    # print(artist_data)
                    name = artist_data.get('genius').get('name', 'Unknown Artist')
                    cover_url = artist_data.get('genius').get('avatar_photo', None)

                    artist_obj = ArtistRead(
                        genius_id=row['genius_id'],
                        name=name,
                        cover_url=cover_url
                    )
                    artists.append(artist_obj)
                except Exception as e:
                    logger.exception(f"Error: {e}")
                    continue

            return artists

        except Exception as e:
            logger.exception(f"Error: {e}")
            return []