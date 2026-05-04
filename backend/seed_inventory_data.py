import os
import random
from dotenv import load_dotenv
from sqlalchemy import create_engine
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

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_inventory_data():
    db = SessionLocal()

    try:
        if db.query(InventorySeason).count() > 0:
            print("Inventory data already exists. Skipping seed.")
            return

        # 1. Seasons
        db.add_all([
            InventorySeason(id=1, name="Maha", start_month="September", end_month="March"),
            InventorySeason(id=2, name="Yala", start_month="April", end_month="August"),
        ])

        # 2. Stages
        db.add_all([
            InventoryStage(id=1, name="Land Ploughing", sinhala_name="කුඹුර කොටනවා"),
            InventoryStage(id=2, name="Harrowing", sinhala_name="හානවා"),
            InventoryStage(id=3, name="Puddling", sinhala_name="මඩ කරනවා"),
            InventoryStage(id=4, name="Sowing", sinhala_name="වී ඉහිනවා"),
            InventoryStage(id=5, name="Harvesting", sinhala_name="ගොයම් කපනවා"),
        ])

        # 3. Categories
        db.add_all([
            InventoryMachineCategory(id=1, name="Tractor"),
            InventoryMachineCategory(id=2, name="Rotavator"),
            InventoryMachineCategory(id=3, name="Power Tiller"),
            InventoryMachineCategory(id=4, name="Seeder"),
            InventoryMachineCategory(id=5, name="Sprayer"),
            InventoryMachineCategory(id=6, name="Combine Harvester"),
        ])

        # 4. Brands
        db.add_all([
            InventoryBrand(id=1, name="TAFE", category_id=1),
            InventoryBrand(id=2, name="Kubota", category_id=1),
            InventoryBrand(id=3, name="Massey Ferguson", category_id=1),
            InventoryBrand(id=4, name="Mahindra", category_id=1),
            InventoryBrand(id=5, name="Fieldking", category_id=2),
            InventoryBrand(id=6, name="Yanmar", category_id=6),
            InventoryBrand(id=7, name="Generic Seeder", category_id=4),
            InventoryBrand(id=8, name="Generic Sprayer", category_id=5),
        ])

        # 5. Models
        db.add_all([
            InventoryMachineModel(id=1, brand_id=1, category_id=1, model_name="TAFE 45 DI"),
            InventoryMachineModel(id=2, brand_id=1, category_id=1, model_name="TAFE 7250"),
            InventoryMachineModel(id=3, brand_id=2, category_id=1, model_name="Kubota L4508"),
            InventoryMachineModel(id=4, brand_id=2, category_id=1, model_name="Kubota MU4501"),
            InventoryMachineModel(id=5, brand_id=3, category_id=1, model_name="MF 240"),
            InventoryMachineModel(id=6, brand_id=3, category_id=1, model_name="MF 260"),
            InventoryMachineModel(id=7, brand_id=4, category_id=1, model_name="Mahindra 575 DI"),
            InventoryMachineModel(id=8, brand_id=4, category_id=1, model_name="Mahindra 265 DI"),
            InventoryMachineModel(id=9, brand_id=5, category_id=2, model_name="Fieldking 6ft Rotavator"),
            InventoryMachineModel(id=10, brand_id=2, category_id=3, model_name="Kubota Power Tiller"),
            InventoryMachineModel(id=11, brand_id=7, category_id=4, model_name="Paddy Seeder"),
            InventoryMachineModel(id=12, brand_id=8, category_id=5, model_name="Knapsack Power Sprayer"),
            InventoryMachineModel(id=13, brand_id=2, category_id=6, model_name="Kubota DC-70"),
            InventoryMachineModel(id=14, brand_id=6, category_id=6, model_name="Yanmar AW70V"),
        ])

        # 6. Parts - 100
        part_names = [
            ("Oil Filter", "Filter"), ("Air Filter", "Filter"), ("Fuel Filter", "Filter"),
            ("Hydraulic Filter", "Filter"), ("Cabin Filter", "Filter"),
            ("Fan Belt", "Belt"), ("Timing Belt", "Belt"), ("Drive Belt", "Belt"),
            ("Alternator Belt", "Belt"), ("Compressor Belt", "Belt"),
            ("Piston Ring", "Engine"), ("Cylinder Liner", "Engine"), ("Head Gasket", "Engine"),
            ("Crankshaft", "Engine"), ("Camshaft", "Engine"), ("Fuel Injector", "Engine"),
            ("Glow Plug", "Engine"), ("Spark Plug", "Engine"),
            ("Clutch Plate", "Transmission"), ("Pressure Plate", "Transmission"),
            ("Gear Shaft", "Transmission"), ("Gear Lever Cable", "Transmission"),
            ("Brake Shoe", "Brake"), ("Brake Disc", "Brake"), ("Brake Pad", "Brake"),
            ("Bearing", "Mechanical"), ("Ball Bearing", "Mechanical"), ("Roller Bearing", "Mechanical"),
            ("Oil Seal", "Seal"), ("Dust Seal", "Seal"),
            ("Hydraulic Pump", "Hydraulic"), ("Hydraulic Hose", "Hydraulic"),
            ("Hydraulic Cylinder", "Hydraulic"), ("Control Valve", "Hydraulic"),
            ("Radiator Hose", "Cooling"), ("Radiator Core", "Cooling"),
            ("Water Pump", "Cooling"), ("Thermostat", "Cooling"),
            ("Battery", "Electrical"), ("Starter Motor", "Electrical"),
            ("Alternator", "Electrical"), ("Wiring Harness", "Electrical"),
            ("Fuse Box", "Electrical"), ("Ignition Switch", "Electrical"),
            ("Rear Tyre", "Tyre"), ("Front Tyre", "Tyre"), ("Tube", "Tyre"),
            ("Rotavator Blade", "Blade"), ("Tine Blade", "Blade"),
            ("Side Gear", "Rotavator"), ("Rotor Shaft", "Rotavator"),
            ("Cutter Blade", "Blade"), ("Feeder Chain", "Harvester"),
            ("Threshing Drum", "Harvester"), ("Concave Screen", "Harvester"),
            ("Straw Walker", "Harvester"), ("Grain Elevator", "Harvester"),
            ("Seed Plate", "Seeder"), ("Seed Tube", "Seeder"),
            ("Metering Device", "Seeder"), ("Seed Hopper", "Seeder"),
            ("Nozzle", "Sprayer"), ("Sprayer Pump", "Sprayer"),
            ("Spray Lance", "Sprayer"), ("Pressure Regulator", "Sprayer"),
            ("Chain", "Drive"), ("Sprocket", "Drive"), ("Pulley", "Drive"),
            ("Universal Joint", "Mechanical"), ("Coupling", "Mechanical"),
            ("Engine Oil", "Lubricant"), ("Gear Oil", "Lubricant"),
            ("Hydraulic Oil", "Lubricant"),
            ("Plough Share", "Tillage"), ("Harrow Disc", "Tillage"),
            ("Cage Wheel", "Paddy Field"),
            ("Air Intake Hose", "Engine"), ("Fuel Pump", "Engine"),
            ("Exhaust Pipe", "Engine"), ("Silencer", "Engine"),
            ("Seat Assembly", "Cabin"), ("Steering Wheel", "Cabin"),
            ("Dashboard Panel", "Cabin"), ("Headlight", "Electrical"),
            ("Indicator Light", "Electrical"), ("Horn", "Electrical"),
            ("Gear Box", "Transmission"), ("Axle Shaft", "Transmission"),
            ("Wheel Hub", "Mechanical"), ("Brake Cylinder", "Brake"),
            ("Clutch Cable", "Transmission"), ("Throttle Cable", "Engine"),
            ("Radiator Cap", "Cooling"), ("Cooling Fan", "Cooling"),
            ("Fuel Tank", "Engine"), ("Oil Pump", "Engine"),
            ("Lift Arm", "Hydraulic"), ("Top Link", "Hydraulic"),
            ("Lower Link", "Hydraulic"), ("Drawbar", "Mechanical"),
            ("Mud Guard", "Body"), ("Bonnet", "Body"),
        ]

        db.add_all([
            InventoryPart(id=i + 1, name=name, part_type=ptype)
            for i, (name, ptype) in enumerate(part_names)
        ])

        db.commit()

        # 7. Model-Part Mappings - 150
        model_specific_parts = {
            1: [1, 2, 3, 6, 19, 23, 26, 29, 31, 35, 39],
            2: [1, 2, 3, 6, 20, 24, 27, 30, 32, 37, 40],
            3: [1, 2, 3, 6, 19, 25, 26, 29, 31, 35, 39, 40],
            4: [1, 4, 6, 8, 19, 20, 26, 31, 32, 37, 41, 45],
            5: [1, 2, 3, 6, 19, 23, 26, 29, 31, 35, 39],
            6: [1, 2, 4, 8, 20, 24, 27, 30, 32, 37, 41, 46],
            7: [1, 2, 3, 6, 19, 23, 26, 29, 31, 35, 39],
            8: [1, 3, 6, 8, 19, 25, 28, 30, 32, 37, 40],
            9: [26, 29, 48, 49, 50, 51, 66, 67, 72, 73, 76],
            10: [1, 2, 3, 6, 26, 29, 39, 40, 48, 49, 76],
            11: [26, 29, 58, 59, 60, 61, 66, 67, 68, 72],
            12: [39, 62, 63, 64, 65, 72, 73, 84, 85],
            13: [1, 2, 3, 8, 26, 29, 52, 53, 54, 55, 56, 57, 66, 67],
            14: [1, 2, 3, 8, 26, 29, 52, 53, 54, 55, 56, 57, 66, 67],
        }

        mappings = []
        existing_pairs = set()

        for model_id, part_ids in model_specific_parts.items():
            for part_id in part_ids:
                existing_pairs.add((model_id, part_id))
                criticality = "HIGH" if part_id in [1, 6, 19, 26, 29, 31, 48, 52, 53, 62, 63] else "MEDIUM"
                mappings.append(
                    InventoryModelPartMapping(
                        model_id=model_id,
                        part_id=part_id,
                        criticality=criticality,
                    )
                )

        random.seed(42)
        while len(mappings) < 150:
            model_id = random.randint(1, 14)
            part_id = random.randint(1, 100)

            if (model_id, part_id) not in existing_pairs:
                existing_pairs.add((model_id, part_id))
                mappings.append(
                    InventoryModelPartMapping(
                        model_id=model_id,
                        part_id=part_id,
                        criticality=random.choice(["LOW", "MEDIUM", "HIGH"]),
                    )
                )

        db.add_all(mappings[:150])
        db.commit()

        # 8. Seasonal Demand Rules - 50
        rule_plan = [
            (1, 1, "HIGH", 20), (1, 2, "HIGH", 20), (1, 3, "MEDIUM", 10), (1, 4, "LOW", 5), (1, 6, "LOW", 5),
            (2, 1, "HIGH", 20), (2, 2, "MEDIUM", 10), (2, 3, "MEDIUM", 10), (2, 5, "LOW", 5), (2, 6, "LOW", 5),
            (3, 1, "HIGH", 20), (3, 2, "HIGH", 20), (3, 3, "HIGH", 20), (3, 5, "LOW", 5), (3, 6, "LOW", 5),
            (4, 1, "MEDIUM", 10), (4, 2, "LOW", 5), (4, 3, "LOW", 5), (4, 4, "HIGH", 20), (4, 5, "MEDIUM", 10),
            (5, 1, "MEDIUM", 10), (5, 2, "LOW", 5), (5, 3, "LOW", 5), (5, 5, "LOW", 5), (5, 6, "VERY_HIGH", 30),
        ]

        rules = []
        for season_id in [1, 2]:
            for stage_id, category_id, level, base in rule_plan:
                # Maha slightly higher for land prep and harvesting
                boost = 5 if season_id == 1 and stage_id in [1, 5] else 0
                rules.append(
                    InventorySeasonalDemandRule(
                        season_id=season_id,
                        stage_id=stage_id,
                        category_id=category_id,
                        demand_level=level,
                        base_demand=base + boost,
                    )
                )

        db.add_all(rules)
        db.commit()

        # 9. Demand History
        months_by_season = {
            1: ["September", "October", "November", "December"],
            2: ["April", "May", "June", "July"],
        }

        histories = []
        selected_mappings = db.query(InventoryModelPartMapping).limit(80).all()

        for mapping in selected_mappings:
            model = db.query(InventoryMachineModel).filter_by(id=mapping.model_id).first()

            for season_id, months in months_by_season.items():
                for month in months:
                    stage_id = random.randint(1, 5)

                    rule = db.query(InventorySeasonalDemandRule).filter_by(
                        season_id=season_id,
                        stage_id=stage_id,
                        category_id=model.category_id,
                    ).first()

                    base = rule.base_demand if rule else 8
                    demand_qty = max(1, base + random.randint(-3, 5))

                    histories.append(
                        InventoryDemandHistory(
                            model_id=mapping.model_id,
                            part_id=mapping.part_id,
                            month=month,
                            season_id=season_id,
                            stage_id=stage_id,
                            demand_quantity=demand_qty,
                        )
                    )

        db.add_all(histories)
        db.commit()

        # 10. Stock Test Records - 50
        stock_records = []
        stock_values = [2, 5, 8, 10, 12, 15, 18, 22, 25, 30, 35, 40, 45, 50]

        first_50_mappings = db.query(InventoryModelPartMapping).limit(50).all()

        for mapping in first_50_mappings:
            stock_records.append(
                InventoryStockTestRecord(
                    model_id=mapping.model_id,
                    part_id=mapping.part_id,
                    current_stock=random.choice(stock_values),
                )
            )

        db.add_all(stock_records)
        db.commit()

        print("✅ Inventory seed data inserted successfully.")
        print("Seasons:", db.query(InventorySeason).count())
        print("Stages:", db.query(InventoryStage).count())
        print("Categories:", db.query(InventoryMachineCategory).count())
        print("Brands:", db.query(InventoryBrand).count())
        print("Models:", db.query(InventoryMachineModel).count())
        print("Parts:", db.query(InventoryPart).count())
        print("Mappings:", db.query(InventoryModelPartMapping).count())
        print("Demand Rules:", db.query(InventorySeasonalDemandRule).count())
        print("Demand History:", db.query(InventoryDemandHistory).count())
        print("Stock Records:", db.query(InventoryStockTestRecord).count())

    except Exception as e:
        db.rollback()
        print("❌ Error seeding inventory data:", str(e))
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_inventory_data()