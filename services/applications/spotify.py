import aiohttp
import os
import base64
import time
import random
from bs4 import BeautifulSoup
import cloudscraper

from schemas.service_schemas import SpotifyArtist, SpotifyTrack, SpotifyTrackDetails
from services.applications.genius import GeniusAPI, GeniusParser



scraper = cloudscraper.create_scraper()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://tunebat.com/"
}


class SpotifyAPI:
    def __init__(self, access_token: str, client_id:str, client_secret: str, genius: GeniusAPI, genius_parser: GeniusParser) -> None:
        self._token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.genius = genius
        self.genius_parser = genius_parser
        self.dheaders = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type" : "application/x-www-form-urlencoded"
        }

    async def refresh_token(self):
        # Form Basic auth from client_id and client_secret
        auth_base64 = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        url = f"https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_base64}"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": os.environ["SPOTIFY_REFRESH"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data=data, headers=headers) as response:
                resp_text = await response.json()


                self._token = resp_text["access_token"]
                self.dheaders["Authorization"] = f"Bearer {self._token}"

    async def get_artist_id(self, artist_name:str) -> int:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.spotify.com/v1/search"
            params = {
                'q': artist_name,
                'type': "artist"
            }
            async with session.get(url=url, headers=self.dheaders, params=params) as response:
                data = await response.json()
                try:
                    artists = data["artists"]
                except KeyError:
                    await self.refresh_token()
                    return await self.get_artist_id(artist_name)
                first_artist_id = artists['items'][0]['id']
                return first_artist_id

    async def get_artist(self, artist_id: int):
        async with aiohttp.ClientSession() as session:
            url = f"https://api.spotify.com/v1/artists/{artist_id}"
            async with session.get(url=url, headers=self.dheaders) as response:
                data = await response.json()
                try:
                    artist = SpotifyArtist(
                        name=data["name"],
                        genres=data["genres"],
                        followers_count=data["followers"]["total"],
                        avatar_photo=data["images"][0]["url"],
                        popularity=data["popularity"]
                    )
                    return artist
                except Exception as e:
                    raise Exception()
    
    async def get_artist_top_tracks(self, artist_id: str) -> list[SpotifyTrack]:
        start_time = time.perf_counter() 
        async with aiohttp.ClientSession() as session:
            url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=ES"
            async with session.get(url=url, headers=self.dheaders) as response:
                data = await response.json(content_type=None)

                # If there is no "tracks" key, we need to catch the error
                tracks = data.get("tracks", [])

                tracks_items: list[SpotifyTrack] = []
                for track in tracks[:10]:

                    artist_names = ", ".join(artist["name"] for artist in track["artists"])

                    track_obj = SpotifyTrack(
                        spotify_song_id=track["id"],
                        artist=artist_names,
                        title=track["name"],
                        release_date=track["album"]["release_date"],
                        cover_url=track["album"]["images"][0]["url"],
                        preview_url=track["preview_url"],
                    ) 
                    tracks_items.append(track_obj)

                end_time = time.perf_counter() 
                print(f"Execution time: {end_time - start_time:.2f} seconds")
                return tracks_items
    
            
    async def get_track_details(
        self, 
        track_id: str, 
    ) -> SpotifyTrackDetails | None:
        """
        Here we're off to Tunebat, not Spotify's audio-features
        track_name: 'Gods plan'
        artist_name: 'Drake'
        track_id: '788Sc88rcfsfdsf'
        """

        url = f"https://tunebat.com/Info/-/{track_id}"

        try: 
            print(f"Fetching URL: {url}")
            response = scraper.get(url=url, headers=headers)
            
            if response.status_code == 200:

                soup = BeautifulSoup(response.content, "lxml")

                key = soup.find("p", string="Key").find_previous_sibling("p").get_text(strip=True)
                bpm = soup.find("p", string="BPM").find_previous_sibling("p").get_text(strip=True)
                camelot = soup.find("p", string="Camelot").find_previous_sibling("p").get_text(strip=True)
                popularity = soup.find("p", string="Popularity").find_previous_sibling("p").get_text(strip=True)
                energy = soup.find("div", class_="ant-col GFAiD Vwk-7 qYBvC ant-col-xs-8 ant-col-sm-8").get_text(strip=True)
                danceability = soup.find("div", class_="ant-col GFAiD qYBvC ant-col-xs-8 ant-col-sm-8").get_text(strip=True)
                happiness = soup.find("div", class_="ant-col GFAiD qYBvC Vwk-7 ant-col-xs-8 ant-col-sm-8").get_text(strip=True)
                
                track_details = SpotifyTrackDetails(
                    key=key,
                    bpm=bpm,
                    camelot=camelot,
                    popularity=popularity,
                    energy=energy,
                    danceability=danceability,
                    happiness=happiness
                )
                print(f"Data were successfully obtained for {url}")
                time.sleep(random.uniform(1, 6))
                return track_details
            else:
                print(f"[Tunebat] status={response.status_code} url={url}")
                    
        except Exception as e:
            print(f"An error occurred at the URL {url}: {e}")
        finally:
            print("Data collection is complete")