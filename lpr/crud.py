import math
import logging
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from lpr.model import DBBuilding, DBGate, DBCameraSetting, DBCamera, DBLpr, DBLprSetting, DBLprSettingInstance, DBCameraSettingInstance
from lpr.schema import (
    BuildingCreate,
    BuildingUpdate,
    GateCreate,
    GateUpdate,
    CameraCreate,
    CameraUpdate,
    CameraSettingInstanceCreate,
    CameraSettingInstanceUpdate,
    LprCreate,
    LprUpdate,
    CameraSettingCreate,
    CameraSettingUpdate,
    LprSettingCreate,
    LprSettingUpdate,
    LprSettingInstanceCreate,
    LprSettingInstanceUpdate,
)
from tcp.tcp_client import connect_to_server
from tcp.manager import connection_manager


logger = logging.getLogger(__name__)



class CrudOperation:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session


class BuildingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_building(self, building_id: int):
        async with self.db_session as session:
            query = await session.execute(
                    select(DBBuilding)
                    .where(DBBuilding.id == building_id)
                )
            building = query.unique().scalar_one_or_none()
            if building is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
            return building

    async def get_buildings(self, page: int = 1, page_size: int = 10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBBuilding.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBBuilding).offset(offset).limit(page_size)
            )
            buildings = query.unique().scalars().all()

            return {
                "items": buildings,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }


    async def create_building(self, building):
        async with self.db_session as session:
            try:
                new_building = DBBuilding(
                    name=building.name,
                    latitude=building.latitude,
                    longitude=building.longitude,
                    description=building.description
                )
                session.add(new_building)
                await session.commit()
                await session.refresh(new_building)
                return new_building
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_building(self, building_id: int, building):
        async with self.db_session as session:
            db_building = await self.get_building(building_id)
            try:
                db_building = await session.merge(db_building)
                for key, value in building.dict(exclude_unset=True).items():
                    setattr(db_building, key, value)
                await session.commit()
                await session.refresh(db_building)
                return db_building
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    async def delete_building(self, building_id: int):
        async with self.db_session as session:
            db_building = await self.get_building(building_id)
            try:
                db_building = await session.merge(db_building)
                await session.delete(db_building)
                await session.commit()
                return db_building
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))



class GateOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_gate(self, gate_id: int):
        async with self.db_session as session:
            # session = self.db_session
            query = await session.execute(select(DBGate)
                .where(DBGate.id == gate_id)
            )
            db_gate =  query.unique().scalar_one_or_none()
            if db_gate is None:
                raise HTTPException(status_code=404, detail="gate not found")
            return db_gate

    async def get_gates(self, page: int = 1, page_size: int = 10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBGate.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBGate).offset(offset).limit(page_size)
            )
            gates = query.unique().scalars().all()
            return {
                "items": gates,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }

    async def create_gate(self, gate):
        async with self.db_session as session:
            db_building = await BuildingOperation(session).get_building(gate.building_id)
            try:
                db_building = await session.merge(db_building)
                new_gate = DBGate(name=gate.name,
                    gate_type=gate.gate_type,
                    description=gate.description,
                    building_id=db_building.id)
                session.add(new_gate)
                await session.commit()
                await session.refresh(new_gate)
                # result = await session.execute(
                #         select(DBGate)
                #         .where(DBGate.id == new_gate.id)
                #     )
                # new_gate = result.scalars().first()
                return new_gate
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def update_gate(self, gate_id: int, gate):
        async with self.db_session as session:
            db_gate = await self.get_gate(gate_id)
            try:
                db_gate = await session.merge(db_gate)
                update_data = gate.dict(exclude_unset=True)
                if "building_id" in update_data:
                    building_id = update_data["building_id"]
                    await BuildingOperation(session).get_building(building_id)

                for key, value in update_data.items():
                    setattr(db_gate, key, value)
                await session.commit()
                await session.refresh(db_gate)
                return db_gate
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def delete_gate(self, gate_id: int):
        async with self.db_session as session:
            db_gate = await self.get_gate(gate_id)
            try:
                db_gate = await session.merge(db_gate)
                await session.delete(db_gate)
                await session.commit()
                return db_gate
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))


class SettingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_setting(self, setting_id: int):
        async with self.db_session as session:
            query = await session.execute(
                select(DBCameraSetting).where(DBCameraSetting.id==setting_id)
            )
            setting =  query.unique().scalar_one_or_none()
            if setting is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
            return setting

    async def get_setting_by_name(self, name: str):
        async with self.db_session as session:
            query = await session.execute(select(DBCameraSetting).where(DBCameraSetting.name == name))
            setting = query.unique().scalar_one_or_none()
            return setting

    async def get_settings(self, page: int=1, page_size: int=10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBCameraSetting.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBCameraSetting).offset(offset).limit(page_size)
            )
            settings = query.unique().scalars().all()
            return {
                "items": settings,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }

    async def create_setting(self, setting):
        async with self.db_session as session:
            try:
                new_setting = DBCameraSetting(
                name=setting.name,
                description=setting.description,
                value=setting.value,
                setting_type=setting.setting_type
                )
                session.add(new_setting)
                await session.commit()
                await session.refresh(new_setting)
                # result = await session.execute(
                #         select(DBCameraSetting)
                #         .where(DBCameraSetting.id == new_setting.id)
                #     )
                # new_setting = result.scalars().first()
                return new_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create setting")

    async def update_setting(self, setting_id: int, setting: CameraSettingUpdate):
        async with self.db_session as session:
            db_setting = await self.get_setting(setting_id)
            try:
                db_setting = await session.merge(db_setting)
                update_data = setting.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_setting, key, value)
                await session.commit()
                await session.refresh(db_setting)
                return db_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update setting")

    async def delete_setting(self, setting_id: int):
        async with self.db_session as session:
            db_setting = await self.get_setting(setting_id)
            try:
                db_setting = await session.merge(db_setting)
                await session.delete(db_setting)
                await session.commit()
                return db_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete setting")


class CameraOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_camera(self, camera_id: int):
        async with self.db_session as session:
            result = await session.execute(select(DBCamera)
                .where(DBCamera.id==camera_id)
            )
            camera =  result.unique().scalar_one_or_none()
            if camera is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Camera not found")
            return camera

    async def get_cameras(self, page: int=1, page_size: int=10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBCamera.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBCamera).offset(offset).limit(page_size)
            )
            cameras = query.unique().scalars().all()
            return {
                "items": cameras,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }

    async def create_camera(self, camera: CameraCreate):
        async with self.db_session as session:
            # session = self.db_session
            db_gate = await GateOperation(session).get_gate(camera.gate_id)
            try:
                db_gate = await session.merge(db_gate)
                # if camera.setting_ids:
                #     result = await session.execute(select(DBCameraSetting).where(DBCameraSetting.id.in_(camera.setting_ids)))
                #     settings = result.scalars().all()
                #     if len(settings) != len(camera.setting_ids):
                #         raise HTTPException(status_code=404, detail="One or more settings not found")


                db_camera = DBCamera(
                    name=camera.name,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    description=camera.description,
                    gate_id=camera.gate_id
                )
                session.add(db_camera)
                await session.commit()
                await session.flush()

                result = await session.execute(select(DBCameraSetting))
                default_settings = result.scalars().all()
                for setting in default_settings:
                    setting_instance = DBCameraSettingInstance(
                        camera_id=db_camera.id,
                        name=setting.name,
                        description=setting.description,
                        value=setting.value,
                        setting_type=setting.setting_type,
                        is_active=setting.is_active,
                        default_setting_id=setting.id
                    )
                    session.add(setting_instance)
                await session.commit()
                logger.critical(f"created camera with settings to create camera{db_camera.id}")

                if camera.lpr_ids:
                    logger.critical(f"lpr ids are: {camera.lpr_ids}")
                    query = await session.execute(select(DBLpr)
                        .where(DBLpr.id.in_(camera.lpr_ids))
                    )
                    lprs =  query.unique().scalars().all()
                    logger.critical(f"found lprs are: {[lpr.name for lpr in lprs]}")
                    if len(lprs) != len(camera.lpr_ids):
                        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="One or more LPRs not found")
                    db_camera.lprs.extend(lprs)
                    await session.commit()

                # await session.commit()
                await session.refresh(db_camera)
                return db_camera

            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create camera")

    async def update_camera(self, camera_id: int, camera: CameraUpdate):
        async with self.db_session as session:
            db_camera = await self.get_camera(camera_id)

            try:
                db_camera = await session.merge(db_camera)
                update_data = camera.dict(exclude_unset=True)
                if "gate_id" in update_data:
                    gate_id = update_data["gate_id"]
                    await GateOperation(session).get_gate(gate_id)
                    db_camera.gate_id = gate_id

                if "lpr_ids" in update_data:
                    result = await session.execute(
                        select(DBLpr).where(DBLpr.id.in_(update_data["lpr_ids"]))
                    )
                    lprs = result.unique().scalars().all()
                    if len(lprs) != len(update_data["lpr_ids"]):
                        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="One or more LPRs not found")
                    db_camera.lprs = lprs

                for key, value in update_data.items():
                    if key not in ["gate_id", "lpr_ids"]:
                        setattr(db_camera, key, value)

                await session.commit()
                await session.refresh(db_camera)
                return db_camera
            except SQLAlchemyError as error:
                    await session.rollback()
                    raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update camera")

    async def update_camera_setting(
            self, camera_id: int, setting_id: int, setting_update: CameraSettingInstanceUpdate
        ):
            async with self.db_session as session:
                # Fetch the setting instance
                query = await session.execute(
                    select(DBCameraSettingInstance)
                    .where(
                        DBCameraSettingInstance.camera_id == camera_id,
                        DBCameraSettingInstance.id == setting_id
                    )
                )
                setting_instance = query.scalar_one_or_none()
                if setting_instance is None:
                    raise HTTPException(
                        status_code=404, detail="Setting not found for this camera"
                    )

                try:
                    update_data = setting_update.dict(exclude_unset=True)
                    for key, value in update_data.items():
                        setattr(setting_instance, key, value)
                    await session.commit()
                    await session.refresh(setting_instance)
                    return setting_instance
                except SQLAlchemyError as error:
                    await session.rollback()
                    raise HTTPException(
                        status.HTTP_409_CONFLICT, f"{error}: Could not update camera setting"
                    )

    async def add_camera_setting(
        self, camera_id: int, setting_create: CameraSettingInstanceCreate
    ):
        async with self.db_session as session:
            # Check if setting with the same name already exists for this camera
            exists_query = await session.execute(
                select(DBCameraSettingInstance)
                .where(
                    DBCameraSettingInstance.camera_id == camera_id,
                    DBCameraSettingInstance.name == setting_create.name
                )
            )
            if exists_query.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail="Setting with this name already exists for this camera"
                )

            try:
                # Optionally, check if a default setting exists with this name
                default_setting_query = await session.execute(
                    select(DBCameraSetting).where(DBCameraSetting.name == setting_create.name)
                )
                default_setting = default_setting_query.scalar_one_or_none()

                setting_instance = DBCameraSettingInstance(
                    camera_id=camera_id,
                    name=setting_create.name,
                    description=setting_create.description,
                    value=setting_create.value,
                    setting_type=setting_create.setting_type,
                    default_setting_id=default_setting.id if default_setting else None
                )
                session.add(setting_instance)
                await session.commit()
                await session.refresh(setting_instance)
                return setting_instance
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT, f"{error}: Could not add camera setting"
                )

    async def remove_camera_setting(self, camera_id: int, setting_id: int):
        async with self.db_session as session:
            # Fetch the setting instance
            query = await session.execute(
                select(DBCameraSettingInstance)
                .where(
                    DBCameraSettingInstance.camera_id == camera_id,
                    DBCameraSettingInstance.id == setting_id
                )
            )
            setting_instance = query.scalar_one_or_none()
            if setting_instance is None:
                raise HTTPException(
                    status_code=404, detail="Setting not found for this camera"
                )

            try:
                await session.delete(setting_instance)
                await session.commit()
                return setting_instance
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT, f"{error}: Could not remove camera setting"
                )

    async def delete_camera(self, camera_id: int):
        async with self.db_session as session:
            db_camera = await self.get_camera(camera_id)
            try:

                await session.delete(db_camera)
                await session.commit()
                return db_camera

            except SQLAlchemyError as error:
                    await session.rollback()
                    raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete camera")


class LprSettingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_setting(self, setting_id: int):
        async with self.db_session as session:
            query = await session.execute(
                select(DBLprSetting).where(DBLprSetting.id == setting_id)
            )
            setting = query.unique().scalar_one_or_none()
            if setting is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LPR setting not found")
            return setting

    async def get_setting_by_name(self, name: str):
        async with self.db_session as session:
            query = await session.execute(select(DBLprSetting).where(DBLprSetting.name == name))
            setting = query.unique().scalar_one_or_none()
            return setting

    async def get_settings(self, page: int=1, page_size: int=10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBLprSetting.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBLprSetting).offset(offset).limit(page_size)
            )
            settings = query.unique().scalars().all()
            return {
                "items": settings,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }

    async def create_setting(self, setting):
        async with self.db_session as session:
            try:
                new_setting = DBLprSetting(
                name=setting.name,
                description=setting.description,
                value=setting.value,
                setting_type=setting.setting_type
                )
                session.add(new_setting)
                await session.commit()
                await session.refresh(new_setting)
                # result = await session.execute(
                #         select(DBLprSetting)
                #         .where(DBLprSetting.id == new_setting.id)
                #     )
                # new_setting = result.scalars().first()
                return new_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create setting")

    async def update_setting(self, setting_id: int, setting):
        async with self.db_session as session:
            db_setting = await self.get_setting(setting_id)
            try:
                db_setting = await session.merge(db_setting)
                update_data = setting.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_setting, key, value)
                await session.commit()
                await session.refresh(db_setting)
                return db_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update setting")

    async def delete_setting(self, setting_id: int):
        async with self.db_session as session:
            db_setting = await self.get_setting(setting_id)
            try:
                db_setting = await session.merge(db_setting)
                await session.delete(db_setting)
                await session.commit()
                return db_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete setting")


class LprOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)
        self.session = db_session

    async def get_lpr(self, lpr_id: int):
        async with self.db_session as session:
            query = await session.execute(
                select(DBLpr).where(DBLpr.id == lpr_id)
            )
            lpr = query.unique().scalar_one_or_none()
            if lpr is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LPR not found")
            return lpr

    async def get_lpr_by_name(self, name: str):
        async with self.db_session as session:
            query = await session.execute(select(DBLpr).where(DBLpr.name == name))
            lpr = query.unique().scalar_one_or_none()
            if lpr is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LPR not found")
            return lpr

    async def get_lprs(self, page: int = 1, page_size: int = 10):
        async with self.db_session as session:
            # Calculate total number of records
            total_query = await session.execute(select(func.count(DBLpr.id)))
            total_records = total_query.scalar_one()

            # Calculate total number of pages
            total_pages = math.ceil(total_records / page_size) if page_size else 1

            # Calculate offset
            offset = (page - 1) * page_size

            # Fetch the records
            query = await session.execute(
                select(DBLpr).offset(offset).limit(page_size)
            )
            lprs = query.unique().scalars().all()
            return {
                "items": lprs,
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
            }

    async def create_lpr(self, lpr):
        async with self.db_session as session:
            try:
                new_lpr = DBLpr(
                    name=lpr.name,
                    ip=lpr.ip,
                    port=lpr.port,
                    auth_token=lpr.auth_token,
                    latitude=lpr.latitude,
                    longitude=lpr.longitude,
                    description=lpr.description
                )
                session.add(new_lpr)
                await session.flush()

                result = await session.execute(select(DBLprSetting))
                default_settings = result.scalars().all()
                for setting in default_settings:
                    setting_instance = DBLprSettingInstance(
                        lpr_id=new_lpr.id,
                        name=setting.name,
                        description=setting.description,
                        value=setting.value,
                        setting_type=setting.setting_type,
                        default_setting_id=setting.id
                    )
                    session.add(setting_instance)
                await session.commit()
                await session.refresh(new_lpr)
                return new_lpr

            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def update_lpr(self, lpr_id: int, lpr):
        async with self.db_session as session:
            db_lpr = await self.get_lpr(lpr_id)
            update_data = lpr.dict(exclude_unset=True)
            try:
                db_lpr = await session.merge(db_lpr)
                for key, value in lpr.dict(exclude_unset=True).items():
                    setattr(db_lpr, key, value)

                await session.commit()
                await session.refresh(db_lpr)
                return db_lpr
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def update_lpr_setting(
            self, lpr_id: int, setting_id: int, setting_update: LprSettingInstanceUpdate
        ):
            async with self.db_session as session:
                # Fetch the setting instance
                query = await session.execute(
                    select(DBLprSettingInstance)
                    .where(
                        DBLprSettingInstance.lpr_id == lpr_id,
                        DBLprSettingInstance.id == setting_id
                    )
                )
                setting_instance = query.scalar_one_or_none()
                if setting_instance is None:
                    raise HTTPException(
                        status_code=404, detail="Setting not found for this lpr"
                    )

                try:
                    update_data = setting_update.dict(exclude_unset=True)
                    for key, value in update_data.items():
                        setattr(setting_instance, key, value)
                    await session.commit()
                    await session.refresh(setting_instance)
                    return setting_instance
                except SQLAlchemyError as error:
                    await session.rollback()
                    raise HTTPException(
                        status.HTTP_409_CONFLICT, f"{error}: Could not update lpr setting"
                    )

    async def add_lpr_setting(
        self, lpr_id: int, setting_create: LprSettingInstanceCreate
    ):
        async with self.db_session as session:
            # Check if setting with the same name already exists for this camera
            exists_query = await session.execute(
                select(DBLprSettingInstance)
                .where(
                    DBLprSettingInstance.lpr_id == lpr_id,
                    DBLprSettingInstance.name == setting_create.name
                )
            )
            if exists_query.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail="Setting with this name already exists for this lpr"
                )

            try:
                # Optionally, check if a default setting exists with this name
                default_setting_query = await session.execute(
                    select(DBLprSetting).where(DBLprSetting.name == setting_create.name)
                )
                default_setting = default_setting_query.scalar_one_or_none()

                setting_instance = DBLprSettingInstance(
                    lpr_id=lpr_id,
                    name=setting_create.name,
                    description=setting_create.description,
                    value=setting_create.value,
                    setting_type=setting_create.setting_type,
                    is_active=setting_create.is_active,
                    default_setting_id=default_setting.id if default_setting else None
                )
                session.add(setting_instance)
                await session.commit()
                await session.refresh(setting_instance)
                return setting_instance
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT, f"{error}: Could not add lpr setting"
                )

    async def remove_lpr_setting(self, lpr_id: int, setting_id: int):
        async with self.db_session as session:
            # Fetch the setting instance
            query = await session.execute(
                select(DBLprSettingInstance)
                .where(
                    DBLprSettingInstance.lpr_id == lpr_id,
                    DBLprSettingInstance.id == setting_id
                )
            )
            setting_instance = query.scalar_one_or_none()
            if setting_instance is None:
                raise HTTPException(
                    status_code=404, detail="Setting not found for this lpr"
                )

            try:
                await session.delete(setting_instance)
                await session.commit()
                return setting_instance
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT, f"{error}: Could not remove lpr setting"
                )

    async def delete_lpr(self, lpr_id: int):
        async with self.db_session as session:
            db_lpr = await self.get_lpr(lpr_id)
            try:
                await session.delete(db_lpr)
                await session.commit()
                return db_lpr
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))
