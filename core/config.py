import os
from dotenv import load_dotenv


load_dotenv()


DB_NAME = os.environ.get("DB_NAME")
DB_HOST = os.environ.get("DB_HOST")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USER")

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

SECRET = os.environ.get("SECRET")

GENIUS_ACCESS = os.environ.get("GENIUS_ACCESS")
SPOTIFY_ACCESS = os.environ.get("SPOTIFY_ACCESS")
SPOTIFY_ID = os.environ.get("SPOTIFY_ID")
SPOTIFY_SECRET = os.environ.get("SPOTIFY_SECRET")

OPENAI_API_TOKEN = os.environ.get("OPENAI_API_TOKEN")
