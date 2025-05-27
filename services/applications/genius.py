import aiohttp
from fastapi import HTTPException
from bs4 import BeautifulSoup
from schemas.service_schemas import GeniusArtist


class GeniusAPI:
    def __init__(self, access_token: str):
        self._token = access_token
        self.request_params = {
            "access_token": self._token
        }
    
    feature_symbols = [",", "&"]
    def featured_artist(self, artist_name: str) -> bool:
        for feature_symbol in GeniusAPI.feature_symbols:
            if feature_symbol in artist_name:
                return True
        return False

    async def get_artist_id(self, artist_name:str) -> int:
        async with aiohttp.ClientSession() as session:
            url = "http://api.genius.com/search"
            request_params = self.request_params
            request_params['q'] = artist_name
            async with session.get(url=url, params=request_params) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch Genius data")
                data = await response.json()

            hits = data.get("response", {}).get("hits",[])

            # 1)  Trying to find where type == "artist" and the name matches
            for hit in hits:
                if hit["type"] == "artist":
                    result = hit["result"] # an artist
                    name_lower = result["name"].lower().strip()
                    if name_lower == artist_name.lower().strip():
                        if not self.featured_artist(result["name"]):
                            return result["id"]

            # 2) If there's no "artist", look for "song".
            for hit in hits:
                if hit["type"] == "song":
                    result = hit["result"]
                    primary_result = result["primary_artist"]

                    if not result["featured_artists"]:
                        primary_name = primary_result["name"].strip()
                        if not self.featured_artist(primary_name):
                            if primary_name.lower() == artist_name.lower():
                                return primary_result["id"]

            raise Exception("Cannot find a suitable artist in hits")
            
    async def get_artist(self, artist_id: int) -> GeniusArtist:       
        async with aiohttp.ClientSession() as session:
            url = f"http://api.genius.com/artists/{artist_id}"
            async with session.get(url=url, params=self.request_params) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch Genius data")
                data = await response.json()

                artist_dict: dict = data["response"]["artist"]
                if artist_dict["image_url"].startswith("https://assets.genius.com/images/default_avatar"):
                    raise Exception("Artist has default avatar")
                artist = GeniusArtist(**artist_dict)
                return artist
        
    async def get_artist_song(self, artist_name: str, track_title: str):
        async with aiohttp.ClientSession() as session:
            url = "http://api.genius.com/search"
            request_params = self.request_params
            query = f"{artist_name} {track_title}"
            request_params['q'] = query
            async with session.get(url=url, params=request_params) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch Genius data")
                data = await response.json()

            hits = data.get("response", {}).get("hits",[])
            
            for hit in hits:
                if hit["type"] == "song":
                    return hit["result"]["url"]
            return None


class GeniusParser:
    async def get_track_links(self, artist_page_url: str)-> list[str]:
        async with aiohttp.ClientSession() as session:
            links = []
            async with session.get(artist_page_url) as response:
                soup = BeautifulSoup(await response.text(), 'lxml')
                for track in soup.find_all(class_="mini_card_grid-song"):
                    link = track.find(class_="mini_card", href=True)
                    links.append(link.get('href'))
            return links

    async def get_songs_text(self, track_url: str)-> list[str]:
        async with aiohttp.ClientSession() as session:

            async with session.get(track_url) as response:
                soup = BeautifulSoup(await response.text(), 'lxml')
                lyrics_div = soup.find(class_="Lyrics-sc-1bcc94c6-1 bzTABU")
                if not lyrics_div:
                    return None
                lyrics = lyrics_div.get_text(separator="\n").strip()
                return lyrics


