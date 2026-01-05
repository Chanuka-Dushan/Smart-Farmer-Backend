from sqlalchemy import Column, Integer, String, Float
from init_db import Base   # <-- IMPORTANT (match your Base)

class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)

    diameter = Column(Float, nullable=True)
    material = Column(String, nullable=True)

    price = Column(Float, nullable=False)
    lifespan = Column(Integer, nullable=True)
