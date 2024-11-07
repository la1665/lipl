import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from auth.auth import get_password_hash
from user.model import DBUser, UserType

logger = logging.getLogger(__name__)

async def create_default_admin(session: AsyncSession):
    pass
    logger.info("Checking if default admin user exists")
    result = await session.execute(select(DBUser).filter(DBUser.username == settings.ADMIN_USERNAME))
    admin = result.unique().scalars().first()

    if admin:
        logger.info("Default admin user already exists")
        print("Admin user already exists.")
        return

    try:
        # If no admin exists, create one with secure credentials
        admin_user = DBUser(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            user_type=UserType.ADMIN,
            is_active=True
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        logger.info("Default admin user created successfully")
        print("Default admin user created successfully.")
        print(f"Admin: {admin_user.username}")


    except SQLAlchemyError as error:
        await session.rollback()
        logger.critical(f"Failed to creat default admin user: {error}")
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create user")
