from sqlalchemy.orm import Session

from utils.database import SessionLocal
from models.part import Part
from models.research import CompatibilityLabel   # change only if import error


COMPATIBLE_MODELS = {"MF 240", "TAFE 7250", "TAFE 45DI", "TAFE 45 DI"}
KUBOTA_MODELS = {"kubota 4508", "Kubota 4508"}

TARGET_COMPATIBLE = 40
TARGET_INCOMPATIBLE = 40


def norm(v):
    return (v or "").strip().lower()


def pair(a, b):
    return (min(a, b), max(a, b))


def pair_exists(db: Session, a, b):
    x, y = pair(a, b)
    return db.query(CompatibilityLabel).filter(
        CompatibilityLabel.part_id_1 == x,
        CompatibilityLabel.part_id_2 == y
    ).first() is not None


def same_part(p1: Part, p2: Part):
    if norm(p1.name) == norm(p2.name):
        return True

    s1 = p1.specs_json or {}
    s2 = p2.specs_json or {}

    t1 = norm(s1.get("type"))
    t2 = norm(s2.get("type"))

    return t1 and t2 and t1 == t2


def is_family(model):
    return norm(model) in {m.lower() for m in COMPATIBLE_MODELS}


def is_kubota(model):
    return norm(model) in {m.lower() for m in KUBOTA_MODELS}


def run():
    db: Session = SessionLocal()

    try:
        parts = db.query(Part).all()

        compatible = []
        incompatible = []

        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                p1 = parts[i]
                p2 = parts[j]

                if not same_part(p1, p2):
                    continue

                m1 = p1.machine_model
                m2 = p2.machine_model

                if is_family(m1) and is_family(m2):
                    compatible.append((p1, p2))
                elif (is_kubota(m1) and is_family(m2)) or (is_kubota(m2) and is_family(m1)):
                    incompatible.append((p1, p2))

        print("Compatible candidates:", len(compatible))
        print("Incompatible candidates:", len(incompatible))

        c = 0
        ic = 0

        for p1, p2 in compatible:
            if c >= TARGET_COMPATIBLE:
                break
            a, b = pair(p1.id, p2.id)
            if pair_exists(db, a, b):
                continue
            db.add(CompatibilityLabel(part_id_1=a, part_id_2=b, label=1, source="manual"))
            c += 1

        for p1, p2 in incompatible:
            if ic >= TARGET_INCOMPATIBLE:
                break
            a, b = pair(p1.id, p2.id)
            if pair_exists(db, a, b):
                continue
            db.add(CompatibilityLabel(part_id_1=a, part_id_2=b, label=0, source="manual"))
            ic += 1

        db.commit()

        print("\n✅ Done")
        print("Compatible inserted:", c)
        print("Incompatible inserted:", ic)

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    run()