from sqlalchemy import Column, Integer, String, ForeignKey
from db_base import Base


class InventorySeason(Base):
    __tablename__ = "inventory_seasons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    start_month = Column(String(20), nullable=False)
    end_month = Column(String(20), nullable=False)


class InventoryStage(Base):
    __tablename__ = "inventory_stages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    sinhala_name = Column(String(100), nullable=True)


class InventoryMachineCategory(Base):
    __tablename__ = "inventory_machine_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class InventoryBrand(Base):
    __tablename__ = "inventory_brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("inventory_machine_categories.id"),
        nullable=False
    )


class InventoryMachineModel(Base):
    __tablename__ = "inventory_machine_models"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(
        Integer,
        ForeignKey("inventory_brands.id"),
        nullable=False
    )
    category_id = Column(
        Integer,
        ForeignKey("inventory_machine_categories.id"),
        nullable=False
    )
    model_name = Column(String(150), nullable=False)


class InventoryPart(Base):
    __tablename__ = "inventory_parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    part_type = Column(String(100), nullable=True)


class InventoryModelPartMapping(Base):
    __tablename__ = "inventory_model_part_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(
        Integer,
        ForeignKey("inventory_machine_models.id"),
        nullable=False
    )
    part_id = Column(
        Integer,
        ForeignKey("inventory_parts.id"),
        nullable=False
    )
    criticality = Column(String(50), nullable=False)


class InventorySeasonalDemandRule(Base):
    __tablename__ = "inventory_seasonal_demand_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    season_id = Column(
        Integer,
        ForeignKey("inventory_seasons.id"),
        nullable=False
    )
    stage_id = Column(
        Integer,
        ForeignKey("inventory_stages.id"),
        nullable=False
    )
    category_id = Column(
        Integer,
        ForeignKey("inventory_machine_categories.id"),
        nullable=False
    )
    demand_level = Column(String(50), nullable=False)
    base_demand = Column(Integer, nullable=False)


class InventoryDemandHistory(Base):
    __tablename__ = "inventory_demand_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(
        Integer,
        ForeignKey("inventory_machine_models.id"),
        nullable=False
    )
    part_id = Column(
        Integer,
        ForeignKey("inventory_parts.id"),
        nullable=False
    )
    month = Column(String(20), nullable=False)
    season_id = Column(
        Integer,
        ForeignKey("inventory_seasons.id"),
        nullable=False
    )
    stage_id = Column(
        Integer,
        ForeignKey("inventory_stages.id"),
        nullable=False
    )
    demand_quantity = Column(Integer, nullable=False)


class InventoryStockTestRecord(Base):
    __tablename__ = "inventory_stock_test_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(
        Integer,
        ForeignKey("inventory_machine_models.id"),
        nullable=False
    )
    part_id = Column(
        Integer,
        ForeignKey("inventory_parts.id"),
        nullable=False
    )
    current_stock = Column(Integer, nullable=False)