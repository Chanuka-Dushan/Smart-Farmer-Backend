from database import SessionLocal
from models import Part

db = SessionLocal()

parts = [

    # ---------------- ENGINE / FUEL SYSTEM ----------------
    Part(name="Oil Filter", brand="TAFE 45 DI", category="engine",
         diameter=80, material="Steel + Filter Media", price=4000, lifespan=12),

    Part(name="Fuel Filter", brand="TAFE 45 DI", category="fuel system",
         diameter=50, material="Metal + Filter Media", price=2500, lifespan=18),

    Part(name="Oil Filter", brand="TAFE 7250", category="engine",
         diameter=85, material="Steel + Filter Media", price=5000, lifespan=12),

    Part(name="Fuel Filter", brand="TAFE 7250", category="fuel system",
         diameter=55, material="Metal + Filter Media", price=3000, lifespan=18),

    Part(name="Oil Filter", brand="MF 240", category="engine",
         diameter=82, material="Steel + Filter Media", price=4500, lifespan=12),

    Part(name="Fuel Filter", brand="MF 240", category="fuel system",
         diameter=60, material="Metal + Filter Media", price=2800, lifespan=18),

    # ---------------- BEARINGS ----------------
    Part(name="Front Hub Bearing Inner", brand="TAFE 45 DI", category="bearing",
         diameter=90, material="Hardened Steel", price=12000, lifespan=48),

    Part(name="Front Hub Bearing Outer", brand="TAFE 7250", category="bearing",
         diameter=95, material="Hardened Steel", price=15000, lifespan=48),

    Part(name="Pinion Pilot Racer", brand="MF 240", category="bearing",
         diameter=70, material="Bearing Steel", price=10000, lifespan=60),

    Part(name="Front Hub Racer Inner", brand="MF 240", category="bearing",
         diameter=88, material="Bearing Steel", price=14000, lifespan=60),

    # ---------------- SEALS / GASKETS ----------------
    Part(name="Head Gasket", brand="TAFE 45 DI", category="seals/orings/gaskets",
         diameter=None, material="Multi-Layer Steel", price=35000, lifespan=120),

    Part(name="Front Hub Grease Seal", brand="TAFE 45 DI", category="seals/orings/gaskets",
         diameter=60, material="Rubber + Steel", price=2500, lifespan=36),

    Part(name="Crank Oil Seal (Rear)", brand="MF 240", category="seals/orings/gaskets",
         diameter=75, material="Viton Rubber", price=5000, lifespan=60),

    Part(name="Hydraulic Pump O-Ring Kit", brand="MF 240", category="seals/orings/gaskets",
         diameter=None, material="Nitrile Rubber", price=8000, lifespan=24),

    # ---------------- STEERING & FRONT AXLE ----------------
    Part(name="Front Axle Assembly", brand="TAFE 45 DI", category="steering and front axel parts",
         diameter=None, material="Forged Steel", price=180000, lifespan=180),

    Part(name="Front Center Beam", brand="TAFE 45 DI", category="steering and front axel parts",
         diameter=None, material="Steel Beam", price=85000, lifespan=180),

    Part(name="Center Pin Bush", brand="MF 240", category="steering and front axel parts",
         diameter=40, material="Bronze", price=6000, lifespan=36),

    Part(name="King Pin Bush", brand="MF 240", category="steering and front axel parts",
         diameter=35, material="Bronze", price=8000, lifespan=36),

    # ---------------- TRANSMISSION / GEARBOX ----------------
    Part(name="Crown Wheel & Pinion Assembly", brand="TAFE 45 DI",
         category="transmission and gear box parts",
         diameter=None, material="Hardened Alloy Steel", price=180000, lifespan=240),

    Part(name="Reverse Gear Wheel", brand="TAFE 45 DI",
         category="transmission and gear box parts",
         diameter=None, material="Hardened Steel", price=45000, lifespan=200),

    Part(name="Top Cover (Gearbox)", brand="MF 240",
         category="transmission and gear box parts",
         diameter=None, material="Cast Iron", price=25000, lifespan=200),

    # ---------------- HYDRAULIC ----------------
    Part(name="Hydraulic Control Valve", brand="TAFE 45 DI",
         category="hydraulic",
         diameter=None, material="Cast Iron", price=90000, lifespan=120),

    Part(name="Hydraulic Safety Valve", brand="TAFE 45 DI",
         category="hydraulic",
         diameter=None, material="Steel", price=12000, lifespan=96),

    Part(name="Lift Arm", brand="MF 240",
         category="hydraulic",
         diameter=None, material="Forged Steel", price=40000, lifespan=120),

    Part(name="Bell Cam", brand="MF 240",
         category="hydraulic",
         diameter=None, material="Steel", price=15000, lifespan=120),

    Part(name="Lift Shaft", brand="MF 240",
         category="hydraulic",
         diameter=None, material="Hardened Steel", price=60000, lifespan=180),
]

db.add_all(parts)
db.commit()
db.close()

print("✅ Real tractor spare parts seeded successfully")
