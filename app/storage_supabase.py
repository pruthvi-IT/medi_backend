# app/storage_supabase.py
import os
from supabase import create_client
from urllib.parse import quote_plus

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "audio-chunks")


def _get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for supabase storage")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def create_signed_upload_url(object_key: str, expires_in: int = 3600):
    """
    Returns dict: {
        "signed_url": "<signed PUT URL>",
        "path": "<bucket/path>",
        "public_url": "<public GET url template>",
    }
    """
    client = _get_supabase_client()
    bucket = STORAGE_BUCKET

    resp = client.storage.from_(bucket).create_signed_upload_url(path=object_key, expires_in=expires_in)
    signed_url = resp.get("signed_url")
    path = resp.get("path") or object_key

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{quote_plus(object_key)}"

    return {"signed_url": signed_url, "path": path, "public_url": public_url}


def create_signed_get_url(object_key: str, expires_in: int = 3600):
    client = _get_supabase_client()
    bucket = STORAGE_BUCKET
    resp = client.storage.from_(bucket).create_signed_url(path=object_key, expires_in=expires_in)
    return {"signed_url": resp.get("signed_url")}
