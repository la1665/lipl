from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

from lpr.model import GateType, SettingType


class BuildingBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class GateBase(BaseModel):
    name: str
    description: Optional[str] = None
    gate_type: GateType = Field(default=GateType.BOTH)

class GateCreate(GateBase):
    building_id: int

class GateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    building_id: Optional[int] = None

class CameraSettingBase(BaseModel):
    name: str
    description: str
    value: str
    setting_type: SettingType = Field(default=SettingType.STRING)

class CameraSettingCreate(CameraSettingBase):
    pass


class CameraSettingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    setting_type: Optional[SettingType] = None

class CameraBase(BaseModel):
    name: str
    location: str
    latitude: str
    longitude: str


class CameraCreate(CameraBase):
    gate_id: int
    settings: List[int] = []


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    gate_id: Optional[int] = None

class LPRBase(BaseModel):
    name: str
    description: str
    value: str
    lpr_type: SettingType = Field(default=SettingType.STRING)

class LPRCreate(LPRBase):
    pass

class LPRUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    lpr_type: Optional[SettingType] = None



class ClientBase(BaseModel):
    ip: str
    port: int
    auth_token: str

class ClientCreate(ClientBase):
    lpr_id: int
    camera_ids: List[int] = []


class CameraSettingInDB(CameraSettingBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class CameraInDB(CameraBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    gate_id: int
    settings: List[CameraSettingInDB] = []

    class Config:
        from_attributes = True

class GateInDB(GateBase):
    id: int
    building_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    cameras: List[CameraInDB] = []

    class Config:
        from_attributes = True


class BuildingInDB(BuildingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    gates: Optional[List[GateInDB]] = []

    class Config:
        from_attributes = True


class LPRInDB(LPRBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    clients: List['ClientInDB'] = []

    class Config:
        from_attributes = True



class ClientInDB(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    lpr_id: int
    # lprs: List[LPRInDB] = []
    cameras: List[CameraInDB] = []
