from sqlalchemy import Column, Integer, String, Float, Text, JSON
from db_base import Base


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=False)

    # Machine compatibility
    machine_model = Column(String(255), nullable=False, index=True)

    # Cross-brand compatibility family
    compatibility_group = Column(String(255), nullable=True, index=True)

    # Description for NLP similarity
    description = Column(Text, nullable=True)

    # Category
    category = Column(String(200), nullable=False)

    # Technical specifications
    diameter = Column(Float, nullable=True)
    material = Column(String(255), nullable=True)

    # Pricing and lifecycle
    price = Column(Float, nullable=False)
    lifespan = Column(Integer, nullable=True)

    # Structured specs
    specs_json = Column(JSON, nullable=True)

    # Optional image
    image_url = Column(String(500), nullable=True)