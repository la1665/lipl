from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

from user.model import UserType


class UserBase(BaseModel):
    username: str
    email: EmailStr
    user_type: UserType = Field(default=UserType.USER)


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    national_id: Optional[str] = None
    personal_number: Optional[str] = None
    office: Optional[str] = None
    phone_number: Optional[str] = None
    user_type: Optional[UserType] = None
    is_active: Optional[bool] = None
    profile_image: Optional[str] = None

class UserInDB(UserBase):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id_number: Optional[str] = None
    personal_number: Optional[str] = None
    phone_number: Optional[str] = None
    office: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
