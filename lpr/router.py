from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.engine import get_db
from lpr.schema import *
from lpr.crud import *
from auth.access_level import get_admin_or_staff_user, get_current_active_user
from user.schema import UserInDB


building_router = APIRouter(prefix="/v1")
gate_router = APIRouter(prefix="/v1")
settings_router = APIRouter(prefix="/v1")
camera_router = APIRouter(prefix="/v1")
lpr_router = APIRouter(prefix="/v1")
client_router = APIRouter(prefix="/v1")



# Building endpoints
@building_router.post("/buildings/", response_model=BuildingInDB, status_code=status.HTTP_201_CREATED)
async def api_create_building(building: BuildingCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await BuildingOperation(db).create_building(building)

@building_router.get("/buildings/", response_model=List[BuildingInDB])
async def api_get_buildings(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await BuildingOperation(db).get_buildings(skip, limit)

@building_router.get("/buildings/{building_id}", response_model=BuildingInDB)
async def api_get_building(building_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await BuildingOperation(db).get_building(building_id)


@building_router.put("/buildings/{building_id}", response_model=BuildingInDB)
async def api_update_building(building_id: int, building: BuildingUpdate, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await BuildingOperation(db).update_building(building_id, building)


@building_router.delete("/buildings/{building_id}", response_model=BuildingInDB)
async def api_delete_building(building_id: int, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await BuildingOperation(db).delete_building(building_id)


# Gate endpoints
@gate_router.post("/gates/", response_model=GateInDB)
async def api_create_gate(gate: GateCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await GateOperation(db).create_gate(gate)

@gate_router.get("/gates/", response_model=List[GateInDB])
async def api_get_gates(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await GateOperation(db).get_gates(skip, limit)

@gate_router.get("/gates/{gate_id}", response_model=GateInDB)
async def api_get_gate(gate_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await GateOperation(db).get_gate(gate_id)


@gate_router.put("/gates/{gate_id}", response_model=GateInDB)
async def api_update_gate(gate_id: int, gate: GateUpdate, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await GateOperation(db).update_gate(gate_id, gate)


@gate_router.delete("/gates/{gate_id}", response_model=GateInDB)
async def api_delete_gate(gate_id: int, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await GateOperation(db).delete_gate(gate_id)


# camera setting endpoints
@settings_router.post("/camera-settings/", response_model=CameraSettingInDB)
async def api_create_setting(setting: CameraSettingCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await SettingOperation(db).create_setting(setting)

@settings_router.get("/camera-settings/", response_model=List[CameraSettingInDB])
async def api_read_settings(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    settings = await SettingOperation(db).get_settings(skip=skip, limit=limit)
    return settings

@settings_router.get("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
async def api_read_setting(setting_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    db_setting = await SettingOperation(db).get_setting(setting_id=setting_id)
    return db_setting

@settings_router.put("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
async def api_update_setting(setting_id: int, setting: CameraSettingUpdate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    db_setting = await SettingOperation(db).update_setting(setting_id, setting)
    return db_setting

@settings_router.delete("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
async def api_delete_setting(setting_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    db_setting = await SettingOperation(db).delete_setting(setting_id)
    return db_setting


#camera endpoints
@camera_router.post("/cameras/", response_model=CameraInDB)
async def api_create_camera(camera: CameraCreate, db: AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    """
    Adds a new camera and establishes a TCP connection.
    """
    return await CameraOperation(db).create_camera(camera)

@camera_router.get("/cameras/", response_model=List[CameraInDB])
async def api_read_cameras(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    """
    Lists all the registered cameras.
    """
    cameras = await CameraOperation(db).get_cameras(skip=skip, limit=limit)
    return cameras

@camera_router.get("/cameras/{camera_id}", response_model=CameraInDB)
async def api_read_camera(camera_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    db_camera = await CameraOperation(db).get_camera(camera_id=camera_id)
    return db_camera


@camera_router.put("/cameras/{camera_id}", response_model=CameraInDB)
async def api_update_camera(camera_id: int, camera: CameraUpdate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    db_camera = await CameraOperation(db).update_camera(camera_id, camera)
    return db_camera

@camera_router.delete("/cameras/{camera_id}", response_model=CameraInDB)
async def api_delete_camera(camera_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    db_camera = await CameraOperation(db).delete_camera(camera_id)
    return db_camera


#lpr endpoints
@lpr_router.post("/lprs/", response_model=LPRInDB)
async def api_create_lpr(lpr: LPRCreate, db: AsyncSession = Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).create_lpr(lpr)

@lpr_router.get("/lprs/", response_model=List[LPRInDB])
async def api_get_lprs(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), current_user:UserInDB=Depends(get_current_active_user)):
    return await LprOperation(db).get_lprs(skip, limit)

@lpr_router.get("/lprs/{lpr_id}", response_model=LPRInDB)
async def api_read_lpr(lpr_id: int, db: AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_current_active_user)):
    return await LprOperation(db).get_lpr(lpr_id)

@lpr_router.put("/lprs/{lpr_id}", response_model=LPRInDB)
async def api_update_lpr(lpr_id: int, lpr: LPRUpdate, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).update_lpr(lpr_id, lpr)

@lpr_router.delete("/lprs/{lpr_id}", response_model=LPRInDB)
async def api_delete_lpr(lpr_id: int, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).delete_lpr(lpr_id)


#client endpoints
@client_router.post("/clients/", response_model=ClientInDB, dependencies=[Depends(get_admin_or_staff_user)], status_code=status.HTTP_201_CREATED)
async def api_create_client(client: ClientCreate, db: AsyncSession = Depends(get_db)):
    return await ClientOperation(db).create_client(client)
