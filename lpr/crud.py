from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from lpr.model import DBBuilding, DBGate, DBCameraSetting, DBCamera, DBLpr, DBClient
from lpr.schema import CameraCreate, CameraSettingCreate, CameraSettingUpdate, CameraUpdate


class CrudOperation:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session


class BuildingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def get_building(self, building_id: int):
        async with self.db_session as session:
            query = await session.execute(
                    select(DBBuilding)
                    .where(DBBuilding.id == building_id)
                    .options(selectinload(DBBuilding.gates))
                )
            building = query.unique().scalars().first()
            if building is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
            return building

    async def get_buildings(self, skip: int = 0, limit: int = 10):
        async with self.db_session as session:
            query = await session.execute(select(DBBuilding)
                .options(selectinload(DBBuilding.gates).selectinload(DBGate.cameras))
                .offset(skip)
                .limit(limit))
            return query.unique().scalars().all()

    async def create_building(self, building):
        async with self.db_session as session:
            try:
                new_building = DBBuilding(
                    name=building.name,
                    location=building.location,
                    description=building.description
                )
                session.add(new_building)
                await session.commit()
                await session.refresh(new_building)
                result = await session.execute(
                        select(DBBuilding)
                        .where(DBBuilding.id == new_building.id)
                        .options(selectinload(DBBuilding.gates))
                    )
                new_building = result.scalars().first()
                return new_building
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_building(self, building_id: int, building):
        async with self.db_session as session:
            db_building = await self.get_building(building_id)
            try:
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
                await session.delete(db_building)
                await session.commit()
                return db_building
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))



class GateOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def get_gate(self, gate_id: int):
        async with self.db_session as session:
            query = await session.execute(select(DBGate)
                .where(DBGate.id == gate_id)
                .options(selectinload(DBGate.cameras))
            )
            db_gate =  query.unique().scalars().first()
            if db_gate is None:
                raise HTTPException(status_code=404, detail="gate not found")
            return db_gate

    async def get_gates(self, skip: int = 0, limit: int = 10):
        async with self.db_session as session:
            query = await session.execute(select(DBGate)
                .offset(skip).limit(limit)
                .options(selectinload(DBGate.cameras))
            )
            return query.unique().scalars().all()

    async def create_gate(self, gate):
        async with self.db_session as session:
            db_building = await BuildingOperation(session).get_building(gate.building_id)
            try:
                new_gate = DBGate(name=gate.name,
                    gate_type=gate.gate_type,
                    description=gate.description,
                    building_id=db_building.id)
                session.add(new_gate)
                await session.commit()
                await session.refresh(new_gate)
                result = await session.execute(
                        select(DBGate)
                        .where(DBGate.id == new_gate.id)
                        .options(selectinload(DBGate.cameras))
                    )
                new_gate = result.scalars().first()
                return new_gate
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def update_gate(self, gate_id: int, gate):
        async with self.db_session as session:
            db_gate = await self.get_gate(gate_id)
            try:
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
                await session.delete(db_gate)
                await session.commit()
                return db_gate
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))


class SettingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def get_setting(self, setting_id: int):
        async with self.db_session as session:
            query = await session.execute(
                select(DBCameraSetting).where(DBCameraSetting.id==setting_id)
                .options(selectinload(DBCameraSetting.cameras))
            )
            setting =  query.unique().scalars().first()
            if setting is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
            return setting

    async def get_settings(self, skip: int=0, limit: int=10):
        async with self.db_session as session:
            query = await session.execute(select(DBCameraSetting)
                .offset(skip).limit(limit)
                .options(selectinload(DBCameraSetting.cameras))
            )
            return query.unique().scalars().all()

    async def create_setting(self, setting: CameraSettingCreate):
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
                result = await session.execute(
                        select(DBCameraSetting)
                        .where(DBCameraSetting.id == new_setting.id)
                        .options(selectinload(DBCameraSetting.cameras))
                    )
                new_setting = result.scalars().first()
                return new_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create setting")

    async def update_setting(self, setting_id: int, setting: CameraSettingUpdate):
        async with self.db_session as session:
            db_setting = await self.get_setting(setting_id)
            update_data = setting.dict(exclude_unset=True)
            try:
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
                await session.delete(db_setting)
                await session.commit()
                return db_setting
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete setting")


class CameraOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def get_camera(self, camera_id: int):
        async with self.db_session as session:
            result = await session.execute(select(DBCamera)
                .where(DBCamera.id==camera_id)
                .options(selectinload(DBCamera.settings))
            )
            camera =  result.unique().scalars().first()
            if camera is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Building not found")
            return camera

    async def get_cameras(self, skip: int=0, limit: int=10):
        async with self.db_session as session:
            cameras = await session.execute(
                select(DBCamera)
                .options(selectinload(DBCamera.settings))
                .offset(skip).limit(limit)
            )
            return cameras.unique().scalars().all()

    async def create_camera(self, camera: CameraCreate):
        async with self.db_session as session:
            db_gate = await GateOperation(session).get_gate(camera.gate_id)
            try:
                db_camera = DBCamera(
                    name=camera.name,
                    location=camera.location,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    gate_id=db_gate.id
                )
                if camera.settings:
                    result = await session.execute(select(DBCameraSetting).where(DBCameraSetting.id.in_(camera.settings)))
                    settings = result.scalars().all()
                    if len(settings) != len(camera.settings):
                        raise HTTPException(status_code=404, detail="One or more settings not found")
                    db_camera.settings.extend(settings)
                session.add(db_camera)
                await session.commit()
                await session.refresh(db_camera)
                return db_camera

            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create camera")

    async def update_camera(self, camera_id: int, camera: CameraUpdate):
        async with self.db_session as session:
            db_camera = await self.get_camera(camera_id)

            update_data = camera.dict(exclude_unset=True)
            try:
                if "gate_id" in update_data:
                    gate_id = update_data["gate_id"]
                    await GateOperation(session).get_gate(gate_id)

                for key, value in update_data.items():
                    setattr(db_camera, key, value)
                    await session.commit()
                    await session.refresh(db_camera)
                    return db_camera
            except SQLAlchemyError as error:
                    await session.rollback()
                    raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update camera")

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


class LprOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def get_lpr(self, lpr_id: int):
        async with self.db_session as session:
            query = await session.execute(select(DBLpr).where(DBLpr.id == lpr_id).options(selectinload(DBLpr.clients)))
            lpr =  query.unique().scalars().first()
            if lpr is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="lpr not found")
            return lpr

    async def get_lprs(self, skip: int = 0, limit: int = 10):
        async with self.db_session as session:
            query = await session.execute(select(DBLpr).options(selectinload(DBLpr.clients)).offset(skip).limit(limit))
            return query.unique().scalars().all()

    async def create_lpr(self, lpr):
        async with self.db_session as session:
            try:
                new_lpr = DBLpr(
                    name=lpr.name,
                    description=lpr.description,
                    value=lpr.value,
                    lpr_type=lpr.lpr_type
                )
                session.add(new_lpr)
                await session.commit()
                await session.refresh(new_lpr)
                result = await session.execute(
                    select(DBLpr)
                    .where(DBLpr.id == new_lpr.id)
                    .options(selectinload(DBLpr.clients))  # Use selectinload to eager-load the relationship
                )
                new_lpr = result.scalars().first()
                return new_lpr
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

    async def update_lpr(self, lpr_id: int, lpr):
        async with self.db_session as session:
            db_lpr = await self.get_lpr(lpr_id)
            update_data = lpr.dict(exclude_unset=True)
            try:
                for key, value in lpr.dict(exclude_unset=True).items():
                    setattr(db_lpr, key, value)
                await session.commit()
                await session.refresh(db_lpr)
                return db_lpr
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))

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


class ClientOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session)

    async def create_client(self, client):
        async with self.db_session as session:
            db_lpr = await LprOperation(session).get_lpr(client.lpr_id)
            try:
                # Create the new Client instance
                new_client = DBClient(
                    ip=client.ip,
                    port=client.port,
                    auth_token=client.auth_token,
                    lpr_id=db_lpr.id
                )

                # Assign cameras to the client
                if client.camera_ids:
                    # Fetch the camera objects
                    camera_result = await session.execute(select(DBCamera).where(DBCamera.id.in_(client.camera_ids)))
                    cameras = camera_result.unique().scalars().all()

                    # Ensure all requested cameras are found
                    if len(cameras) != len(client.camera_ids):
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more cameras not found")
                    new_client.cameras.extend(cameras)
                    # new_client.cameras = cameras

                # Add the client to the database
                session.add(new_client)
                await session.commit()
                await session.refresh(new_client)

                # result = await db.execute(
                #     select(Client)
                #     .where(Client.id == new_client.id)
                #     .options(selectinload(Client.cameras), selectinload(Client.lpr))
                # )

                # Retrieve the client object with all related data properly loaded
                # client_with_cameras = result.unique().scalars().first()

                # return client_with_cameras
                # factory = connect_to_server(new_client.ip, new_client.port, new_client.auth_token)
                # await connection_manager.add_connection(new_client.id, factory)
                return new_client
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
