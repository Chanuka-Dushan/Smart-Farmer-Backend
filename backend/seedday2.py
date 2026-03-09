from sqlalchemy.orm import Session
from utils.database import SessionLocal
from models.part import Part

kubota_4508_parts = [
    {
        "spare_part_name": "began bearing set",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Bearing set used to support rotating shafts and reduce friction in transmission or wheel assemblies.",
        "category": "bearing",
        "diameter": 47.0,
        "material": "hardened alloy steel",
        "price": 9200,
        "lifespan_hr": 4200,
        "specs_json": {"type": "bearing set", "series": "medium duty", "lubrication": "grease"},
        "image_url": None
    },
    {
        "spare_part_name": "center beam",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Main structural beam supporting chassis balance and front section alignment.",
        "category": "body and structural parts",
        "diameter": None,
        "material": "mild steel",
        "price": 19500,
        "lifespan_hr": 10000,
        "specs_json": {"type": "frame support", "finish": "painted steel", "duty": "heavy"},
        "image_url": None
    },
    {
        "spare_part_name": "center pin bush",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Bush fitted in the front axle center pivot to reduce wear during steering movement.",
        "category": "steering and front axel parts",
        "diameter": 30.0,
        "material": "phosphor bronze",
        "price": 2400,
        "lifespan_hr": 3200,
        "specs_json": {"type": "pivot bush", "fitment": "front axle center pin", "lubricated": True},
        "image_url": None
    },
    {
        "spare_part_name": "clutch finger",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Clutch release finger used in clutch cover assembly to transfer release pressure.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "forged steel",
        "price": 2700,
        "lifespan_hr": 3400,
        "specs_json": {"type": "clutch lever finger", "system": "dry clutch", "duty": "standard"},
        "image_url": None
    },
    {
        "spare_part_name": "connectivity road",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Connecting rod linking piston and crankshaft to transmit engine force.",
        "category": "engine",
        "diameter": None,
        "material": "forged steel",
        "price": 10200,
        "lifespan_hr": 6200,
        "specs_json": {"type": "connecting rod", "engine_section": "bottom end", "balanced": True},
        "image_url": None
    },
    {
        "spare_part_name": "cranck oil seal",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Crankshaft oil seal preventing engine oil leakage at crankshaft outlet.",
        "category": "seals/orings/gaskets",
        "diameter": 52.0,
        "material": "nitrile rubber",
        "price": 1350,
        "lifespan_hr": 2600,
        "specs_json": {"type": "oil seal", "position": "crankshaft", "oil_resistant": True},
        "image_url": None
    },
    {
        "spare_part_name": "cylinder head 3",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Cylinder head assembly section housing valves and combustion chamber passages.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 29500,
        "lifespan_hr": 8200,
        "specs_json": {"type": "cylinder head", "cooling": "water cooled", "valve_mount": "overhead"},
        "image_url": None
    },
    {
        "spare_part_name": "cylinder liner",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Replaceable engine cylinder liner providing wear-resistant piston travel surface.",
        "category": "engine",
        "diameter": 95.0,
        "material": "alloy cast iron",
        "price": 8300,
        "lifespan_hr": 5200,
        "specs_json": {"type": "wet liner", "surface_finish": "honed", "wear_resistant": True},
        "image_url": None
    },
    {
        "spare_part_name": "diesel filter",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Fuel filter for removing dirt and water contaminants from diesel supply.",
        "category": "fuel system",
        "diameter": None,
        "material": "steel and filter paper",
        "price": 1900,
        "lifespan_hr": 400,
        "specs_json": {"type": "diesel fuel filter", "filter_media": "paper", "service_interval_hr": 400},
        "image_url": None
    },
    {
        "spare_part_name": "diesel filter set",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Full diesel filter service set for routine fuel system maintenance.",
        "category": "fuel system",
        "diameter": None,
        "material": "steel and cellulose media",
        "price": 3400,
        "lifespan_hr": 400,
        "specs_json": {"type": "fuel filter kit", "includes": ["filter element", "seal"], "service_interval_hr": 400},
        "image_url": None
    },
    {
        "spare_part_name": "engine valve exhause a",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Exhaust valve controlling release of burned gases from engine cylinder.",
        "category": "engine",
        "diameter": 8.0,
        "material": "heat resistant alloy steel",
        "price": 2100,
        "lifespan_hr": 4100,
        "specs_json": {"type": "exhaust valve", "heat_treated": True, "engine_side": "top end"},
        "image_url": None
    },
    {
        "spare_part_name": "front hub grease seal",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Seal used in front hub to retain grease and block dust entry.",
        "category": "seals/orings/gaskets",
        "diameter": 58.0,
        "material": "rubber with steel case",
        "price": 980,
        "lifespan_hr": 2400,
        "specs_json": {"type": "grease seal", "position": "front hub", "dust_protection": True},
        "image_url": None
    },
    {
        "spare_part_name": "front hub racer inner",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Inner bearing race used in front hub wheel assembly.",
        "category": "bearing",
        "diameter": 44.0,
        "material": "hardened steel",
        "price": 2250,
        "lifespan_hr": 4100,
        "specs_json": {"type": "inner race", "position": "front hub", "precision_ground": True},
        "image_url": None
    },
    {
        "spare_part_name": "head gasket",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Cylinder head gasket sealing compression, oil and coolant passages between block and head.",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "multi-layer steel composite",
        "price": 3800,
        "lifespan_hr": 3200,
        "specs_json": {"type": "head gasket", "sealing_layers": 3, "heat_resistant": True},
        "image_url": None
    },
    {
        "spare_part_name": "hydralic control alve",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Hydraulic control valve for regulating oil flow to lift mechanism.",
        "category": "Hydralic",
        "diameter": None,
        "material": "cast iron and machined steel",
        "price": 12800,
        "lifespan_hr": 5100,
        "specs_json": {"type": "hydraulic control valve", "pressure_control": True, "system": "3-point linkage"},
        "image_url": None
    },
    {
        "spare_part_name": "hydralic oring kit",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Hydraulic O-ring kit used to seal valve and pipe joints.",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "nitrile rubber",
        "price": 1750,
        "lifespan_hr": 2100,
        "specs_json": {"type": "o-ring kit", "oil_resistant": True, "system": "hydraulic"},
        "image_url": None
    },
    {
        "spare_part_name": "hydralic safety valve",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Hydraulic safety valve preventing overpressure damage in lift system.",
        "category": "Hydralic",
        "diameter": None,
        "material": "steel",
        "price": 6800,
        "lifespan_hr": 5000,
        "specs_json": {"type": "pressure relief valve", "safety_function": True, "system": "hydraulic"},
        "image_url": None
    },
    {
        "spare_part_name": "kin pin bush",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "King pin bush supporting front steering knuckle pivot movement.",
        "category": "steering and front axel parts",
        "diameter": 27.0,
        "material": "bronze",
        "price": 1850,
        "lifespan_hr": 3100,
        "specs_json": {"type": "king pin bush", "position": "front steering pivot", "lubricated": True},
        "image_url": None
    },
    {
        "spare_part_name": "lift arm",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Hydraulic lift arm for implement attachment and lifting.",
        "category": "Hydralic",
        "diameter": None,
        "material": "forged steel",
        "price": 15800,
        "lifespan_hr": 7100,
        "specs_json": {"type": "linkage arm", "mounting": "3-point", "implement_support": True},
        "image_url": None
    },
    {
        "spare_part_name": "oil filter",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Engine oil filter removing impurities from lubrication oil.",
        "category": "engine",
        "diameter": None,
        "material": "steel and filter media",
        "price": 1800,
        "lifespan_hr": 250,
        "specs_json": {"type": "oil filter", "spin_on": True, "service_interval_hr": 250},
        "image_url": None
    },
    {
        "spare_part_name": "pinon",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Pinion gear used in gear transmission assembly for torque transfer.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "alloy steel",
        "price": 7600,
        "lifespan_hr": 5200,
        "specs_json": {"type": "pinion gear", "gear_cut": "precision machined", "hardened": True},
        "image_url": None
    },
    {
        "spare_part_name": "pinon pilot racer",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Pilot race supporting pinion shaft alignment and smooth rotation.",
        "category": "bearing",
        "diameter": 34.0,
        "material": "hardened steel",
        "price": 2750,
        "lifespan_hr": 3600,
        "specs_json": {"type": "pilot race", "paired_with": "pinion gear", "precision_ground": True},
        "image_url": None
    },
    {
        "spare_part_name": "piston",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Engine piston converting combustion pressure into reciprocating motion.",
        "category": "engine",
        "diameter": 95.0,
        "material": "aluminium alloy",
        "price": 7100,
        "lifespan_hr": 5200,
        "specs_json": {"type": "piston", "combustion_part": True, "weight_grade": "standard"},
        "image_url": None
    },
    {
        "spare_part_name": "piston ring set",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Piston ring set for compression sealing and oil control.",
        "category": "engine",
        "diameter": 95.0,
        "material": "alloy cast iron",
        "price": 3400,
        "lifespan_hr": 3100,
        "specs_json": {"type": "ring set", "includes": ["compression ring", "oil ring"], "engine_fit": "95mm"},
        "image_url": None
    },
    {
        "spare_part_name": "lough lamp / riverse lar",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Rear work lamp and reverse light assembly for field visibility.",
        "category": "electrical and light system parts",
        "diameter": None,
        "material": "plastic housing and glass lens",
        "price": 2550,
        "lifespan_hr": 1600,
        "specs_json": {"type": "lamp assembly", "voltage": "12V", "rear_mount": True},
        "image_url": None
    },
    {
        "spare_part_name": "presure plate spring",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Spring in clutch pressure plate assembly maintaining clamping force.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "spring steel",
        "price": 1450,
        "lifespan_hr": 3600,
        "specs_json": {"type": "clutch spring", "assembly": "pressure plate", "heat_treated": True},
        "image_url": None
    },
    {
        "spare_part_name": "pto seal",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Power take-off shaft seal preventing transmission oil leakage.",
        "category": "seals/orings/gaskets",
        "diameter": 38.0,
        "material": "nitrile rubber",
        "price": 1180,
        "lifespan_hr": 2500,
        "specs_json": {"type": "shaft seal", "position": "PTO", "oil_resistant": True},
        "image_url": None
    },
    {
        "spare_part_name": "riverse wheel",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Reverse gear wheel in gearbox enabling backward drive motion.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "alloy steel",
        "price": 9100,
        "lifespan_hr": 5100,
        "specs_json": {"type": "reverse gear", "gearbox_part": True, "hardened": True},
        "image_url": None
    },
    {
        "spare_part_name": "valve guide",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Valve guide sleeve maintaining proper valve stem alignment.",
        "category": "engine",
        "diameter": 11.0,
        "material": "cast iron",
        "price": 980,
        "lifespan_hr": 3900,
        "specs_json": {"type": "valve guide", "top_end_part": True, "wear_surface": "machined"},
        "image_url": None
    },
    {
        "spare_part_name": "cylinder head",
        "brand": "Kubota",
        "machine_model": "kubota 4508",
        "description": "Complete cylinder head assembly for engine combustion chamber sealing and valve support.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 28500,
        "lifespan_hr": 8200,
        "specs_json": {"type": "cylinder head", "complete_unit": True, "cooling": "water cooled"},
        "image_url": None
    }
]

