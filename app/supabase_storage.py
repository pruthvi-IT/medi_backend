# app/supabase_storage.py
from typing import Optional

from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_BUCKET

_client = None


def get_client():
    """
    Lazily initialize and return a Supabase client.
    """
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client


def get_public_url(object_key: str) -> str:
    """
    For a PUBLIC bucket, the public URL is deterministic.

    You must create a public bucket in Supabase named SUPABASE_BUCKET.

    Pattern:
    https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
    """
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{object_key}"


def upload_file_from_path(local_path: str, object_key: str) -> Optional[str]:
    """
    Uploads the local file to Supabase Storage at object_key.
    Returns the public URL if successful.
    """
    client = get_client()

    with open(local_path, "rb") as f:
        # overwrite if exists
        client.storage.from_(SUPABASE_BUCKET).upload(
            object_key,
            f,
            file_options={"content-type": "audio/wav"},
        )

    return get_public_url(object_key)
