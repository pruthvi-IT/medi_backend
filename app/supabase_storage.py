# app/supabase_storage.py
from typing import Optional

import logging
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_BUCKET

_client = None
logger = logging.getLogger("uvicorn.error")


def get_client():
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client


def ensure_bucket_exists():
    client = get_client()
    try:
        buckets = client.storage.list_buckets()
        logger.info("Supabase: listed %s buckets", len(buckets) if buckets else 0)
    except Exception as e:
        logger.warning("Supabase: list_buckets failed: %s", e)
        buckets = []
    exists = False
    for b in buckets or []:
        name = getattr(b, "name", None)
        if not name and isinstance(b, dict):
            name = b.get("name")
        if name == SUPABASE_BUCKET:
            exists = True
            break
    if not exists:
        try:
            logger.info("Supabase: creating bucket '%s'", SUPABASE_BUCKET)
            client.storage.create_bucket(SUPABASE_BUCKET)
            # Verify creation
            created = None
            try:
                created = client.storage.get_bucket(SUPABASE_BUCKET)
            except Exception:
                created = None
            logger.info("Supabase: bucket '%s' created: %s", SUPABASE_BUCKET, bool(created))
        except Exception as e:
            logger.error("Supabase: create_bucket failed: %s", e)
            raise


def get_public_url(object_key: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{object_key}"


def upload_file_from_path(local_path: str, object_key: str) -> Optional[str]:
    client = get_client()
    try:
        with open(local_path, "rb") as f:
            client.storage.from_(SUPABASE_BUCKET).upload(
                object_key,
                f,
                file_options={"content-type": "audio/wav"},
            )
    except Exception as e:
        msg = str(e)
        if "Bucket not found" in msg:
            logger.warning("Supabase: bucket '%s' missing; creating and retrying", SUPABASE_BUCKET)
            ensure_bucket_exists()
            with open(local_path, "rb") as f:
                client.storage.from_(SUPABASE_BUCKET).upload(
                    object_key,
                    f,
                    file_options={"content-type": "audio/wav"},
                )
        else:
            raise

    return get_signed_url(object_key)


def get_signed_url(object_key: str, expires_in: int = 3600) -> str:
    client = get_client()
    res = client.storage.from_(SUPABASE_BUCKET).create_signed_url(object_key, expires_in)
    url = None
    if isinstance(res, dict):
        url = res.get("signedURL") or res.get("signed_url") or res.get("url")
    if not url:
        try:
            url = str(res)
        except Exception:
            url = None
    if not url:
        raise RuntimeError("Failed to create signed URL")
    return url
