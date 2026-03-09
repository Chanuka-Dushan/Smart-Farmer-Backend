from typing import Any
from ..compatibility import get_model_group


def _safe_text(value: Any) -> str:
    """
    Convert any value to clean lowercase text.
    If None -> return empty string.
    """
    if value is None:
        return ""
    return str(value).strip().lower()


def _flatten_specs_json(specs: Any) -> str:
    """
    Convert specs_json dict into 'key:value key:value' format.
    If None or not dict -> return empty string.
    """
    if not specs or not isinstance(specs, dict):
        return ""

    parts = []
    for key, value in specs.items():
        key_text = _safe_text(key)
        value_text = _safe_text(value)

        if key_text or value_text:
            parts.append(f"{key_text}:{value_text}")

    return " ".join(parts)


def build_part_text(part) -> str:
    """
    Build one clean text string from a Part object.
    Used for TF-IDF training and vector generation.

    Included fields:
    - name
    - description
    - category
    - machine_model
    - compatibility_group
    - specs_json (flattened)
    """

    name = _safe_text(getattr(part, "name", ""))
    description = _safe_text(getattr(part, "description", ""))
    category = _safe_text(getattr(part, "category", ""))
    machine_model = _safe_text(getattr(part, "machine_model", ""))
    compatibility_group = _safe_text(get_model_group(getattr(part, "machine_model", "")))

    specs_json = getattr(part, "specs_json", None)
    specs_text = _flatten_specs_json(specs_json)

    full_text = " ".join([
        name,
        description,
        f"category {category}" if category else "",
        f"machine_model {machine_model}" if machine_model else "",
        f"compatibility_group {compatibility_group}" if compatibility_group else "",
        specs_text
    ])

    # remove extra spaces
    return " ".join(full_text.split())


if __name__ == "__main__":
    class DummyPart:
        name = "Oil Filter"
        description = "High quality engine filtration"
        category = "Filter"
        machine_model = "MF240"
        specs_json = {"thread": "M20", "size": "small"}

    p = DummyPart()
    print(build_part_text(p))


if __name__ == "__main__":
    class DummyPart:
        def __init__(self, name, description, category, machine_model, specs_json):
            self.name = name
            self.description = description
            self.category = category
            self.machine_model = machine_model
            self.specs_json = specs_json

    mf_part = DummyPart(
        name="Front Wheel Bearing",
        description="Heavy duty bearing for front wheel",
        category="Bearing",
        machine_model="MF 240",
        specs_json={"diameter": "35mm", "material": "steel"}
    )

    kubota_part = DummyPart(
        name="Oil Seal",
        description="Durable oil seal for tractor engine",
        category="Seal",
        machine_model="Kubota 4508",
        specs_json={"size": "small", "material": "rubber"}
    )

    print("MF/TAFE PART TEXT:")
    print(build_part_text(mf_part))
    print()

    print("KUBOTA PART TEXT:")
    print(build_part_text(kubota_part))