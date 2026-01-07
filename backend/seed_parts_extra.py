"""
Seed file to add EXTRA MF 240 parts
This file is SAFE to run once.
It will NOT touch existing parts.
"""

from init_db import SessionLocal
from main import Part


# =========================================================
# STEP 1: Define ONLY the NEW MF 240 parts
# =========================================================

new_parts = [
    {
        "name": "Front Hub Grease Seal",
        "brand": "MF240",
        "description": "Prevents grease leakage and protects the front hub assembly from dust and moisture.",
        "category": "Axle & Steering",
        "price": 400,
        "lifespan": 3200,
        "material": "Rubber + Steel",
        "diameter": 65.0,
        "image_url": None
    },
    {
        "name": "Front Axel",
        "brand": "MF240",
        "description": "Main front axle component that supports the tractor’s front wheels and steering system.",
        "category": "Axle & Steering",
        "price": 12500,
        "lifespan": 12500,
        "material": "Forged Steel",
        "diameter": 42.0,
        "image_url": None
    },
    {
        "name": "Front Center Beam",
        "brand": "MF240",
        "description": "Central beam connecting the front axle assembly and bearing steering and load forces.",
        "category": "Axle & Steering",
        "price": 45000,
        "lifespan": 10000,
        "material": "Cast Iron",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Center Pin Bush O/M",
        "brand": "MF240",
        "description": "Bush fitted to the center pin to allow smooth pivoting of the front axle.",
        "category": "Axle & Steering",
        "price": 1500,
        "lifespan": 2800,
        "material": "Bronze",
        "diameter": 28.0,
        "image_url": None
    },
    {
        "name": "King Pin Bush",
        "brand": "MF240",
        "description": "Supports king pin movement and reduces friction in the steering knuckle.",
        "category": "Axle & Steering",
        "price": 900,
        "lifespan": 3400,
        "material": "Bronze Alloy",
        "diameter": 30.0,
        "image_url": None
    },
    {
        "name": "Hydraulic Control Valve",
        "brand": "MF240",
        "description": "Controls the flow and direction of hydraulic oil to operate lifting mechanisms.",
        "category": "Hydraulic System",
        "price": 12500,
        "lifespan": 7000,
        "material": "Cast Iron",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Hydraulic Safety Valve",
        "brand": "MF240",
        "description": "Protects the hydraulic system by releasing excess pressure when limits are exceeded.",
        "category": "Hydraulic System",
        "price": 3500,
        "lifespan": 6500,
        "material": "Steel",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Hydraulic Pump O-Ring Kit",
        "brand": "MF240",
        "description": "Set of O-rings used to seal hydraulic pump joints and prevent oil leakage.",
        "category": "Hydraulic System",
        "price": 2000,
        "lifespan": 2100,
        "material": "Nitrile Rubber",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Pinion Pilot Racer",
        "brand": "MF240",
        "description": "Supports alignment and smooth rotation of the pinion shaft in the transmission system.",
        "category": "Transmission System",
        "price": 3500,
        "lifespan": 3500,
        "material": "Hardened Steel",
        "diameter": 35.0,
        "image_url": None
    },
    {
        "name": "Top Cover",
        "brand": "MF240",
        "description": "Covers and protects internal hydraulic control components from external damage.",
        "category": "Hydraulic System",
        "price": 45000,
        "lifespan": 9000,
        "material": "Cast Iron",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Lift Arm",
        "brand": "MF240",
        "description": "Transfers hydraulic lifting force to agricultural implements attached to the tractor.",
        "category": "Hydraulic System",
        "price": 12500,
        "lifespan": 9000,
        "material": "Forged Steel",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Bell Cam",
        "brand": "MF240",
        "description": "Controls lift position and feedback mechanism within the hydraulic system.",
        "category": "Hydraulic System",
        "price": 9000,
        "lifespan": 7600,
        "material": "Steel",
        "diameter": None,
        "image_url": None
    },
    {
        "name": "Lift Shaft",
        "brand": "MF240",
        "description": "Rotating shaft that transmits hydraulic lift motion to the lift arms.",
        "category": "Hydraulic System",
        "price": 12500,
        "lifespan": 11000,
        "material": "Alloy Steel",
        "diameter": 38.0,
        "image_url": None
    }
]


# =========================================================
# STEP 2: Insert new parts into DB
# =========================================================

def seed_extra_parts():
    db = SessionLocal()

    try:
        for data in new_parts:
            part = Part(**data)
            db.add(part)

        db.commit()
        print("✅ MF240 extra parts inserted successfully")

    except Exception as e:
        db.rollback()
        print("❌ Error while inserting parts:", e)

    finally:
        db.close()


# =========================================================
# STEP 3: Run the seed
# =========================================================

if __name__ == "__main__":
    seed_extra_parts()
