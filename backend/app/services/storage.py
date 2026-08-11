import os
from datetime import timedelta
from minio import Minio

BUCKET_NAME = os.getenv("MINIO_BUCKET", "erp-documents")

def get_minio_client() -> Minio:
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

    return Minio(
        endpoint,
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        region=region,
        secure=is_secure,
    )

def upload_file_to_minio(file, file_name: str) -> str:
    """Uploads a file to the S3 compatible cloud storage (e.g. Cloudflare R2)"""
    minio_client = get_minio_client()

    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
    
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

    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
    
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

def get_file_url_from_minio(file_name: str) -> str:
    """Generates a presigned URL to download a file securely, valid for 1 hour."""
    minio_client = get_minio_client()
    url = minio_client.get_presigned_url(
        "GET",
        BUCKET_NAME,
        file_name,
        expires=timedelta(hours=1),
    )
    return url

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

class LocalStorageStrategy(StorageStrategy):
    def save_file(self, file: UploadFile, path: str = "norms") -> str:
        os.makedirs(f"uploads/{path}", exist_ok=True)
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"uploads/{path}/{unique_filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

class StorageService:
    def __init__(self, strategy: StorageStrategy):
        self._strategy = strategy

    def save_file(self, file: UploadFile, path: str = "norms") -> str:
        return self._strategy.save_file(file, path)
