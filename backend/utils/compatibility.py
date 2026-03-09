# app/utils/compatibility.py

COMPATIBLE_MODELS = {"mf 240", "mf240", "tafe 7250", "tafe7250", "tafe 45di", "tafe45di", "tafe 45 di"}
KUBOTA_MODELS = {"kubota 4508", "kubota4508"}

def norm(v):
    return (v or "").strip().lower()

def is_family(model):
    return norm(model) in COMPATIBLE_MODELS

def is_kubota(model):
    return norm(model) in KUBOTA_MODELS

def get_model_group(model):
    m = norm(model)
    if m in COMPATIBLE_MODELS:
        return "mf_tafe_family"
    if m in KUBOTA_MODELS:
        return "kubota_family"
    return "unknown_family"

def get_compatible_models(model):
    m = norm(model)
    if m in COMPATIBLE_MODELS:
        return list(COMPATIBLE_MODELS)
    if m in KUBOTA_MODELS:
        return list(KUBOTA_MODELS)
    return [m]