from datetime import datetime

from db_session import SessionLocal
from models.research import (
    CompatibilityLabel,
    FeedbackEvent,
    SalesTransaction,
    InventoryStock,
)


def run():
    db = SessionLocal()

    try:
        vendor_id = "1"

        # -----------------------------
        # 1. Compatibility pairs
        # -----------------------------
        compatibility_data = [
            {"part_id_1": 34, "part_id_2": 70, "label": 1, "source": "manual"},
            {"part_id_1": 82, "part_id_2": 68, "label": 1, "source": "manual"},
            {"part_id_1": 102, "part_id_2": 120, "label": 1, "source": "manual"},
        ]

        for item in compatibility_data:
            exists = db.query(CompatibilityLabel).filter(
                CompatibilityLabel.part_id_1 == item["part_id_1"],
                CompatibilityLabel.part_id_2 == item["part_id_2"]
            ).first()

            reverse_exists = db.query(CompatibilityLabel).filter(
                CompatibilityLabel.part_id_1 == item["part_id_2"],
                CompatibilityLabel.part_id_2 == item["part_id_1"]
            ).first()

            if not exists and not reverse_exists:
                db.add(CompatibilityLabel(**item))

        # -----------------------------
        # 2. Inventory stock
        # -----------------------------
        inventory_data = [
            {"vendor_id": vendor_id, "part_id": 34, "stock_level": 3, "reorder_point": 5},
            {"vendor_id": vendor_id, "part_id": 70, "stock_level": 6, "reorder_point": 4},
            {"vendor_id": vendor_id, "part_id": 82, "stock_level": 2, "reorder_point": 4},
            {"vendor_id": vendor_id, "part_id": 68, "stock_level": 5, "reorder_point": 3},
            {"vendor_id": vendor_id, "part_id": 102, "stock_level": 1, "reorder_point": 4},
            {"vendor_id": vendor_id, "part_id": 120, "stock_level": 4, "reorder_point": 3},
        ]

        for item in inventory_data:
            exists = db.query(InventoryStock).filter(
                InventoryStock.vendor_id == item["vendor_id"],
                InventoryStock.part_id == item["part_id"]
            ).first()

            if not exists:
                db.add(InventoryStock(**item))

        # -----------------------------
        # 3. Sales transactions
        # Main-demand parts: 34, 82, 102
        # -----------------------------
        sales_data = [
            # Part 34 - Clutch Finger TAFE 7250
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 4, "date": datetime(2025, 11, 3)},
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 3, "date": datetime(2025, 11, 20)},
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 5, "date": datetime(2025, 12, 5)},
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 2, "date": datetime(2025, 12, 28)},
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 6, "date": datetime(2026, 1, 10)},
            {"vendor_id": vendor_id, "part_id": 34, "quantity": 7, "date": datetime(2026, 2, 3)},

            # Part 82 - Valve Guide MF240
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 2, "date": datetime(2025, 11, 6)},
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 2, "date": datetime(2025, 11, 21)},
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 3, "date": datetime(2025, 12, 8)},
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 2, "date": datetime(2025, 12, 26)},
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 4, "date": datetime(2026, 1, 12)},
            {"vendor_id": vendor_id, "part_id": 82, "quantity": 5, "date": datetime(2026, 2, 4)},

            # Part 102 - Front Hub Bearing Inner TAFE45DI
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 3, "date": datetime(2025, 11, 2)},
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 2, "date": datetime(2025, 11, 19)},
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 4, "date": datetime(2025, 12, 7)},
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 3, "date": datetime(2025, 12, 29)},
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 5, "date": datetime(2026, 1, 11)},
            {"vendor_id": vendor_id, "part_id": 102, "quantity": 6, "date": datetime(2026, 2, 5)},
        ]

        for item in sales_data:
            exists = db.query(SalesTransaction).filter(
                SalesTransaction.vendor_id == item["vendor_id"],
                SalesTransaction.part_id == item["part_id"],
                SalesTransaction.quantity == item["quantity"],
                SalesTransaction.date == item["date"]
            ).first()

            if not exists:
                db.add(SalesTransaction(**item))

        # -----------------------------
        # 4. Feedback events
        # -----------------------------
        feedback_data = [
            {"user_id": "user_1", "part_id": 34, "recommended_part_id": 70, "feedback": "accept"},
            {"user_id": "user_2", "part_id": 34, "recommended_part_id": 70, "feedback": "accept"},
            {"user_id": "user_3", "part_id": 34, "recommended_part_id": 70, "feedback": "reject"},

            {"user_id": "user_4", "part_id": 82, "recommended_part_id": 68, "feedback": "accept"},
            {"user_id": "user_5", "part_id": 82, "recommended_part_id": 68, "feedback": "accept"},

            {"user_id": "user_6", "part_id": 102, "recommended_part_id": 120, "feedback": "accept"},
            {"user_id": "user_7", "part_id": 102, "recommended_part_id": 120, "feedback": "reject"},
            {"user_id": "user_8", "part_id": 102, "recommended_part_id": 120, "feedback": "accept"},
        ]

        for item in feedback_data:
            exists = db.query(FeedbackEvent).filter(
                FeedbackEvent.user_id == item["user_id"],
                FeedbackEvent.part_id == item["part_id"],
                FeedbackEvent.recommended_part_id == item["recommended_part_id"],
                FeedbackEvent.feedback == item["feedback"]
            ).first()

            if not exists:
                db.add(FeedbackEvent(**item))

        db.commit()
        print("Inventory demo seed data inserted successfully.")

    except Exception as e:
        db.rollback()
        print("Error:", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()