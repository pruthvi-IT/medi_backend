# app/storage.py
import os

STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "supabase").lower()

if STORAGE_PROVIDER == "supabase":
    from app.storage_supabase import create_signed_upload_url, create_signed_get_url
else:
    # Fallback: keep previous S3/MinIO code if you want, or raise.
    def create_signed_upload_url(*args, **kwargs):
        raise RuntimeError("Non-supabase providers not implemented. Set STORAGE_PROVIDER=supabase and add SUPABASE env vars.")

    def create_signed_get_url(*args, **kwargs):
        raise RuntimeError("Non-supabase providers not implemented. Set STORAGE_PROVIDER=supabase and add SUPABASE env vars.")
