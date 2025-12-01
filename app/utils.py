# app/utils.py
import os
import boto3
from botocore.client import Config
from urllib.parse import urljoin

STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "minio").lower()  # "s3" in prod
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

# MinIO (dev) defaults
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audio-chunks")


def _create_s3_client():
    """
    Create an AWS S3 client using AWS credentials from environment.
    If AWS credentials are not present, boto3 will use its default chain.
    """
    return boto3.client(
        "s3",
        region_name=os.getenv("S3_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def _create_minio_client():
    """
    Create an S3-compatible client for MinIO (dev).
    """
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def generate_presigned_put_url(key: str, content_type: str, expires_in: int = 3600):
    """
    Returns: (url, public_url, bucket, key)
    - url: presigned URL for PUT
    - public_url: read URL (public-facing)
    - bucket: bucket name
    - key: object key

    The function switches behavior based on STORAGE_PROVIDER env var:
      - "s3": uses AWS S3 and returns AWS-style public URL
      - otherwise: uses MinIO endpoint (dev)
    """
    if STORAGE_PROVIDER == "s3":
        client = _create_s3_client()
        bucket = S3_BUCKET
        if not bucket:
            raise RuntimeError("S3_BUCKET env var is required for STORAGE_PROVIDER=s3")
        url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )
        public_url = f"https://{bucket}.s3.{S3_REGION}.amazonaws.com/{key}"
        return url, public_url, bucket, key
    else:
        # MinIO / S3-compatible local flow
        client = _create_minio_client()
        bucket = MINIO_BUCKET
        try:
            client.head_bucket(Bucket=bucket)
        except Exception:
            client.create_bucket(Bucket=bucket)
        url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )
        public_url = urljoin(MINIO_ENDPOINT + "/", f"{bucket}/{key}")
        return url, public_url, bucket, key
