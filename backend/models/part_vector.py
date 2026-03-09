from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from db_base import Base


class PartVector(Base):
    __tablename__ = "part_vectors"

    part_id = Column(Integer, ForeignKey("parts.id"), primary_key=True, index=True)
    vector = Column(Text, nullable=False)
    vector_version = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)