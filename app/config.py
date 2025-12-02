# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medi.db")
DEV_AUTH_TOKEN = os.getenv("DEV_AUTH_TOKEN", "testtoken")

FILE_STORAGE_DIR = os.getenv("FILE_STORAGE_DIR", "./data/audio")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "audio-chunks")
