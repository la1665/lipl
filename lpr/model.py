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



# class DBCameraSettingAssociation(Base):
#     __tablename__ = 'camera_setting_association'

#     camera_id = Column(Integer, ForeignKey('cameras.id'), primary_key=True)
#     setting_id = Column(Integer, ForeignKey('camera_settings.id'), primary_key=True)
#     name = Column(String(255), nullable=False)
#     value = Column(String(255), nullable=False)

#     camera = relationship("DBCamera", back_populates="setting_associations")
#     setting = relationship("DBCameraSetting", back_populates="camera_associations")


# class DBLprSettingAssociation(Base):
#     __tablename__ = 'lpr_setting_association'

#     lpr_id = Column(Integer, ForeignKey('lprs.id'), primary_key=True)
#     setting_id = Column(Integer, ForeignKey('lpr_settings.id'), primary_key=True)
#     name = Column(String(255), nullable=False)
#     value = Column(String(255), nullable=False)

#     lpr = relationship("DBLpr", back_populates="setting_associations")
#     setting = relationship("DBLprSetting", back_populates="lpr_associations")



# camera_settings_association = Table(
#     'camera_settings_association',
#     Base.metadata,
#     Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True),
#     Column('setting_id', Integer, ForeignKey('camera_settings.id'), primary_key=True),
# )

# lpr_settings_association = Table(
#     'lpr_settings_association',
#     Base.metadata,
#     Column('lpr_id', Integer, ForeignKey('lprs.id'), primary_key=True),
#     Column('setting_id', Integer, ForeignKey('lpr_settings.id'), primary_key=True),
# )


camera_lpr_association = Table(
    'camera_lpr_association',
    Base.metadata,
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True),
    Column('lpr_id', Integer, ForeignKey('lprs.id'), primary_key=True),
)



class DBBuilding(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True, unique=True)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    gates = relationship('DBGate', back_populates='building', cascade='all, delete-orphan', lazy="selectin")


class DBGate(Base):
    __tablename__ = 'gates'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True, unique=True)
    gate_type = Column(sqlEnum(GateType), default=GateType.BOTH, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)
    building = relationship('DBBuilding', back_populates='gates', lazy="selectin")
    cameras = relationship("DBCamera", back_populates="gate", cascade="all, delete-orphan", lazy="selectin")




class DBCameraSetting(Base):
    __tablename__ = 'camera_settings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(sqlEnum(SettingType),default=SettingType.STRING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # cameras = relationship("DBCamera", secondary=camera_settings_association, back_populates="settings", lazy="selectin")
    # camera_associations = relationship("DBCameraSettingAssociation", back_populates="setting", lazy="selectin")

class DBCameraSettingInstance(Base):
    __tablename__ = 'camera_setting_instances'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=False)
    camera = relationship("DBCamera", back_populates="settings", lazy="selectin")

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(
        sqlEnum(SettingType), default=SettingType.STRING, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    default_setting_id = Column(Integer, ForeignKey('camera_settings.id'), nullable=True)
    default_setting = relationship("DBCameraSetting", lazy="selectin")



class DBCamera(Base):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False, unique=True)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    gate_id = Column(Integer, ForeignKey('gates.id'), nullable=False)
    gate = relationship("DBGate", back_populates="cameras", lazy="selectin")
    # settings = relationship("DBCameraSetting", secondary=camera_settings_association, back_populates="cameras", lazy="selectin")
    # setting_associations = relationship("DBCameraSettingAssociation", back_populates="camera", cascade="all, delete-orphan", lazy="selectin")
    settings = relationship(
            "DBCameraSettingInstance",
            back_populates="camera",
            lazy="selectin",
            cascade="all, delete-orphan"
        )
    lprs = relationship(
            'DBLpr',
            secondary=camera_lpr_association,
            back_populates='cameras',
            lazy="joined"
        )

    # @property
    # def settings(self):
    #     return {assoc.name: assoc.value for assoc in self.setting_associations}



class DBLprSetting(Base):
    __tablename__ = 'lpr_settings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(sqlEnum(SettingType),default=SettingType.STRING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # lprs = relationship("DBLpr", secondary=lpr_settings_association, back_populates="settings", lazy="selectin")
    # lpr_associations = relationship("DBLprSettingAssociation", back_populates="setting", lazy="selectin")


class DBLprSettingInstance(Base):
    __tablename__ = 'lpr_setting_instances'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lpr_id = Column(Integer, ForeignKey('lprs.id'), nullable=False)
    lpr = relationship("DBLpr", back_populates="settings", lazy="selectin")

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(
        sqlEnum(SettingType), default=SettingType.STRING, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    default_setting_id = Column(Integer, ForeignKey('lpr_settings.id'), nullable=True)
    default_setting = relationship("DBLprSetting", lazy="selectin")



class DBLpr(Base):
    __tablename__ = 'lprs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True, unique=True)
    ip = Column(String, nullable=False, index=True)
    port = Column(Integer, nullable=False)
    auth_token = Column(String, nullable=False)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    # settings = relationship("DBLprSetting", secondary=lpr_settings_association, back_populates="lprs", lazy="selectin")
    # setting_associations = relationship("DBLprSettingAssociation", back_populates="lpr", cascade="all, delete-orphan", lazy="selectin")

    settings = relationship(
            "DBLprSettingInstance",
            back_populates="lpr",
            lazy="selectin",
            cascade="all, delete-orphan"
        )
    cameras = relationship(
            'DBCamera',
            secondary=camera_lpr_association,
            back_populates='lprs',
            lazy="joined"
        )

    # @property
    # def settings(self):
    #     return {assoc.name: assoc.value for assoc in self.setting_associations}





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
