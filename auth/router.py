import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from settings import settings
from auth import auth, access_level
from auth.schema import Token
from db.engine import get_db

auth_router = APIRouter(prefix="/v1")

logger = logging.getLogger(__name__)

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info(f"User login attempt for username: {form_data.username}")
    user = await access_level.get_user(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        logger.error(f"Login failed: User {form_data.username} not found, or Invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
