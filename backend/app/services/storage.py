import os
from datetime import timedelta
from minio import Minio

BUCKET_NAME = os.getenv("MINIO_BUCKET", "erp-documents")

_minio_client_instance: Minio | None = None
_bucket_ensured: bool = False

def get_minio_client() -> Minio:
    global _minio_client_instance
    if _minio_client_instance is not None:
        return _minio_client_instance

    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "MINIO_ENDPOINT is not configured. Set it in .env to use Cloud Storage."
        )

    is_secure = os.getenv("MINIO_SECURE", "true").lower() == "true"
    region = os.getenv("MINIO_REGION", "auto")

    if endpoint.startswith("http://"):
        endpoint = endpoint[7:]
        is_secure = False
    elif endpoint.startswith("https://"):
        endpoint = endpoint[8:]
        is_secure = True

    _minio_client_instance = Minio(
        endpoint,
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        region=region,
        secure=is_secure,
    )
    return _minio_client_instance

def _ensure_bucket_exists(client: Minio):
    global _bucket_ensured
    if not _bucket_ensured:
        try:
            if not client.bucket_exists(BUCKET_NAME):
                client.make_bucket(BUCKET_NAME)
            _bucket_ensured = True
        except Exception as e:
            print(f"Warning checking MinIO bucket: {e}")

def upload_file_to_minio(file, file_name: str) -> str:
    """Uploads a file to the S3 compatible cloud storage (e.g. Cloudflare R2)"""
    minio_client = get_minio_client()
    _ensure_bucket_exists(minio_client)
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    minio_client.put_object(
        BUCKET_NAME,
        file_name,
        file.file, 
        length=file_size,
        part_size=10*1024*1024,
        content_type=file.content_type
    )
    return file_name

def upload_buffer_to_minio(buffer, file_name: str, content_type: str = "application/pdf") -> str:
    """Uploads an in-memory buffer to the S3 compatible cloud storage"""
    minio_client = get_minio_client()
    _ensure_bucket_exists(minio_client)
    
    buffer.seek(0, 2)
    file_size = buffer.tell()
    buffer.seek(0)
    
    minio_client.put_object(
        BUCKET_NAME,
        file_name,
        buffer, 
        length=file_size,
        part_size=10*1024*1024,
        content_type=content_type
    )
    return file_name

from urllib.parse import urlparse, unquote

def extract_minio_key(file_name_or_url: str) -> str:
    """Extracts the clean MinIO object key from a full URL, presigned URL, or raw key."""
    if not file_name_or_url:
        return ""
    
    # Strip query parameters (e.g. presigned signature params)
    path = file_name_or_url.split("?")[0].strip()
    
    # If it is a full URL, parse the pathname
    if "://" in path:
        parsed = urlparse(path)
        path = unquote(parsed.path)
    
    path = path.lstrip("/")
    
    # Strip bucket name if present at the start of the path
    if path.startswith(f"{BUCKET_NAME}/"):
        path = path[len(BUCKET_NAME) + 1:]
    
    return path

def get_file_url_from_minio(file_name: str, expires: timedelta = timedelta(days=7)) -> str:
    """Generates a presigned URL to download a file securely, valid for up to 7 days."""
    if not file_name:
        return ""
    clean_key = extract_minio_key(file_name)
    if not clean_key:
        return ""
    try:
        minio_client = get_minio_client()
        url = minio_client.get_presigned_url(
            "GET",
            BUCKET_NAME,
            clean_key,
            expires=expires,
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL for {file_name}: {e}")
        return file_name

def delete_file_from_minio(file_name: str):
    """Deletes a file from the S3 compatible cloud storage."""
    minio_client = get_minio_client()
    try:
        minio_client.remove_object(BUCKET_NAME, file_name)
    except Exception as e:
        print(f"Error deleting file {file_name} from MinIO: {e}")

from abc import ABC, abstractmethod
import shutil
import uuid
from fastapi import UploadFile

class StorageStrategy(ABC):
    @abstractmethod
    def save_file(self, file: UploadFile, path: str = "norms") -> str:
        pass

class MinioStorageStrategy(StorageStrategy):
    def save_file(self, file: UploadFile, path: str = "norms") -> str:
        unique_filename = f"uploads/{path}/{uuid.uuid4()}_{file.filename}"
        return upload_file_to_minio(file, unique_filename)

class StorageService:
    def __init__(self, strategy: StorageStrategy):
        self._strategy = strategy

    def save_file(self, file: UploadFile, path: str = "norms") -> str:
        return self._strategy.save_file(file, path)
