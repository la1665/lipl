import logging
from fastapi import HTTPException,UploadFile, status
from sqlalchemy import Sequence, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from user.model import DBUser, UserType
from user.schema import UserBase, UserCreate, UserUpdate, UserInDB
from user.validator import validate_image_size, validate_image_extension, validate_image_content_type
from auth.access_level import get_user
from auth.auth import get_password_hash
from utils.minio_utils import upload_profile_image, delete_profile_image

logger = logging.getLogger(__name__)

class UserOperation:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    def _validate_and_upload_image(self, profile_image: UploadFile, user: DBUser):
        """
        Validates and uploads the profile image to MinIO.
        """
        # Validate the image with provided validators
        validate_image_extension(profile_image.filename)
        validate_image_content_type(profile_image.content_type)
        validate_image_size(profile_image)

        # Read the file data and upload to MinIO
        file_data = profile_image.file.read()
        image_url = upload_profile_image(file_data, user.id, profile_image.filename, profile_image.content_type)
        user.profile_image = image_url

    async def get_all_users(self):
        logger.info("Fetching all users")
        async with self.db_session as session:
            result = await session.execute(
                select(DBUser)
            )
            users = result.unique().scalars().all()
            logger.info(f"Retrieved all users data")
            return users

    async def get_user(self, user_id: int):
        logger.info(f"Fetching user with ID: {user_id}")
        async with self.db_session as session:
            result = await session.execute(
                select(DBUser).where(DBUser.id==user_id)
            )
            user = result.unique().scalar_one_or_none()
            if user is None:
                logger.error(f"User with ID {user_id} not found")
                raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found!")
            logger.info(f"Retrieved user data: {user}")
            return user

    async def create_user(self, user: UserCreate) -> DBUser:
        logger.info("Attempting to create a new user")
        hashed_password = get_password_hash(user.password)
        async with self.db_session as session:
            query = await session.execute(
                select(DBUser).where(
                    or_(DBUser.username == user.username, DBUser.email == user.email)
                ))
            db_user = query.unique().scalar_one_or_none()
            if db_user:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "username/email already exists.")

            try:
                new_user = DBUser(
                    username=user.username,
                    email=user.email,
                    user_type=user.user_type,
                    hashed_password=hashed_password
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                logger.info(f"User created successfully with ID: {new_user.id}")
                return new_user
            except SQLAlchemyError as error:
                await session.rollback()
                logger.error(f"Failed to create user: {error}")
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create user")



    async def update_user(self, user_id: int, user_update: UserUpdate):
        async with self.db_session as session:
            db_user = await self.get_user(user_id)
            try:
                db_user = session.merge(db_user)
                for key, value in user_update.dict(exclude_unset=True).items():
                    setattr(db_user, key, value)

                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                return db_user
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user {user_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update user."
                )


    async def delete_user(self, user_id: int):
        async with self.db_session as session:
            db_user = await self.get_user(user_id)
            try:
                db_user = session.merge(db_user)
                await session.delete(db_user)
                await session.commit()
                return db_user
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Could not delete user")

    async def update_user_activate_status(self, user_id:int):
        async with self.db_session as session:
            user = await self.get_user(user_id)
            if user.user_type not in [UserType.USER, UserType.VIEWER]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only change the is_active status of users with the 'user, viewer' role"
                    )

            user.is_active = not user.is_active

            try:
                await session.commit()
                await session.refresh(user)
                return user
            except:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not update user status")


    async def upload_profile_image(self, user_id: int, profile_image: UploadFile):

            user = await self.get_user(user_id)
            # Validate the image
            validate_image_extension(profile_image.filename)
            validate_image_content_type(profile_image.content_type)
            validate_image_size(profile_image)

            # Read the file data
            file_data = await profile_image.read()

            # Delete old profile image if exists
            # if user.profile_image:
            #     old_filename = user.profile_image.split("/")[-1].split("?")[0]
            #     delete_profile_image(old_filename)

            # Upload new profile image
            image_url = upload_profile_image(file_data, user.id, profile_image.filename, profile_image.content_type)
            user.profile_image = image_url

            try:
                async with self.db_session as session:
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                return user
            except SQLAlchemyError as error:
                await self.db_session.rollback()
                logger.error(f"Failed to upload profile image for user {user_id}: {error}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to upload profile image."
                )
