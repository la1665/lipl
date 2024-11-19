from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING

from lpr.model import GateType, SettingType
if TYPE_CHECKING:
    from lpr.schema import (
        GateInDB,
        CameraInDB,
        LprInDB,
        CameraSettingInDB,
        LprSettingInDB,
    )

class BuildingBase(BaseModel):
    name: str
    latitude: str
    longitude: str
    description: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BuildingInDB(BuildingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    gates: Optional[List["GateInDB"]] = []

    class Config:
        from_attributes = True


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
    gate_type: Optional[GateType] = None


class GateInDB(GateBase):
    id: int
    building_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    cameras: List["CameraInDB"] = []

    class Config:
        from_attributes = True


class CameraSettingInstanceBase(BaseModel):
    name: str
    description: Optional[str] = None
    value: str
    setting_type: SettingType
    is_active: bool = True


class CameraSettingInstanceCreate(CameraSettingInstanceBase):
    pass


class CameraSettingInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    setting_type: Optional[SettingType] = None
    is_active: Optional[bool] = None


class CameraSettingInstanceInDB(CameraSettingInstanceBase):
    id: int
    camera_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




class LprSettingInstanceBase(BaseModel):
    name: str
    description: Optional[str] = None
    value: str
    setting_type: SettingType
    is_active: bool = True


class LprSettingInstanceCreate(LprSettingInstanceBase):
    pass


class LprSettingInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    setting_type: Optional[SettingType] = None
    is_active: Optional[bool] = None


class LprSettingInstanceInDB(LprSettingInstanceBase):
    id: int
    lpr_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class CameraSummary(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class LprSummary(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

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

class CameraSettingInDB(CameraSettingBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    cameras: List[CameraSummary] = []

    class Config:
        from_attributes = True



class CameraBase(BaseModel):
    name: str
    latitude: str
    longitude: str
    description: str


class CameraCreate(CameraBase):
    gate_id: int
    lpr_ids: List[int] = []


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    description: Optional[str] = None
    gate_id: Optional[int] = None
    lpr_ids: Optional[List[int]] = []


class CameraInDB(CameraBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    gate_id: int
    settings: List[CameraSettingInstanceInDB] = []
    lprs: List[LprSummary] = []

    class Config:
        from_attributes = True


class LprSettingBase(BaseModel):
    name: str
    description: str
    value: str
    setting_type: SettingType = Field(default=SettingType.STRING)


class LprSettingCreate(LprSettingBase):
    pass

class LprSettingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    setting_type: Optional[SettingType] = None

class LprSettingInDB(LprSettingBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    lprs: List[LprSummary] = []

    class Config:
        from_attributes = True



class LprBase(BaseModel):
    name: str
    description: str
    ip: str
    port: int
    auth_token: str
    latitude: str
    longitude: str

class LprCreate(LprBase):
    pass


class LprUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    auth_token: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class LprInDB(LprBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: List[LprSettingInstanceInDB] = []
    cameras: List[CameraSummary] = []

    class Config:
        from_attributes = True



class BuildingPagination(BaseModel):
    items: List[BuildingInDB]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int

    class Config:
        from_attributes = True
