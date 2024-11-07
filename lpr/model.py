from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Boolean,Table,Text,Float, func
from sqlalchemy import Enum as sqlEnum
from sqlalchemy.orm import relationship
from enum import Enum

from db.engine import Base


class GateType(Enum):
    ENTRANCE = 0
    EXIT = 1
    BOTH = 2


class SettingType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"


camera_settings_association = Table(
    'camera_settings_association', Base.metadata,
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True),
    Column('setting_id', Integer, ForeignKey('camera_settings.id'), primary_key=True)
)

client_camera_association = Table(
    'client_camera_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True)
)


class DBBuilding(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    gates = relationship('DBGate', back_populates='building', cascade='all, delete-orphan')


class DBGate(Base):
    __tablename__ = 'gates'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    gate_type = Column(sqlEnum(GateType), default=GateType.BOTH, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)
    building = relationship('DBBuilding', back_populates='gates')
    cameras = relationship("DBCamera", back_populates="gate", cascade="all, delete-orphan")




class DBCameraSetting(Base):
    __tablename__ = 'camera_settings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(sqlEnum(SettingType),default=SettingType.STRING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    cameras = relationship("DBCamera", secondary=camera_settings_association, back_populates="settings")


class DBCamera(Base):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=True)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    gate_id = Column(Integer, ForeignKey('gates.id'), nullable=False)
    gate = relationship("DBGate", back_populates="cameras")
    settings = relationship("DBCameraSetting", secondary=camera_settings_association, back_populates="cameras", lazy="joined")
    clients = relationship(
            'DBClient',
            secondary=client_camera_association,
            back_populates='cameras'
        )


class DBLpr(Base):
    __tablename__ = 'lprs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    value = Column(String(255), nullable=False)
    lpr_type = Column(sqlEnum(SettingType), nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    clients = relationship('DBClient', back_populates='lpr')


class DBClient(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip = Column(String, nullable=False, index=True)
    port = Column(Integer, nullable=False)
    auth_token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    # Foreign key for LPR
    lpr_id = Column(Integer, ForeignKey('lprs.id'), nullable=False)
    lpr = relationship('DBLpr', back_populates='clients')

    # Relationship to hold multiple cameras
    cameras = relationship(
            'DBCamera',
            secondary=client_camera_association,
            back_populates='clients',
            lazy="joined"
        )


class DBPlateData(Base):
    __tablename__ = 'plate_data'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    plate_number = Column(String, nullable=False)
    ocr_accuracy = Column(Float, nullable=True)
    vision_speed = Column(Float, nullable=True)
    gate = Column(String, nullable=True)


class DBImageData(Base):
    __tablename__ = 'image_data'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String, nullable=False)
    gate = Column(String, nullable=True)
    file_path = Column(String, nullable=False)  # Path to the saved image
    timestamp = Column(DateTime, nullable=False, default=func.now())
