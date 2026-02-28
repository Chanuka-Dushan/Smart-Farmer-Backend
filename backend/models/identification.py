"""
ORM models for part identification system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db_base import Base


class IdentificationTractor(Base):
    __tablename__ = "identification_tractors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    compatibilities = relationship("IdentificationPartCompatibility", back_populates="tractor")


class IdentificationPart(Base):
    __tablename__ = "identification_parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    part_number = Column(String(64), unique=True)
    description = Column(Text)
    image = Column(String(512))
    model_3d_vid = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    compatibilities = relationship("IdentificationPartCompatibility", back_populates="part")


class IdentificationPartCompatibility(Base):
    __tablename__ = "identification_part_compatibility"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("identification_parts.id", ondelete="CASCADE"), nullable=False)
    tractor_id = Column(Integer, ForeignKey("identification_tractors.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    part = relationship("IdentificationPart", back_populates="compatibilities")
    tractor = relationship("IdentificationTractor", back_populates="compatibilities")
