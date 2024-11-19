import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from minio.error import S3Error

from db.engine import get_db
from user.crud import UserOperation
from user.model import UserType
from user.schema import UserInDB, UserCreate, UserUpdate
# from user.validator import validate_image_size, validate_image_extension, validate_image_content_type
from auth.access_level import (get_user,
    get_current_active_user,
    get_admin_user,
    get_admin_or_staff_user,
)
from settings import settings

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/v1")

@user_router.post("/users", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def api_create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_user)
):
    logger.info(f"Create user request for username: {user.username}")

    new_user =  await UserOperation(db).create_user(user)
    return new_user


@user_router.get("/users", response_model=List[UserInDB])
async def api_read_all_users(db: AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    return await UserOperation(db).get_all_users()

@user_router.get("/users/{user_id}")
async def api_read_user(user_id: int, db: AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    user = await UserOperation(db).get_user(user_id)
    return user

@user_router.delete("/users/{user_id}")
async def api_delete_user(user_id: int, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    logger.info(f"Delete request received for user ID: {user_id}")
    user = await UserOperation(db).delete_user(user_id)
    logger.info(f"User ID {user_id} deleted successfully")
    return user


@user_router.put("/users/{user_id}", response_model=UserInDB)
async def api_update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_user)
):
    """
    Update user details.

    Parameters:
    - user_id: ID of the user to update
    - user_update: JSON body containing fields to update
    """
    logger.info(f"Update request received for user ID: {user_id}")
    updated_user = await UserOperation(db).update_user(user_id, user_update)
    logger.info(f"User ID {user_id} updated successfully")
    return updated_user


@user_router.patch("/users/{user_id}/activate")
async def api_change_user_activation(user_id: int, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    user = await UserOperation(db).update_user_activate_status(user_id)
    return {"msg": f"User with id:{user.id} is_active status updated to {user.is_active} successfully"}


@user_router.post("/users/{user_id}/profile-image", response_model=UserInDB)
async def api_upload_profile_image(
    user_id: int,
    profile_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Upload or update the user's profile image.
    """
    logger.info(f"Profile image upload request for user ID: {user_id}")
    updated_user = await UserOperation(db).upload_profile_image(user_id, profile_image)
    logger.info(f"Profile image uploaded for user ID: {user_id}")
    return updated_user


@user_router.get("/users/{user_id}/profile-image", response_class=StreamingResponse)
async def get_profile_image(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Fetch and serve the user's profile image from MinIO.
    Accessible by all authenticated and active users.
    """
    user = await UserOperation(db).get_user(user_id)
    if not user or not user.profile_image:
        raise HTTPException(status_code=404, detail="Profile image not found.")

    try:
        response = minio_client.get_object(settings.MINIO_PROFILE_IMAGE_BUCKET, user.profile_image)
        return StreamingResponse(response, media_type="image/jpeg")  # Adjust media_type as needed
    except S3Error as e:
        print(f"Error fetching image: {e}")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Failed to fetch profile image.")
