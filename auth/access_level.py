from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

from settings import settings
from db.engine import get_db
from auth.auth import oauth2_scheme
from auth.schema import TokenData
from user.schema import UserInDB
from user.model import DBUser, UserType



async def get_user(db: AsyncSession, username: str|None):
    result = await db.execute(select(DBUser).filter(DBUser.username == username))
    user = result.unique().scalars().first()
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                detail="Authorization Error: Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"})
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authorization Error: Could not validate credentials",
         headers={"WWW-Authenticate": "Bearer"})
    current_user = await get_user(db, username=token_data.username)
    if current_user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authorization Error: Could not validate credentials",
         headers={"WWW-Authenticate": "Bearer"})
    return current_user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive user."
        )
    return current_user


async def get_admin_user(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.user_type is not UserType.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
            "You don't have enough permissions to perform this action."
        )
    return current_user


async def get_admin_or_staff_user(current_user: DBUser = Depends(get_current_active_user)):
    if current_user.user_type not in [UserType.ADMIN, UserType.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user
