import os
import json
import sqlite3
from sqlalchemy import text
from utils.database import SessionLocal
from models.part import Part


# =========================================================
# Seed/sync PostgreSQL parts table from local SQLite database
# =========================================================
# Requirements:
# 1. .env DATABASE_URL must point to PostgreSQL
# 2. Local SQLite DB file must exist in backend folder
# 3. PostgreSQL parts table must have all required columns
#
# Default SQLite path:
#   smart_farmer.db
#
# If your file name is different, run in PowerShell:
#   $env:SQLITE_SOURCE_PATH="smart_farmer"
#   python seed_parts_from_sqlite_db.py
#
# Optional exact sync:
#   $env:EXACT_PARTS_SYNC="1"
#   python seed_parts_from_sqlite_db.py
# =========================================================


SQLITE_SOURCE_PATH = os.getenv("SQLITE_SOURCE_PATH", "smart_farmer.db")
EXACT_SYNC = os.getenv("EXACT_PARTS_SYNC", "0") == "1"


PART_COLUMNS = [
    "id",
    "name",
    "brand",
    "machine_model",
    "compatibility_group",
    "machine_family",
    "function_type",
    "description",
    "category",
    "diameter",
    "material",
    "price",
    "lifespan",
    "specs_json",
    "image_url",
]


def find_sqlite_file():
    possible_paths = [
        SQLITE_SOURCE_PATH,
        "smart_farmer.db",
        "smart_farmer",
        "./smart_farmer.db",
        "./smart_farmer",
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            return path

    raise FileNotFoundError(
        "SQLite database file not found. Put smart_farmer.db in backend folder "
        "or set SQLITE_SOURCE_PATH."
    )


def parse_specs_json(value):
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}

    return value


def load_parts_from_sqlite(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parts'")
        if cursor.fetchone() is None:
            raise Exception("No 'parts' table found in SQLite database.")

        cursor.execute("PRAGMA table_info(parts)")
        existing_columns = [row["name"] for row in cursor.fetchall()]

        selected_columns = [col for col in PART_COLUMNS if col in existing_columns]

        if "id" not in selected_columns:
            raise Exception("SQLite parts table must have an id column.")

        query = f"SELECT {', '.join(selected_columns)} FROM parts ORDER BY id"
        cursor.execute(query)

        rows = cursor.fetchall()

        parts = []

        for row in rows:
            item = {}

            for col in PART_COLUMNS:
                item[col] = row[col] if col in selected_columns else None

            item["specs_json"] = parse_specs_json(item.get("specs_json"))

            parts.append(item)

        return parts

    finally:
        conn.close()


def upsert_parts(parts_data):
    db = SessionLocal()

    inserted = 0
    updated = 0
    deleted = 0

    try:
        snapshot_ids = {item["id"] for item in parts_data if item.get("id") is not None}

        for item in parts_data:
            part_id = item.get("id")

            if part_id is None:
                print(f"Skipping row without id: {item}")
                continue

            existing = db.query(Part).filter(Part.id == part_id).first()

            if existing:
                for col in PART_COLUMNS:
                    if col == "id":
                        continue

                    if hasattr(existing, col):
                        setattr(existing, col, item.get(col))

                updated += 1

            else:
                create_data = {
                    col: item.get(col)
                    for col in PART_COLUMNS
                    if hasattr(Part, col)
                }

                db.add(Part(**create_data))
                inserted += 1

        if EXACT_SYNC:
            extra_parts = db.query(Part).filter(~Part.id.in_(snapshot_ids)).all()

            for part in extra_parts:
                db.delete(part)
                deleted += 1

        db.commit()

        # Fix PostgreSQL sequence after inserting explicit ids
        try:
            db.execute(
                text(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('parts', 'id'),
                        COALESCE((SELECT MAX(id) FROM parts), 1),
                        true
                    )
                    """
                )
            )
            db.commit()
        except Exception as sequence_error:
            db.rollback()
            print(f"Warning: Could not reset parts id sequence: {sequence_error}")

        print("\n✅ Parts seed completed successfully")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Deleted extras: {deleted}")
        print(f"SQLite snapshot rows: {len(parts_data)}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error while seeding parts: {e}")

    finally:
        db.close()


def main():
    print("🔧 Loading parts from SQLite...")

    sqlite_path = find_sqlite_file()
    print(f"SQLite source: {sqlite_path}")

    parts_data = load_parts_from_sqlite(sqlite_path)
    print(f"Parts found in SQLite: {len(parts_data)}")

    if len(parts_data) == 0:
        print("No parts found. Nothing to seed.")
        return

    print("🔧 Syncing parts into PostgreSQL...")
    upsert_parts(parts_data)


if __name__ == "__main__":
    main()