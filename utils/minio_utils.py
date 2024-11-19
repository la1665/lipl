import io
import base64
from fastapi import HTTPException, status
from minio import S3Error

from minio_db.engine import minio_client
from settings import settings

def upload_profile_image(file_data: bytes, user_id: int, filename: str, content_type: str) -> str:
    """
    Uploads a profile image to MinIO and returns the URL.
    The filename will be formatted as '{user_id}-{original_filename}'.
    """
    unique_filename = f"{user_id}-{filename}"
    file_length = len(file_data)
    try:
        # Upload file to MinIO
        minio_client.put_object(
            bucket_name=settings.MINIO_PROFILE_IMAGE_BUCKET,
            object_name=unique_filename,
            data=io.BytesIO(file_data),
            length=file_length,
            content_type=content_type  # Adjust based on file type
        )


        # Generate a pre-signed URL for accessing the image
        image_url = minio_client.presigned_get_object(
            settings.MINIO_PROFILE_IMAGE_BUCKET, unique_filename
        )
        return image_url

    except S3Error as error:
        print(f"Error uploading profile image: {error}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload profile image."
            )


def delete_profile_image(filename: str) -> None:
    """
    Deletes a profile image from MinIO.
    """
    try:
        minio_client.remove_object(settings.MINIO_PROFILE_IMAGE_BUCKET, filename)
        print(f"Deleted profile image: {filename}")
    except S3Error as e:
        print(f"Error deleting profile image: {e}")
        raise



def upload_vehicle_full_image(base64_image, filename: str, content_type: str) -> str:
    """
    Uploads a full vehicle image to the designated MinIO bucket and returns the URL.
    """
    image_data = base64.b64decode(base64_image)
    image_bytes = io.BytesIO(image_data)

    try:
        # Upload full image to MinIO
        minio_client.put_object(
            bucket_name=settings.MINIO_FULL_IMAGE_BUCKET,
            object_name=filename,
            data=image_bytes,
            length=len(image_data),
            content_type=content_type
        )

        # Generate a pre-signed URL for accessing the image
        image_url = minio_client.presigned_get_object(
            settings.MINIO_FULL_IMAGE_BUCKET, filename
        )
        return image_url

    except S3Error as error:
        print(f"Error uploading full vehicle image: {error}")
        raise

def delete_vehicle_full_image(filename: str) -> None:
    """
    Deletes a full vehicle image from MinIO.
    """
    try:
        minio_client.remove_object(settings.MINIO_FULL_IMAGE_BUCKET, filename)
        print(f"Deleted full vehicle image: {filename}")
    except S3Error as e:
        print(f"Error deleting full vehicle image: {e}")
        raise

def upload_vehicle_plate_image(base64_image, filename: str, content_type: str) -> str:
    """
    Uploads a vehicle plate image to the designated MinIO bucket and returns the URL.
    """
    image_data = base64.b64decode(base64_image)
    image_bytes = io.BytesIO(image_data)
    try:
        # Upload plate image to MinIO
        minio_client.put_object(
            bucket_name=settings.MINIO_PLATE_IMAGE_BUCKET,
            object_name=filename,
            data=image_bytes,
            length=len(image_data),
            content_type=content_type
        )

        # Generate a pre-signed URL for accessing the image
        image_url = minio_client.presigned_get_object(
            settings.MINIO_PLATE_IMAGE_BUCKET, filename
        )
        return image_url

    except S3Error as error:
        print(f"Error uploading vehicle plate image: {error}")
        raise

def delete_vehicle_plate_image(filename: str) -> None:
    """
    Deletes a vehicle plate image from MinIO.
    """
    try:
        minio_client.remove_object(settings.MINIO_PLATE_IMAGE_BUCKET, filename)
        print(f"Deleted vehicle plate image: {filename}")
    except S3Error as e:
        print(f"Error deleting vehicle plate image: {e}")
        raise
