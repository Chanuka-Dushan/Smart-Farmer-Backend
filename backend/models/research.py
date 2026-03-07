from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from db_base import Base  # same Base you use in main.py


class CompatibilityLabel(Base):
    __tablename__ = "compatibility_labels"

    id = Column(Integer, primary_key=True, index=True)

    part_id_1 = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)
    part_id_2 = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)

    label = Column(Integer, nullable=False)  # 1 compatible, 0 incompatible
    source = Column(String, default="manual", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)
    recommended_part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)

    feedback = Column(String, nullable=False)  # "accept" or "reject"
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PartVector(Base):
    __tablename__ = "part_vectors"

    part_id = Column(Integer, ForeignKey("parts.id"), primary_key=True)

    vector = Column(JSON, nullable=False)  # store list like [0.12, 0.98, ...]
    vector_version = Column(String, nullable=False, default="v1")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(String, nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)


class InventoryStock(Base):
    __tablename__ = "inventory_stock"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(String, nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)

    stock_level = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)