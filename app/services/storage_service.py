import uuid
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/msword": "doc",
    "application/vnd.ms-powerpoint": "ppt",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class StorageService:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        except S3Error as e:
            raise RuntimeError(f"Cannot access Minio bucket: {e}") from e

    def upload(self, data: bytes, user_id: str, original_filename: str, content_type: str) -> str:
        ext = _ALLOWED_CONTENT_TYPES.get(content_type, "bin")
        s3_key = f"{user_id}/{uuid.uuid4()}.{ext}"
        self._client.put_object(
            self._bucket,
            s3_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return s3_key

    def get_presigned_url(self, s3_key: str, expires: int = 3600) -> str:
        url = self._client.presigned_get_object(
            self._bucket,
            s3_key,
            expires=timedelta(seconds=expires),
        )
        return url

    def delete(self, s3_key: str) -> None:
        self._client.remove_object(self._bucket, s3_key)

    @staticmethod
    def allowed_content_type(content_type: str) -> bool:
        return content_type in _ALLOWED_CONTENT_TYPES

    @staticmethod
    def max_size() -> int:
        return MAX_FILE_SIZE

    _IMAGE_EXT_BY_MIME = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/webp": "webp",
    }

    def upload_image(self, data: bytes, material_id: str, order: int, mime: str) -> str:
        ext = self._IMAGE_EXT_BY_MIME.get(mime, "bin")
        s3_key = f"images/{material_id}/{order}.{ext}"
        self._client.put_object(
            self._bucket,
            s3_key,
            BytesIO(data),
            length=len(data),
            content_type=mime,
        )
        return s3_key

    def get_image(self, s3_key: str) -> tuple[bytes, str]:
        response = self._client.get_object(self._bucket, s3_key)
        try:
            data = response.read()
            content_type = response.headers.get("Content-Type", "application/octet-stream")
        finally:
            response.close()
            response.release_conn()
        return data, content_type

    def delete_prefix(self, prefix: str) -> None:
        objects = self._client.list_objects(self._bucket, prefix=prefix, recursive=True)
        for obj in objects:
            try:
                self._client.remove_object(self._bucket, obj.object_name)
            except S3Error:
                pass