tafe_7250_parts = [
    {
        "spare_part_name": "Bearing Set",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Bearing set supporting rotating parts in wheel or transmission assemblies.",
        "category": "bearing",
        "diameter": 48.0,
        "material": "hardened steel",
        "price": 9000,
        "lifespan_hr": 4250,
        "specs_json": {
            "type": "bearing set",
            "system": "rotating support",
            "grease_lubricated": True,
            "function": "supports rotating shafts and reduces friction"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Center Beam",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Central structural beam used in chassis support.",
        "category": "body and structural parts",
        "diameter": None,
        "material": "mild steel",
        "price": 19200,
        "lifespan_hr": 10100,
        "specs_json": {
            "type": "center beam",
            "system": "body and structural",
            "heavy_section": True,
            "function": "supports frame structure"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Center Pin Bush",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Center pivot bush for front axle movement.",
        "category": "steering and front axel parts",
        "diameter": 31.0,
        "material": "bronze alloy",
        "price": 2350,
        "lifespan_hr": 3250,
        "specs_json": {
            "type": "center pin bush",
            "system": "steering and front axle",
            "lubricated": True,
            "function": "reduces pivot wear"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Clutch Finger",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Finger lever in clutch release system.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "forged steel",
        "price": 2600,
        "lifespan_hr": 3450,
        "specs_json": {
            "type": "clutch finger",
            "system": "clutch",
            "heat_treated": True,
            "function": "transfers clutch release force"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Connecting Rod",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Connecting rod joining piston and crankshaft.",
        "category": "engine",
        "diameter": None,
        "material": "forged steel",
        "price": 9950,
        "lifespan_hr": 6250,
        "specs_json": {
            "type": "connecting rod",
            "system": "engine bottom end",
            "balanced": True,
            "function": "transfers piston force to crankshaft"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Crank Oil Seal",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Oil seal fitted at crankshaft end to prevent engine oil leakage.",
        "category": "seals/orings/gaskets",
        "diameter": 54.0,
        "material": "nitrile rubber",
        "price": 1300,
        "lifespan_hr": 2650,
        "specs_json": {
            "type": "crankshaft oil seal",
            "system": "engine sealing",
            "oil_resistant": True,
            "function": "prevents engine oil leakage"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head 3",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Cylinder head component housing combustion chamber and valve passages.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 29000,
        "lifespan_hr": 8150,
        "specs_json": {
            "type": "cylinder head section",
            "system": "engine top end",
            "cooling": "water cooled",
            "function": "supports valves and combustion sealing"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Liner",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Replaceable liner inside engine cylinder.",
        "category": "engine",
        "diameter": 96.0,
        "material": "alloy cast iron",
        "price": 8050,
        "lifespan_hr": 5300,
        "specs_json": {
            "type": "cylinder liner",
            "system": "engine cylinder",
            "surface_finish": "honed",
            "function": "provides wear-resistant cylinder surface"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Diesel Filter Set",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Complete diesel filter replacement set for service use.",
        "category": "fuel system",
        "diameter": None,
        "material": "steel and cellulose filter media",
        "price": 3250,
        "lifespan_hr": 400,
        "specs_json": {
            "type": "fuel filter set",
            "system": "fuel system",
            "includes": ["element", "seal"],
            "function": "service replacement kit"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Engine Valve Exhaust",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Exhaust valve for releasing burned gases from engine cylinder.",
        "category": "engine",
        "diameter": 8.0,
        "material": "heat resistant alloy steel",
        "price": 2050,
        "lifespan_hr": 4150,
        "specs_json": {
            "type": "exhaust valve",
            "system": "engine top end",
            "heat_treated": True,
            "function": "controls exhaust gas outlet"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Head Gasket",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Engine head gasket sealing block and cylinder head surfaces.",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "multi-layer steel composite",
        "price": 3700,
        "lifespan_hr": 3250,
        "specs_json": {
            "type": "head gasket",
            "system": "engine top end",
            "heat_resistant": True,
            "function": "seals compression, oil, and coolant"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Hydraulic Control Valve",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Hydraulic control valve regulating rear linkage oil flow.",
        "category": "Hydralic",
        "diameter": None,
        "material": "cast iron and steel",
        "price": 12500,
        "lifespan_hr": 5050,
        "specs_json": {
            "type": "hydraulic control valve",
            "system": "hydraulic",
            "flow_control": True,
            "function": "controls hydraulic oil direction and pressure"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Hydraulic O-ring Kit",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "O-ring kit used for sealing hydraulic joints and passages.",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "nitrile rubber",
        "price": 1700,
        "lifespan_hr": 2150,
        "specs_json": {
            "type": "hydraulic o-ring kit",
            "system": "hydraulic sealing",
            "oil_resistant": True,
            "function": "prevents hydraulic oil leakage"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Hydraulic Safety Valve",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Relief valve protecting hydraulic system from excess pressure.",
        "category": "Hydralic",
        "diameter": None,
        "material": "steel",
        "price": 6650,
        "lifespan_hr": 5000,
        "specs_json": {
            "type": "hydraulic safety valve",
            "system": "hydraulic",
            "pressure_relief": True,
            "function": "protects hydraulic components from overpressure"
        },
        "image_url": None
    },
    {
        "spare_part_name": "King Pin Bush",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Bush for king pin steering pivot support.",
        "category": "steering and front axel parts",
        "diameter": 28.0,
        "material": "bronze",
        "price": 1800,
        "lifespan_hr": 3150,
        "specs_json": {
            "type": "king pin bush",
            "system": "steering and front axle",
            "lubricated": True,
            "function": "supports steering pivot movement"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Lift Arm",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Rear hydraulic lift arm for raising and lowering implements.",
        "category": "Hydralic",
        "diameter": None,
        "material": "forged steel",
        "price": 15400,
        "lifespan_hr": 7050,
        "specs_json": {
            "type": "lift arm",
            "system": "hydraulic linkage",
            "mounting": "3-point linkage",
            "function": "raises and lowers attached implements"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Pinion Gear",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Pinion gear used in transmission gear train.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "alloy steel",
        "price": 7450,
        "lifespan_hr": 5150,
        "specs_json": {
            "type": "pinion gear",
            "system": "transmission",
            "hardened": True,
            "function": "transfers torque through gear mesh"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Pinion Pilot Racer",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Pilot race supporting pinion shaft alignment.",
        "category": "bearing",
        "diameter": 35.0,
        "material": "hardened steel",
        "price": 2650,
        "lifespan_hr": 3650,
        "specs_json": {
            "type": "pilot race",
            "system": "transmission / differential",
            "precision_ground": True,
            "function": "supports pinion shaft rotation"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Diesel engine piston for power transfer in combustion cycle.",
        "category": "engine",
        "diameter": 96.0,
        "material": "aluminium alloy",
        "price": 7000,
        "lifespan_hr": 5250,
        "specs_json": {
            "type": "piston",
            "system": "engine combustion",
            "weight_grade": "standard",
            "function": "transfers combustion pressure to connecting rod"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston Ring Set",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Piston ring set used for compression sealing and oil control.",
        "category": "engine",
        "diameter": 96.0,
        "material": "alloy cast iron",
        "price": 3350,
        "lifespan_hr": 3150,
        "specs_json": {
            "type": "piston ring set",
            "system": "engine combustion",
            "oil_control": True,
            "function": "seals combustion and regulates lubrication oil"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Rear Work / Reverse Lamp",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Rear reverse and work lamp assembly.",
        "category": "electrical and light system parts",
        "diameter": None,
        "material": "plastic housing and glass lens",
        "price": 2450,
        "lifespan_hr": 1550,
        "specs_json": {
            "type": "rear lamp assembly",
            "system": "electrical and lighting",
            "voltage": "12V",
            "function": "provides rear work and reverse light"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Pressure Plate Spring",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Clutch pressure spring maintaining engagement load.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "spring steel",
        "price": 1420,
        "lifespan_hr": 3600,
        "specs_json": {
            "type": "pressure plate spring",
            "system": "clutch",
            "heat_treated": True,
            "function": "provides clutch clamping force"
        },
        "image_url": None
    },
    {
        "spare_part_name": "PTO Seal",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Seal for PTO shaft to prevent gearbox oil leakage.",
        "category": "seals/orings/gaskets",
        "diameter": 39.0,
        "material": "nitrile rubber",
        "price": 1150,
        "lifespan_hr": 2520,
        "specs_json": {
            "type": "pto seal",
            "system": "transmission sealing",
            "oil_resistant": True,
            "function": "prevents PTO oil leakage"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Reverse Gear Wheel",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Gear wheel used for reverse transmission motion.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "alloy steel",
        "price": 8900,
        "lifespan_hr": 5050,
        "specs_json": {
            "type": "reverse gear wheel",
            "system": "transmission",
            "case_hardened": True,
            "function": "enables reverse motion"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Valve Guide",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Valve guide used to align valve stem inside cylinder head.",
        "category": "engine",
        "diameter": 11.5,
        "material": "cast iron",
        "price": 950,
        "lifespan_hr": 3980,
        "specs_json": {
            "type": "valve guide",
            "system": "engine top end",
            "machined_surface": True,
            "function": "guides valve stem accurately"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head",
        "brand": "tafe",
        "machine_model": "TAFE 7250",
        "description": "Complete cylinder head assembly for tractor diesel engine.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 27800,
        "lifespan_hr": 8150,
        "specs_json": {
            "type": "cylinder head",
            "system": "engine top end",
            "complete_unit": True,
            "function": "houses valves and seals combustion chamber"
        },
        "image_url": None
    }
]

tafe_45di_parts = [
    {
        "spare_part_name": "Clutch Finger",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Release finger used in clutch pressure plate assembly.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "forged steel",
        "price": 2580,
        "lifespan_hr": 3480,
        "specs_json": {
            "type": "clutch finger",
            "system": "clutch",
            "heat_treated": True,
            "function": "transfers clutch release movement"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Connecting Rod",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Connecting rod linking piston and crankshaft.",
        "category": "engine",
        "diameter": None,
        "material": "forged steel",
        "price": 9850,
        "lifespan_hr": 6280,
        "specs_json": {
            "type": "connecting rod",
            "system": "engine bottom end",
            "balanced": True,
            "function": "transfers piston force to crankshaft"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head 3",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Cylinder head unit supporting valves and combustion chamber.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 28800,
        "lifespan_hr": 8120,
        "specs_json": {
            "type": "cylinder head section",
            "system": "engine top end",
            "cooling": "water cooled",
            "function": "supports combustion sealing and valve seating"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Liner",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Replaceable liner forming piston sliding surface inside cylinder.",
        "category": "engine",
        "diameter": 97.0,
        "material": "alloy cast iron",
        "price": 8150,
        "lifespan_hr": 5350,
        "specs_json": {
            "type": "cylinder liner",
            "system": "engine cylinder",
            "surface_finish": "honed",
            "function": "provides wear-resistant liner surface"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Diesel Filter Set",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Complete service set for diesel fuel filtration.",
        "category": "fuel system",
        "diameter": None,
        "material": "steel and cellulose filter media",
        "price": 3220,
        "lifespan_hr": 400,
        "specs_json": {
            "type": "fuel filter set",
            "system": "fuel system",
            "includes": ["filter element", "seal"],
            "function": "service replacement kit for filtration"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Engine Valve Exhaust",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Exhaust valve allowing combustion gases to exit cylinder.",
        "category": "engine",
        "diameter": 8.2,
        "material": "heat resistant alloy steel",
        "price": 2080,
        "lifespan_hr": 4180,
        "specs_json": {
            "type": "exhaust valve",
            "system": "engine top end",
            "heat_treated": True,
            "function": "controls exhaust gas outlet"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Engine piston converting combustion energy into mechanical motion.",
        "category": "engine",
        "diameter": 97.0,
        "material": "aluminium alloy",
        "price": 7050,
        "lifespan_hr": 5280,
        "specs_json": {
            "type": "piston",
            "system": "engine combustion",
            "weight_grade": "standard",
            "function": "transfers combustion pressure"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston Ring Set",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Set of rings used for compression sealing and oil scraping.",
        "category": "engine",
        "diameter": 97.0,
        "material": "alloy cast iron",
        "price": 3380,
        "lifespan_hr": 3180,
        "specs_json": {
            "type": "piston ring set",
            "system": "engine combustion",
            "oil_control": True,
            "function": "seals combustion and controls oil film"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Rear Work / Reverse Lamp",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Rear lamp assembly for work light and reverse indication.",
        "category": "electrical and light system parts",
        "diameter": None,
        "material": "plastic housing and glass lens",
        "price": 2420,
        "lifespan_hr": 1540,
        "specs_json": {
            "type": "rear lamp assembly",
            "system": "electrical and lighting",
            "voltage": "12V",
            "function": "provides rear work and reverse lighting"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Pressure Plate Spring",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Spring used in clutch pressure plate to maintain clamping force.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "spring steel",
        "price": 1400,
        "lifespan_hr": 3580,
        "specs_json": {
            "type": "pressure plate spring",
            "system": "clutch",
            "heat_treated": True,
            "function": "maintains clutch pressure load"
        },
        "image_url": None
    },
    {
        "spare_part_name": "PTO Seal",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Seal preventing transmission oil leakage from PTO shaft.",
        "category": "seals/orings/gaskets",
        "diameter": 39.5,
        "material": "nitrile rubber",
        "price": 1160,
        "lifespan_hr": 2530,
        "specs_json": {
            "type": "pto seal",
            "system": "transmission sealing",
            "oil_resistant": True,
            "function": "prevents oil leakage at PTO shaft"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Valve Guide",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Guide sleeve controlling valve stem alignment and movement.",
        "category": "engine",
        "diameter": 11.8,
        "material": "cast iron",
        "price": 940,
        "lifespan_hr": 3990,
        "specs_json": {
            "type": "valve guide",
            "system": "engine top end",
            "machined_surface": True,
            "function": "guides valve stem movement"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head",
        "brand": "tafe",
        "machine_model": "TAFE 45DI",
        "description": "Complete cylinder head assembly for diesel tractor engine.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 27600,
        "lifespan_hr": 8120,
        "specs_json": {
            "type": "cylinder head",
            "system": "engine top end",
            "complete_unit": True,
            "function": "houses valves and seals combustion chamber"
        },
        "image_url": None
    }
]

mf_240_parts = [
    {
        "spare_part_name": "Clutch Finger",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Clutch release finger used in pressure plate assembly to transfer release force.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "forged steel",
        "price": 2500,
        "lifespan_hr": 3500,
        "specs_json": {
            "type": "clutch finger",
            "system": "clutch",
            "heat_treated": True,
            "function": "transfers clutch release force"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Connecting Rod",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Connecting rod linking piston to crankshaft in the engine.",
        "category": "engine",
        "diameter": None,
        "material": "forged steel",
        "price": 9700,
        "lifespan_hr": 6300,
        "specs_json": {
            "type": "connecting rod",
            "system": "engine bottom end",
            "balanced": True,
            "function": "transfers combustion force from piston to crankshaft"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head 3",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Cylinder head section housing combustion chamber and valve passages.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 28200,
        "lifespan_hr": 8100,
        "specs_json": {
            "type": "cylinder head section",
            "system": "engine top end",
            "cooling": "water cooled",
            "function": "supports valves and seals combustion chamber"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Liner",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Replaceable liner providing piston sliding surface inside engine block.",
        "category": "engine",
        "diameter": 98.0,
        "material": "alloy cast iron",
        "price": 7900,
        "lifespan_hr": 5400,
        "specs_json": {
            "type": "cylinder liner",
            "system": "engine cylinder",
            "surface_finish": "honed",
            "function": "provides wear-resistant cylinder wall"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Diesel Filter Set",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Complete service set for diesel filtration maintenance.",
        "category": "fuel system",
        "diameter": None,
        "material": "steel and filter media",
        "price": 3150,
        "lifespan_hr": 400,
        "specs_json": {
            "type": "fuel filter set",
            "system": "fuel system",
            "includes": ["filter element", "seal"],
            "function": "complete filter replacement kit"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Engine Valve Exhaust",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Exhaust valve used to release burned gases from engine cylinder.",
        "category": "engine",
        "diameter": 8.5,
        "material": "heat resistant steel",
        "price": 2000,
        "lifespan_hr": 4200,
        "specs_json": {
            "type": "exhaust valve",
            "system": "engine top end",
            "heat_treated": True,
            "function": "controls exhaust gas flow"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Head Gasket",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Gasket sealing the cylinder head and engine block.",
        "category": "seals/orings/gaskets",
        "diameter": None,
        "material": "graphite composite steel",
        "price": 3600,
        "lifespan_hr": 3200,
        "specs_json": {
            "type": "head gasket",
            "system": "engine top end",
            "heat_resistant": True,
            "function": "seals compression, oil, and coolant passages"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Diesel engine piston converting combustion pressure into motion.",
        "category": "engine",
        "diameter": 98.0,
        "material": "aluminium alloy",
        "price": 6900,
        "lifespan_hr": 5300,
        "specs_json": {
            "type": "piston",
            "system": "engine combustion",
            "weight_grade": "standard",
            "function": "transfers combustion pressure to connecting rod"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Piston Ring Set",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Set of piston rings for compression sealing and oil control.",
        "category": "engine",
        "diameter": 98.0,
        "material": "alloy cast iron",
        "price": 3300,
        "lifespan_hr": 3200,
        "specs_json": {
            "type": "piston ring set",
            "system": "engine combustion",
            "includes": ["compression ring", "oil ring"],
            "function": "seals combustion and regulates oil"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Rear Work / Reverse Lamp",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Rear light assembly providing work light and reverse indication.",
        "category": "electrical and light system parts",
        "diameter": None,
        "material": "plastic and glass",
        "price": 2350,
        "lifespan_hr": 1500,
        "specs_json": {
            "type": "rear lamp assembly",
            "system": "electrical and lighting",
            "voltage": "12V",
            "function": "provides rear illumination and reverse lighting"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Pressure Plate Spring",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Spring in clutch pressure plate providing clamping force.",
        "category": "transmition and gear box parts",
        "diameter": None,
        "material": "spring steel",
        "price": 1380,
        "lifespan_hr": 3550,
        "specs_json": {
            "type": "pressure plate spring",
            "system": "clutch",
            "heat_treated": True,
            "function": "maintains clutch engagement force"
        },
        "image_url": None
    },
    {
        "spare_part_name": "PTO Seal",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Seal for PTO shaft preventing transmission oil leakage.",
        "category": "seals/orings/gaskets",
        "diameter": 40.0,
        "material": "nitrile rubber",
        "price": 1120,
        "lifespan_hr": 2550,
        "specs_json": {
            "type": "pto shaft seal",
            "system": "transmission sealing",
            "oil_resistant": True,
            "function": "prevents oil leakage at PTO shaft"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Valve Guide",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Guide sleeve maintaining proper valve stem alignment.",
        "category": "engine",
        "diameter": 12.0,
        "material": "cast iron",
        "price": 920,
        "lifespan_hr": 4000,
        "specs_json": {
            "type": "valve guide",
            "system": "engine top end",
            "machined_surface": True,
            "function": "guides valve stem movement"
        },
        "image_url": None
    },
    {
        "spare_part_name": "Cylinder Head",
        "brand": "mf",
        "machine_model": "MF 240",
        "description": "Complete cylinder head assembly for diesel engine.",
        "category": "engine",
        "diameter": None,
        "material": "cast iron",
        "price": 27200,
        "lifespan_hr": 8100,
        "specs_json": {
            "type": "cylinder head",
            "system": "engine top end",
            "complete_unit": True,
            "function": "houses valves and seals combustion chamber"
        },
        "image_url": None
    }
]


ALL_PARTS = (
    kubota_4508_parts
    + tafe_7250_parts
    + tafe_45di_parts
    + mf_240_parts
)


def create_part_object(item: dict) -> Part:
    return Part(
        name=item["spare_part_name"],
        brand=item["brand"],
        category=item["category"],
        diameter=item["diameter"],
        material=item["material"],
        price=float(item["price"]),
        lifespan=int(item["lifespan_hr"]),
        machine_model=item["machine_model"],
        description=item["description"],
        specs_json=item["specs_json"],
        image_url=item["image_url"],
    )


def seed_parts():
    db: Session = SessionLocal()
    try:
        print("Deleting existing parts data...")
        db.query(Part).delete()
        db.commit()

        print("Creating new part records...")
        part_objects = [create_part_object(item) for item in ALL_PARTS]

        db.add_all(part_objects)
        db.commit()

        print(f"✅ Successfully inserted {len(part_objects)} parts into the database.")

    except Exception as e:
        db.rollback()
        print("❌ Error while seeding parts:")
        print(str(e))

    finally:
        db.close()


if __name__ == "__main__":
    seed_parts()