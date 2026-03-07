# backend/utils/vectorizer/text_builder.py

from typing import Any


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
        parts.append(f"{key_text}:{value_text}")

    return " ".join(parts)


def build_part_text(part) -> str:
    """
    Build one clean text string from a Part object.
    Used for TF-IDF training and vector generation.
    """

    name = _safe_text(getattr(part, "name", ""))
    description = _safe_text(getattr(part, "description", ""))
    machine_model = _safe_text(getattr(part, "machine_model", ""))

    specs_json = getattr(part, "specs_json", None)
    specs_text = _flatten_specs_json(specs_json)

    full_text = " ".join([
        name,
        description,
        machine_model,
        specs_text
    ])

    # remove extra spaces
    return " ".join(full_text.split())

if __name__ == "__main__":
    class DummyPart:
        name = "Oil Filter"
        description = "High quality engine filtration"
        machine_model = "MF240"
        specs_json = {"thread": "M20", "size": "small"}

    p = DummyPart()
    print(build_part_text(p))