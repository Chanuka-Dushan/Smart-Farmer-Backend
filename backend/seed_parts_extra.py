from sqlalchemy.orm import Session
from utils.database import SessionLocal
from models.part import Part


# =========================================================
# OLD DATA RESTORE SEED
# SAFE:
# - does NOT delete current parts
# - skips duplicates by (name + machine_model)
# - adds machine_model and specs_json
# =========================================================


old_parts = [

    # ==================================================
    # MF 240 EXTRA PARTS (from old extra seed)
    # ==================================================
    {
        "name": "Front Hub Grease Seal",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Prevents grease leakage and protects the front hub assembly from dust and moisture.",
        "category": "steering and front axel parts",
        "price": 400,
        "lifespan": 3200,
        "material": "Rubber + Steel",
        "diameter": 65.0,
        "specs_json": {
            "type": "grease seal",
            "system": "front hub",
            "function": "prevents grease leakage",
            "dust_protection": True
        },
        "image_url": None
    },
    {
        "name": "Front Axel",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Main front axle component that supports the tractor’s front wheels and steering system.",
        "category": "steering and front axel parts",
        "price": 12500,
        "lifespan": 12500,
        "material": "Forged Steel",
        "diameter": 42.0,
        "specs_json": {
            "type": "front axle",
            "system": "steering and front axle",
            "function": "supports front wheels and steering load",
            "heavy_duty": True
        },
        "image_url": None
    },
    {
        "name": "Front Center Beam",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Central beam connecting the front axle assembly and bearing steering and load forces.",
        "category": "body and structural parts",
        "price": 45000,
        "lifespan": 10000,
        "material": "Cast Iron",
        "diameter": None,
        "specs_json": {
            "type": "center beam",
            "system": "body and structural",
            "function": "supports front axle structure",
            "load_bearing": True
        },
        "image_url": None
    },
    {
        "name": "Center Pin Bush O/M",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Bush fitted to the center pin to allow smooth pivoting of the front axle.",
        "category": "steering and front axel parts",
        "price": 1500,
        "lifespan": 2800,
        "material": "Bronze",
        "diameter": 28.0,
        "specs_json": {
            "type": "center pin bush",
            "system": "front axle pivot",
            "function": "allows smooth axle pivoting",
            "lubricated": True
        },
        "image_url": None
    },
    {
        "name": "King Pin Bush",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Supports king pin movement and reduces friction in the steering knuckle.",
        "category": "steering and front axel parts",
        "price": 900,
        "lifespan": 3400,
        "material": "Bronze Alloy",
        "diameter": 30.0,
        "specs_json": {
            "type": "king pin bush",
            "system": "steering pivot",
            "function": "reduces friction in steering knuckle",
            "lubricated": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Control Valve",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Controls the flow and direction of hydraulic oil to operate lifting mechanisms.",
        "category": "Hydralic",
        "price": 12500,
        "lifespan": 7000,
        "material": "Cast Iron",
        "diameter": None,
        "specs_json": {
            "type": "hydraulic control valve",
            "system": "hydraulic",
            "function": "controls hydraulic oil flow",
            "flow_control": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Safety Valve",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Protects the hydraulic system by releasing excess pressure when limits are exceeded.",
        "category": "Hydralic",
        "price": 3500,
        "lifespan": 6500,
        "material": "Steel",
        "diameter": None,
        "specs_json": {
            "type": "hydraulic safety valve",
            "system": "hydraulic",
            "function": "releases excess pressure",
            "pressure_relief": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Pump O-Ring Kit",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Set of O-rings used to seal hydraulic pump joints and prevent oil leakage.",
        "category": "seals/orings/gaskets",
        "price": 2000,
        "lifespan": 2100,
        "material": "Nitrile Rubber",
        "diameter": None,
        "specs_json": {
            "type": "o-ring kit",
            "system": "hydraulic sealing",
            "function": "prevents oil leakage",
            "oil_resistant": True
        },
        "image_url": None
    },
    {
        "name": "Pinion Pilot Racer",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Supports alignment and smooth rotation of the pinion shaft in the transmission system.",
        "category": "bearing",
        "price": 3500,
        "lifespan": 3500,
        "material": "Hardened Steel",
        "diameter": 35.0,
        "specs_json": {
            "type": "pilot race",
            "system": "transmission",
            "function": "supports pinion shaft alignment",
            "precision_ground": True
        },
        "image_url": None
    },
    {
        "name": "Top Cover",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Covers and protects internal hydraulic control components from external damage.",
        "category": "Hydralic",
        "price": 45000,
        "lifespan": 9000,
        "material": "Cast Iron",
        "diameter": None,
        "specs_json": {
            "type": "top cover",
            "system": "hydraulic housing",
            "function": "protects hydraulic internals",
            "protective_cover": True
        },
        "image_url": None
    },
    {
        "name": "Lift Arm",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Transfers hydraulic lifting force to agricultural implements attached to the tractor.",
        "category": "Hydralic",
        "price": 12500,
        "lifespan": 9000,
        "material": "Forged Steel",
        "diameter": None,
        "specs_json": {
            "type": "lift arm",
            "system": "3-point linkage",
            "function": "transfers lifting force to implements",
            "implement_support": True
        },
        "image_url": None
    },
    {
        "name": "Bell Cam",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Controls lift position and feedback mechanism within the hydraulic system.",
        "category": "Hydralic",
        "price": 9000,
        "lifespan": 7600,
        "material": "Steel",
        "diameter": None,
        "specs_json": {
            "type": "bell cam",
            "system": "hydraulic control",
            "function": "controls lift position feedback",
            "control_part": True
        },
        "image_url": None
    },
    {
        "name": "Lift Shaft",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Rotating shaft that transmits hydraulic lift motion to the lift arms.",
        "category": "Hydralic",
        "price": 12500,
        "lifespan": 11000,
        "material": "Alloy Steel",
        "diameter": 38.0,
        "specs_json": {
            "type": "lift shaft",
            "system": "hydraulic linkage",
            "function": "transmits lift motion",
            "rotating_shaft": True
        },
        "image_url": None
    },

    # ==================================================
    # TAFE 45 DI – ENGINE / FUEL / BEARING / STEERING / TRANSMISSION / HYDRAULIC
    # ==================================================
    {
        "name": "Oil Filter",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Engine oil filter",
        "category": "engine",
        "diameter": 80.0,
        "material": "Steel + filter media",
        "price": 4500,
        "lifespan": 250,
        "specs_json": {
            "type": "oil filter",
            "system": "engine lubrication",
            "service_interval_hr": 250,
            "filter_media": "oil filter media"
        },
        "image_url": None
    },
    {
        "name": "Fuel Filter",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Diesel fuel filter",
        "category": "fuel system",
        "diameter": 50.0,
        "material": "Metal + paper",
        "price": 3000,
        "lifespan": 400,
        "specs_json": {
            "type": "fuel filter",
            "system": "fuel system",
            "service_interval_hr": 400,
            "filter_media": "paper"
        },
        "image_url": None
    },
    {
        "name": "Air Filter",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Engine air intake filter",
        "category": "engine",
        "diameter": 120.0,
        "material": "Plastic + paper",
        "price": 6500,
        "lifespan": 500,
        "specs_json": {
            "type": "air filter",
            "system": "engine intake",
            "service_interval_hr": 500,
            "filter_media": "paper"
        },
        "image_url": None
    },
    {
        "name": "Head Gasket",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Cylinder head gasket",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "Multi-layer steel",
        "price": 35000,
        "lifespan": 8000,
        "specs_json": {
            "type": "head gasket",
            "system": "engine sealing",
            "heat_resistant": True,
            "function": "seals cylinder head and block"
        },
        "image_url": None
    },
    {
        "name": "Crank Oil Seal (Rear)",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Rear crankshaft oil seal",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "Rubber + steel",
        "price": 5000,
        "lifespan": 6000,
        "specs_json": {
            "type": "crank oil seal",
            "system": "engine sealing",
            "position": "rear",
            "oil_resistant": True
        },
        "image_url": None
    },
    {
        "name": "Front Hub Bearing Inner",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Inner front hub bearing",
        "category": "bearing",
        "diameter": 90.0,
        "material": "Hardened steel",
        "price": 18000,
        "lifespan": 3000,
        "specs_json": {
            "type": "front hub bearing inner",
            "system": "front hub",
            "function": "supports wheel rotation",
            "precision_ground": True
        },
        "image_url": None
    },
    {
        "name": "Front Hub Bearing Outer",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Outer front hub bearing",
        "category": "bearing",
        "diameter": 100.0,
        "material": "Hardened steel",
        "price": 22000,
        "lifespan": 3000,
        "specs_json": {
            "type": "front hub bearing outer",
            "system": "front hub",
            "function": "supports wheel rotation",
            "precision_ground": True
        },
        "image_url": None
    },
    {
        "name": "Pinion Pilot Racer",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Pinion pilot bearing race",
        "category": "bearing",
        "diameter": 60.0,
        "material": "Bearing steel",
        "price": 12000,
        "lifespan": 4000,
        "specs_json": {
            "type": "pilot race",
            "system": "transmission",
            "function": "supports pinion shaft rotation",
            "bearing_grade": "standard"
        },
        "image_url": None
    },
    {
        "name": "Front Axle",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Front axle assembly",
        "category": "steering and front axel parts",
        "diameter": None,
        "material": "Forged steel",
        "price": 180000,
        "lifespan": 12000,
        "specs_json": {
            "type": "front axle",
            "system": "steering and front axle",
            "function": "supports front wheel assembly",
            "heavy_duty": True
        },
        "image_url": None
    },
    {
        "name": "Front Center Beam",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Front axle center beam",
        "category": "steering and front axel parts",
        "diameter": None,
        "material": "Steel",
        "price": 85000,
        "lifespan": 10000,
        "specs_json": {
            "type": "center beam",
            "system": "front axle structure",
            "function": "supports axle center section",
            "load_bearing": True
        },
        "image_url": None
    },
    {
        "name": "Center Pin Bush",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Center pin bush",
        "category": "steering and front axel parts",
        "diameter": 40.0,
        "material": "Bronze",
        "price": 3500,
        "lifespan": 3000,
        "specs_json": {
            "type": "center pin bush",
            "system": "front axle pivot",
            "function": "reduces pivot wear",
            "lubricated": True
        },
        "image_url": None
    },
    {
        "name": "King Pin Bush",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "King pin steering bush",
        "category": "steering and front axel parts",
        "diameter": 35.0,
        "material": "Bronze",
        "price": 6000,
        "lifespan": 3500,
        "specs_json": {
            "type": "king pin bush",
            "system": "steering pivot",
            "function": "supports steering movement",
            "lubricated": True
        },
        "image_url": None
    },
    {
        "name": "Crown Wheel & Pinion Assembly",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Differential gear set",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "Hardened alloy steel",
        "price": 180000,
        "lifespan": 12000,
        "specs_json": {
            "type": "crown wheel and pinion assembly",
            "system": "differential",
            "function": "transfers torque to axle",
            "hardened": True
        },
        "image_url": None
    },
    {
        "name": "Reverse Gear Wheel",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Reverse gear for gearbox",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "Hardened steel",
        "price": 45000,
        "lifespan": 9000,
        "specs_json": {
            "type": "reverse gear wheel",
            "system": "gearbox",
            "function": "enables reverse motion",
            "hardened": True
        },
        "image_url": None
    },
    {
        "name": "Top Cover",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Gearbox top cover",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "Cast iron",
        "price": 30000,
        "lifespan": 10000,
        "specs_json": {
            "type": "top cover",
            "system": "gearbox housing",
            "function": "covers gearbox internals",
            "protective_cover": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Control Valve",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Hydraulic spool valve",
        "category": "Hydralic",
        "diameter": None,
        "material": "Cast iron",
        "price": 85000,
        "lifespan": 7000,
        "specs_json": {
            "type": "hydraulic control valve",
            "system": "hydraulic",
            "function": "controls spool flow",
            "flow_control": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Safety Valve",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Hydraulic pressure relief valve",
        "category": "Hydralic",
        "diameter": None,
        "material": "Steel",
        "price": 12000,
        "lifespan": 6000,
        "specs_json": {
            "type": "hydraulic safety valve",
            "system": "hydraulic",
            "function": "relieves excess pressure",
            "pressure_relief": True
        },
        "image_url": None
    },
    {
        "name": "Hydraulic Pump O-ring Kit",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Hydraulic pump seal kit",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "Rubber",
        "price": 6000,
        "lifespan": 2000,
        "specs_json": {
            "type": "o-ring kit",
            "system": "hydraulic sealing",
            "function": "prevents seal leakage",
            "oil_resistant": True
        },
        "image_url": None
    },
    {
        "name": "Lift Arm",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "3-point hitch lift arm",
        "category": "Hydralic",
        "diameter": None,
        "material": "Forged steel",
        "price": 42000,
        "lifespan": 9000,
        "specs_json": {
            "type": "lift arm",
            "system": "3-point linkage",
            "function": "lifts implements",
            "implement_support": True
        },
        "image_url": None
    },
    {
        "name": "Bell Cam",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Hydraulic bell cam",
        "category": "Hydralic",
        "diameter": None,
        "material": "Steel",
        "price": 15000,
        "lifespan": 8000,
        "specs_json": {
            "type": "bell cam",
            "system": "hydraulic control",
            "function": "supports lift control feedback",
            "control_part": True
        },
        "image_url": None
    },
    {
        "name": "Lift Shaft",
        "brand": "tafe",
        "machine_model": "TAFE 45 DI",
        "description": "Lift mechanism shaft",
        "category": "Hydralic",
        "diameter": None,
        "material": "Hardened steel",
        "price": 60000,
        "lifespan": 10000,
        "specs_json": {
            "type": "lift shaft",
            "system": "hydraulic linkage",
            "function": "transmits lift motion",
            "rotating_shaft": True
        },
        "image_url": None
    },

    # ==================================================
    # TAFE 7250
    # ==================================================
    {
        "name": "Oil Filter",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Oil filter for TAFE 7250",
        "category": "engine",
        "diameter": 85.0,
        "material": "Steel + media",
        "price": 5500,
        "lifespan": 300,
        "specs_json": {
            "type": "oil filter",
            "system": "engine lubrication",
            "service_interval_hr": 300,
            "filter_media": "oil filter media"
        },
        "image_url": None
    },
    {
        "name": "Fuel Filter",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Fuel filter for TAFE 7250",
        "category": "fuel system",
        "diameter": 55.0,
        "material": "Metal + paper",
        "price": 3800,
        "lifespan": 450,
        "specs_json": {
            "type": "fuel filter",
            "system": "fuel system",
            "service_interval_hr": 450,
            "filter_media": "paper"
        },
        "image_url": None
    },
    {
        "name": "Front Hub Bearing Inner",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Front hub inner bearing",
        "category": "bearing",
        "diameter": 95.0,
        "material": "Hardened steel",
        "price": 20000,
        "lifespan": 3200,
        "specs_json": {
            "type": "front hub bearing inner",
            "system": "front hub",
            "function": "supports inner wheel rotation",
            "precision_ground": True
        },
        "image_url": None
    },
    {
        "name": "Front Hub Bearing Outer",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Front hub outer bearing",
        "category": "bearing",
        "diameter": 105.0,
        "material": "Hardened steel",
        "price": 24000,
        "lifespan": 3200,
        "specs_json": {
            "type": "front hub bearing outer",
            "system": "front hub",
            "function": "supports outer wheel rotation",
            "precision_ground": True
        },
        "image_url": None
    },

    # ==================================================
    # MF 240
    # ==================================================
    {
        "name": "Oil Filter",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Oil filter for MF 240",
        "category": "engine",
        "diameter": 90.0,
        "material": "Steel + media",
        "price": 5000,
        "lifespan": 300,
        "specs_json": {
            "type": "oil filter",
            "system": "engine lubrication",
            "service_interval_hr": 300,
            "filter_media": "oil filter media"
        },
        "image_url": None
    },
    {
        "name": "Fuel Filter",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Fuel filter for MF 240",
        "category": "fuel system",
        "diameter": 60.0,
        "material": "Metal + paper",
        "price": 4000,
        "lifespan": 450,
        "specs_json": {
            "type": "fuel filter",
            "system": "fuel system",
            "service_interval_hr": 450,
            "filter_media": "paper"
        },
        "image_url": None
    },
    {
        "name": "Front Hub Bearing Inner",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "MF 240 inner hub bearing",
        "category": "bearing",
        "diameter": 88.0,
        "material": "Hardened steel",
        "price": 19000,
        "lifespan": 3000,
        "specs_json": {
            "type": "front hub bearing inner",
            "system": "front hub",
            "function": "supports inner wheel rotation",
            "precision_ground": True
        },
        "image_url": None
    },
    {
        "name": "Crank Oil Seal",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Crankshaft oil seal",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "Rubber + steel",
        "price": 4500,
        "lifespan": 6000,
        "specs_json": {
            "type": "crank oil seal",
            "system": "engine sealing",
            "oil_resistant": True,
            "function": "prevents crankshaft oil leakage"
        },
        "image_url": None
    },
    {
        "name": "Crown Wheel & Pinion",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Differential crown & pinion",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "Hardened steel",
        "price": 165000,
        "lifespan": 11000,
        "specs_json": {
            "type": "crown wheel and pinion",
            "system": "differential",
            "function": "transfers final drive torque",
            "hardened": True
        },
        "image_url": None
    },
    {
        "name": "Reverse Gear",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Reverse gear wheel",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "Hardened steel",
        "price": 42000,
        "lifespan": 9000,
        "specs_json": {
            "type": "reverse gear",
            "system": "gearbox",
            "function": "enables reverse motion",
            "hardened": True
        },
        "image_url": None
    },
]


def part_exists(db: Session, name: str, machine_model: str) -> bool:
    existing = (
        db.query(Part)
        .filter(Part.name == name, Part.machine_model == machine_model)
        .first()
    )
    return existing is not None


def seed_old_parts():
    db: Session = SessionLocal()

    inserted_count = 0
    skipped_count = 0

    try:
        for item in old_parts:
            if part_exists(db, item["name"], item["machine_model"]):
                skipped_count += 1
                print(f"Skipped duplicate: {item['name']} | {item['machine_model']}")
                continue

            part = Part(
                name=item["name"],
                brand=item["brand"],
                category=item["category"],
                diameter=item["diameter"],
                material=item["material"],
                price=float(item["price"]),
                lifespan=int(item["lifespan"]),
                machine_model=item["machine_model"],
                description=item["description"],
                specs_json=item["specs_json"],
                image_url=item["image_url"],
            )

            db.add(part)
            inserted_count += 1

        db.commit()

        print("\n✅ Restore complete")
        print(f"Inserted: {inserted_count}")
        print(f"Skipped duplicates: {skipped_count}")

    except Exception as e:
        db.rollback()
        print("\n❌ Error while restoring old parts:")
        print(str(e))

    finally:
        db.close()


if __name__ == "__main__":
    seed_old_parts()