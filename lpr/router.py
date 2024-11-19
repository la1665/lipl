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
camera_settings_router = APIRouter(prefix="/v1")
camera_router = APIRouter(prefix="/v1")
lpr_setting_router = APIRouter(prefix="/v1")
lpr_router = APIRouter(prefix="/v1")



# Building endpoints
@building_router.post("/buildings/", response_model=BuildingInDB, status_code=status.HTTP_201_CREATED)
async def api_create_building(building: BuildingCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await BuildingOperation(db).create_building(building)

@building_router.get("/buildings/", response_model=BuildingPagination)
async def api_get_buildings(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await BuildingOperation(db).get_buildings(page, page_size)

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
@gate_router.post("/gates/", response_model=GateInDB, status_code=status.HTTP_201_CREATED)
async def api_create_gate(gate: GateCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await GateOperation(db).create_gate(gate)

@gate_router.get("/gates/", response_model=GatePagination)
async def api_get_gates(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    return await GateOperation(db).get_gates(page, page_size)

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
@camera_settings_router.post("/camera-settings/", response_model=CameraSettingInDB, status_code=status.HTTP_201_CREATED)
async def api_create_setting(setting: CameraSettingCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    return await SettingOperation(db).create_setting(setting)

@camera_settings_router.get("/camera-settings/", response_model=CameraSettingPagination)
async def api_read_settings(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    settings = await SettingOperation(db).get_settings(page, page_size)
    return settings

@camera_settings_router.get("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
async def api_read_setting(setting_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    db_setting = await SettingOperation(db).get_setting(setting_id=setting_id)
    return db_setting

@camera_settings_router.put("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
async def api_update_setting(setting_id: int, setting: CameraSettingUpdate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    db_setting = await SettingOperation(db).update_setting(setting_id, setting)
    return db_setting

@camera_settings_router.delete("/camera-settings/{setting_id}", response_model=CameraSettingInDB)
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

@camera_router.get("/cameras/", response_model=CameraPagination)
async def api_read_cameras(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_current_active_user)):
    """
    Lists all the registered cameras.
    """
    cameras = await CameraOperation(db).get_cameras(page, page_size)
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

@camera_router.put(
    "/cameras/{camera_id}/settings/{setting_id}",
    response_model=CameraSettingInstanceInDB,
)
async def api_update_camera_setting(
    camera_id: int,
    setting_id: int,
    setting_update: CameraSettingInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await CameraOperation(db).update_camera_setting(
        camera_id, setting_id, setting_update
    )

@camera_router.post(
    "/cameras/{camera_id}/settings/", response_model=CameraSettingInstanceInDB
)
async def api_add_camera_setting(
    camera_id: int,
    setting_create: CameraSettingInstanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await CameraOperation(db).add_camera_setting(camera_id, setting_create)

@camera_router.delete(
    "/cameras/{camera_id}/settings/{setting_id}",
    response_model=CameraSettingInstanceInDB,
)
async def api_remove_camera_setting(
    camera_id: int,
    setting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await CameraOperation(db).remove_camera_setting(camera_id, setting_id)


# LPR Setting endpoints
@lpr_setting_router.post("/lpr-settings/", response_model=LprSettingInDB, status_code=status.HTTP_201_CREATED)
async def api_create_lpr_setting(
    setting: LprSettingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprSettingOperation(db).create_setting(setting)


@lpr_setting_router.get("/lpr-settings/", response_model=LprSettingPagination)
async def api_get_lpr_settings(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user),
):
    return await LprSettingOperation(db).get_settings(page, page_size)


@lpr_setting_router.get("/lpr-settings/{setting_id}", response_model=LprSettingInDB)
async def api_get_lpr_setting(
    setting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user),
):
    return await LprSettingOperation(db).get_setting(setting_id)


@lpr_setting_router.put("/lpr-settings/{setting_id}", response_model=LprSettingInDB)
async def api_update_lprsetting(
    setting_id: int,
    setting: LprSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprSettingOperation(db).update_setting(setting_id, setting)

@lpr_setting_router.delete("/lpr-settings/{setting_id}", response_model=LprSettingInDB)
async def api_delete_lpr_setting(
    setting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprSettingOperation(db).delete_setting(setting_id)



#lpr endpoints
@lpr_router.post("/lprs/", response_model=LprInDB, status_code=status.HTTP_201_CREATED)
async def api_create_lpr(lpr: LprCreate, db: AsyncSession = Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).create_lpr(lpr)

@lpr_router.get("/lprs/", response_model=LprPagination)
async def api_get_lprs(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user:UserInDB=Depends(get_current_active_user)):
    return await LprOperation(db).get_lprs(page, page_size)

@lpr_router.get("/lprs/{lpr_id}", response_model=LprInDB)
async def api_read_lpr(lpr_id: int, db: AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_current_active_user)):
    return await LprOperation(db).get_lpr(lpr_id)

@lpr_router.put("/lprs/{lpr_id}", response_model=LprInDB)
async def api_update_lpr(lpr_id: int, lpr: LprUpdate, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).update_lpr(lpr_id, lpr)

@lpr_router.delete("/lprs/{lpr_id}", response_model=LprInDB)
async def api_delete_lpr(lpr_id: int, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    return await LprOperation(db).delete_lpr(lpr_id)

@lpr_router.put(
    "/lprs/{lpr_id}/settings/{setting_id}",
    response_model=LprSettingInstanceInDB,
)
async def api_update_lpr_setting(
    lpr_id: int,
    setting_id: int,
    setting_update: LprSettingInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprOperation(db).update_lpr_setting(
        lpr_id, setting_id, setting_update
    )

@lpr_router.post(
    "/lprs/{lpr_id}/settings/", response_model=LprSettingInstanceInDB
)
async def api_add_lpr_setting(
    lpr_id: int,
    setting_create: LprSettingInstanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprOperation(db).add_lpr_setting(lpr_id, setting_create)

@lpr_router.delete(
    "/lprs/{lpr_id}/settings/{setting_id}",
    response_model=LprSettingInstanceInDB,
)
async def api_remove_lpr_setting(
    lpr_id: int,
    setting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_admin_or_staff_user),
):
    return await LprOperation(db).remove_lpr_setting(lpr_id, setting_id)
