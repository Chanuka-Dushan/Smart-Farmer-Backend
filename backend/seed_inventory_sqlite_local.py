import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from models.inventory_models import (
    InventorySeason,
    InventoryStage,
    InventoryMachineCategory,
    InventoryBrand,
    InventoryMachineModel,
    InventoryPart,
    InventoryModelPartMapping,
    InventorySeasonalDemandRule,
    InventoryDemandHistory,
    InventoryStockTestRecord,
)


# =========================================================
# Sync local SQLite inventory data into PostgreSQL
# =========================================================
#
# Step 1:
#   Make sure SQLite already has data:
#   python seed_inventory_sqlite_local.py
#
# Step 2:
#   Run this file:
#   python sync_inventory_sqlite_to_postgres.py
#
# This copies data from:
#   smart_farmer.db
#
# Into PostgreSQL using:
#   DATABASE_URL from .env
#
# Then data will be visible in pgAdmin.
# =========================================================


load_dotenv()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "smart_farmer.db")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in .env file")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


TABLE_MODEL_ORDER = [
    {
        "table": "inventory_seasons",
        "model": InventorySeason,
        "pg_table": "inventory_seasons",
    },
    {
        "table": "inventory_stages",
        "model": InventoryStage,
        "pg_table": "inventory_stages",
    },
    {
        "table": "inventory_machine_categories",
        "model": InventoryMachineCategory,
        "pg_table": "inventory_machine_categories",
    },
    {
        "table": "inventory_brands",
        "model": InventoryBrand,
        "pg_table": "inventory_brands",
    },
    {
        "table": "inventory_machine_models",
        "model": InventoryMachineModel,
        "pg_table": "inventory_machine_models",
    },
    {
        "table": "inventory_parts",
        "model": InventoryPart,
        "pg_table": "inventory_parts",
    },
    {
        "table": "inventory_model_part_mappings",
        "model": InventoryModelPartMapping,
        "pg_table": "inventory_model_part_mappings",
    },
    {
        "table": "inventory_seasonal_demand_rules",
        "model": InventorySeasonalDemandRule,
        "pg_table": "inventory_seasonal_demand_rules",
    },
    {
        "table": "inventory_demand_history",
        "model": InventoryDemandHistory,
        "pg_table": "inventory_demand_history",
    },
    {
        "table": "inventory_stock_test_records",
        "model": InventoryStockTestRecord,
        "pg_table": "inventory_stock_test_records",
    },
]


def sqlite_table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,),
    )

    return cursor.fetchone() is not None


def read_sqlite_table(sqlite_cursor, table_name):
    if not sqlite_table_exists(sqlite_cursor, table_name):
        raise Exception(f"SQLite table not found: {table_name}")

    sqlite_cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
    rows = sqlite_cursor.fetchall()

    return [dict(row) for row in rows]


def get_model_columns(model):
    mapper = inspect(model)
    return {column.key for column in mapper.columns}


def filter_row_for_model(row, model):
    model_columns = get_model_columns(model)

    return {
        key: value
        for key, value in row.items()
        if key in model_columns
    }


def clear_postgres_tables(db):
    print("\nClearing PostgreSQL inventory tables...")

    # Delete child tables first, parent tables last
    for item in reversed(TABLE_MODEL_ORDER):
        model = item["model"]
        table_name = item["pg_table"]

        deleted_count = db.query(model).delete(synchronize_session=False)
        print(f"Deleted from {table_name}: {deleted_count}")

    db.commit()


def insert_table_data(db, table_name, model, rows):
    if not rows:
        print(f"{table_name}: 0 rows found in SQLite. Skipping.")
        return 0

    clean_rows = [
        filter_row_for_model(row, model)
        for row in rows
    ]

    db.bulk_insert_mappings(model, clean_rows)
    db.commit()

    print(f"Inserted into {table_name}: {len(clean_rows)}")

    return len(clean_rows)


def reset_postgres_sequences(db):
    print("\nResetting PostgreSQL ID sequences...")

    for item in TABLE_MODEL_ORDER:
        table_name = item["pg_table"]

        try:
            db.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        true
                    )
                    """
                )
            )
            db.commit()
            print(f"Sequence reset: {table_name}")

        except Exception as e:
            db.rollback()
            print(f"Warning: Could not reset sequence for {table_name}: {e}")


def print_postgres_counts(db):
    print("\nPostgreSQL seed summary:")

    for item in TABLE_MODEL_ORDER:
        model = item["model"]
        table_name = item["pg_table"]

        count = db.query(model).count()
        print(f"{table_name}: {count}")


def sync_inventory_sqlite_to_postgres():
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_DB_PATH}. "
            "Make sure smart_farmer.db is in the backend folder."
        )

    print(f"SQLite source: {SQLITE_DB_PATH}")
    print("PostgreSQL target: DATABASE_URL from .env")

    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    db = SessionLocal()

    try:
        sqlite_data = {}

        print("\nReading SQLite data...")

        for item in TABLE_MODEL_ORDER:
            table_name = item["table"]
            rows = read_sqlite_table(sqlite_cursor, table_name)
            sqlite_data[table_name] = rows
            print(f"{table_name}: {len(rows)} rows")

        clear_postgres_tables(db)

        print("\nInserting data into PostgreSQL...")

        for item in TABLE_MODEL_ORDER:
            table_name = item["table"]
            model = item["model"]

            rows = sqlite_data[table_name]
            insert_table_data(db, table_name, model, rows)

        reset_postgres_sequences(db)

        print_postgres_counts(db)

        print("\n✅ SQLite inventory data copied to PostgreSQL successfully.")
        print("Now refresh pgAdmin and check your inventory tables.")

    except Exception as e:
        db.rollback()
        print("\n❌ Error syncing SQLite data to PostgreSQL:")
        print(e)
        raise

    finally:
        sqlite_conn.close()
        db.close()


if __name__ == "__main__":
    sync_inventory_sqlite_to_postgres()