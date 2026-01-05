from main import Part
from init_db import SessionLocal

db = SessionLocal()

parts = [

# ==================================================
# TAFE 45 DI – ENGINE / FUEL (5)
# ==================================================
Part(name="Oil Filter", brand="TAFE", description="Engine oil filter", category="engine",
     diameter=80, material="Steel + filter media", price=4500, lifespan=250, image_url=None),

Part(name="Fuel Filter", brand="TAFE", description="Diesel fuel filter", category="fuel system",
     diameter=50, material="Metal + paper", price=3000, lifespan=400, image_url=None),

Part(name="Air Filter", brand="TAFE", description="Engine air intake filter", category="engine",
     diameter=120, material="Plastic + paper", price=6500, lifespan=500, image_url=None),

Part(name="Head Gasket", brand="TAFE", description="Cylinder head gasket",
     category="seals/orings/gaskets", diameter=None, material="Multi-layer steel",
     price=35000, lifespan=8000, image_url=None),

Part(name="Crank Oil Seal (Rear)", brand="Generic", description="Rear crankshaft oil seal",
     category="seals/orings/gaskets", diameter=None, material="Rubber + steel",
     price=5000, lifespan=6000, image_url=None),

# ==================================================
# TAFE 45 DI – BEARINGS (3)
# ==================================================
Part(name="Front Hub Bearing Inner", brand="SKF", description="Inner front hub bearing",
     category="bearing", diameter=90, material="Hardened steel",
     price=18000, lifespan=3000, image_url=None),

Part(name="Front Hub Bearing Outer", brand="SKF", description="Outer front hub bearing",
     category="bearing", diameter=100, material="Hardened steel",
     price=22000, lifespan=3000, image_url=None),

Part(name="Pinion Pilot Racer", brand="Generic", description="Pinion pilot bearing race",
     category="bearing", diameter=60, material="Bearing steel",
     price=12000, lifespan=4000, image_url=None),

# ==================================================
# TAFE 45 DI – STEERING / AXLE (4)
# ==================================================
Part(name="Front Axle", brand="TAFE", description="Front axle assembly",
     category="steering and front axel parts", diameter=None, material="Forged steel",
     price=180000, lifespan=12000, image_url=None),

Part(name="Front Center Beam", brand="TAFE", description="Front axle center beam",
     category="steering and front axel parts", diameter=None, material="Steel",
     price=85000, lifespan=10000, image_url=None),

Part(name="Center Pin Bush", brand="Generic", description="Center pin bush",
     category="steering and front axel parts", diameter=40, material="Bronze",
     price=3500, lifespan=3000, image_url=None),

Part(name="King Pin Bush", brand="Generic", description="King pin steering bush",
     category="steering and front axel parts", diameter=35, material="Bronze",
     price=6000, lifespan=3500, image_url=None),

# ==================================================
# TAFE 45 DI – TRANSMISSION (3)
# ==================================================
Part(name="Crown Wheel & Pinion Assembly", brand="TAFE",
     description="Differential gear set",
     category="transmission and gear box parts", diameter=None,
     material="Hardened alloy steel", price=180000, lifespan=12000, image_url=None),

Part(name="Reverse Gear Wheel", brand="TAFE",
     description="Reverse gear for gearbox",
     category="transmission and gear box parts", diameter=None,
     material="Hardened steel", price=45000, lifespan=9000, image_url=None),

Part(name="Top Cover", brand="TAFE", description="Gearbox top cover",
     category="transmission and gear box parts", diameter=None,
     material="Cast iron", price=30000, lifespan=10000, image_url=None),

# ==================================================
# TAFE 45 DI – HYDRAULIC (6)
# ==================================================
Part(name="Hydraulic Control Valve", brand="TAFE",
     description="Hydraulic spool valve", category="hydraulic",
     diameter=None, material="Cast iron", price=85000, lifespan=7000, image_url=None),

Part(name="Hydraulic Safety Valve", brand="Generic",
     description="Hydraulic pressure relief valve", category="hydraulic",
     diameter=None, material="Steel", price=12000, lifespan=6000, image_url=None),

Part(name="Hydraulic Pump O-ring Kit", brand="Generic",
     description="Hydraulic pump seal kit", category="seals/orings/gaskets",
     diameter=None, material="Rubber", price=6000, lifespan=2000, image_url=None),

Part(name="Lift Arm", brand="TAFE", description="3-point hitch lift arm",
     category="hydraulic", diameter=None, material="Forged steel",
     price=42000, lifespan=9000, image_url=None),

Part(name="Bell Cam", brand="TAFE", description="Hydraulic bell cam",
     category="hydraulic", diameter=None, material="Steel",
     price=15000, lifespan=8000, image_url=None),

Part(name="Lift Shaft", brand="TAFE", description="Lift mechanism shaft",
     category="hydraulic", diameter=None, material="Hardened steel",
     price=60000, lifespan=10000, image_url=None),

# ==================================================
# TAFE 7250 – ENGINE / FUEL (2)
# ==================================================
Part(name="Oil Filter", brand="TAFE", description="Oil filter for TAFE 7250",
     category="engine", diameter=85, material="Steel + media",
     price=5500, lifespan=300, image_url=None),

Part(name="Fuel Filter", brand="TAFE", description="Fuel filter for TAFE 7250",
     category="fuel system", diameter=55, material="Metal + paper",
     price=3800, lifespan=450, image_url=None),

# ==================================================
# TAFE 7250 – BEARINGS (2)
# ==================================================
Part(name="Front Hub Bearing Inner", brand="SKF",
     description="Front hub inner bearing", category="bearing",
     diameter=95, material="Hardened steel",
     price=20000, lifespan=3200, image_url=None),

Part(name="Front Hub Bearing Outer", brand="SKF",
     description="Front hub outer bearing", category="bearing",
     diameter=105, material="Hardened steel",
     price=24000, lifespan=3200, image_url=None),

# ==================================================
# MF 240 – ENGINE / FUEL (2)
# ==================================================
Part(name="Oil Filter", brand="AGCO", description="Oil filter for MF 240",
     category="engine", diameter=90, material="Steel + media",
     price=5000, lifespan=300, image_url=None),

Part(name="Fuel Filter", brand="AGCO", description="Fuel filter for MF 240",
     category="fuel system", diameter=60, material="Metal + paper",
     price=4000, lifespan=450, image_url=None),

# ==================================================
# MF 240 – BEARINGS / SEALS (3)
# ==================================================
Part(name="Front Hub Bearing Inner", brand="SKF",
     description="MF 240 inner hub bearing", category="bearing",
     diameter=88, material="Hardened steel",
     price=19000, lifespan=3000, image_url=None),

Part(name="Front Hub Grease Seal", brand="Generic",
     description="Hub grease seal", category="seals/orings/gaskets",
     diameter=None, material="Rubber + steel",
     price=2800, lifespan=3500, image_url=None),

Part(name="Crank Oil Seal", brand="Generic",
     description="Crankshaft oil seal", category="seals/orings/gaskets",
     diameter=None, material="Rubber + steel",
     price=4500, lifespan=6000, image_url=None),

# ==================================================
# MF 240 – TRANSMISSION (2)
# ==================================================
Part(name="Crown Wheel & Pinion", brand="AGCO",
     description="Differential crown & pinion",
     category="transmission and gear box parts",
     diameter=None, material="Hardened steel",
     price=165000, lifespan=11000, image_url=None),

Part(name="Reverse Gear", brand="AGCO",
     description="Reverse gear wheel",
     category="transmission and gear box parts",
     diameter=None, material="Hardened steel",
     price=42000, lifespan=9000, image_url=None),
]

db.add_all(parts)
db.commit()
db.close()

print("✅ 47 tractor spare parts seeded successfully")
