import os
from minio import Minio
from minio.error import S3Error

from settings import settings


# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
)

# Ensure the bucket exists

try:
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        print(f"Bucket '{settings.MINIO_BUCKET_NAME}' created.")
    else:
        print(f"Bucket '{settings.MINIO_BUCKET_NAME}' already exists.")
except S3Error as error:
    print(f"Error creating bucket '{error}'")
