import re
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

        hits = data.get("response", {}).get("hits", [])
        target_name = artist_name.strip().lower()

        def is_valid_artist(name: str) -> bool:
            return name.strip().lower() == target_name and not self.featured_artist(name)

        # first search for type == "artist"
        for hit in hits:
            if hit.get("type") == "artist":
                name = hit["result"]["name"]
                if is_valid_artist(name):
                    return hit["result"]["id"]

        # then, search among the songs
        for hit in hits:
            if hit.get("type") == "song":
                result = hit["result"]
                if result.get("featured_artists"):
                    continue

                primary_artist = result.get("primary_artist", {})
                name = primary_artist.get("name", "")
                if is_valid_artist(name):
                    return primary_artist["id"]

        raise Exception("The artist name is incorrect or there is no such artist on Genius :(")
            
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
                html = await response.text()
        soup = BeautifulSoup(html, 'lxml')
        for track in soup.find_all(class_="mini_card_grid-song"):
            link = track.find(class_="mini_card", href=True)
            links.append(link.get('href'))
        return links

    async def get_songs_text(self, track_url: str)-> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(track_url) as response:
                html = await response.text()
        soup = BeautifulSoup(html, 'lxml') 
        lyrics_div = soup.find_all('div', attrs={"class": re.compile(r"^Lyrics__Container-sc-")}) # Lyrics-sc-7c7d0940-1 gVRfzh 
        
        if not lyrics_div:
            return None
        
        full_text = "\n".join(div.get_text(separator="\n").strip() for div in lyrics_div)

        start_keywords = ["[Intro", "[Verse", "[Chorus", "[Bridge", "[Outro", "[Refrain", 
                            "[Post-Chorus", "[Pre-Chorus", "[Breakdown", "[Interlude:", "[Skit:"]
        for keyword in start_keywords:
            idx = full_text.find(keyword)
            if idx != -1:
                full_text = full_text[idx:]
                break

        return full_text


