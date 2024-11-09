import io
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
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=unique_filename,
            data=io.BytesIO(file_data),
            length=file_length,
            content_type=content_type  # Adjust based on file type
        )


        # Generate a pre-signed URL for accessing the image
        image_url = minio_client.presigned_get_object(
            settings.MINIO_BUCKET_NAME, unique_filename
        )
        return image_url

    except S3Error as error:
        print(f"Error uploading profile image: {error}")
        raise


def delete_profile_image(filename: str) -> None:
    """
    Deletes a profile image from MinIO.
    """
    try:
        minio_client.remove_object(settings.MINIO_BUCKET_NAME, filename)
        print(f"Deleted profile image: {filename}")
    except S3Error as e:
        print(f"Error deleting profile image: {e}")
        raise
