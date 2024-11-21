from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.engine import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    vehicle_class = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    vehicle_color = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("DBUser", back_populates="vehicles")
    traffic_entries = relationship("Traffic", back_populates="vehicle")  # Add this if not already present


class Traffic(Base):
    __tablename__ = "traffic"
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), index=True)
    timestamp = Column(DateTime, default=func.now())
    ocr_accuracy = Column(Float, nullable=True)
    vision_speed = Column(Float, nullable=True)

    vehicle = relationship("Vehicle", back_populates="traffic_entries")

# Vehicle.traffic_entries = relationship("Traffic", back_populates="vehicle")
