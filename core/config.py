import os
from dotenv import load_dotenv
from utils.env import load_env_var


load_dotenv()


DB_NAME = load_env_var("DB_NAME")
DB_HOST = load_env_var("DB_HOST")
DB_PASS = load_env_var("DB_PASS")
DB_PORT = load_env_var("DB_PORT")
DB_USER = load_env_var("DB_USER")

REDIS_HOST = load_env_var("REDIS_HOST")
REDIS_PORT = load_env_var("REDIS_PORT")

SECRET = load_env_var("SECRET")

GENIUS_ACCESS = load_env_var("GENIUS_ACCESS")
SPOTIFY_ACCESS = load_env_var("SPOTIFY_ACCESS")
SPOTIFY_ID = load_env_var("SPOTIFY_ID")
SPOTIFY_SECRET = load_env_var("SPOTIFY_SECRET")

OPENAI_API_TOKEN = load_env_var("OPENAI_API_TOKEN")
