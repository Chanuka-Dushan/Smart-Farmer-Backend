from math import ceil
from sqlalchemy.orm import Session

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
)


MONTH_TO_SEASON = {
    "January": "Maha",
    "February": "Maha",
    "March": "Maha",
    "April": "Yala",
    "May": "Yala",
    "June": "Yala",
    "July": "Yala",
    "August": "Yala",
    "September": "Maha",
    "October": "Maha",
    "November": "Maha",
    "December": "Maha",
}


# Temporary compatibility knowledge base.
# You can later replace this with a database compatibility table.
COMPATIBLE_MODEL_GROUPS = [
    ["TAFE 7250", "MF 240", "TAFE 45DI"],
]


def normalize_text(value):
    return str(value or "").strip().lower()


def get_compatible_model_names(model_name: str):
    """
    Returns compatible model names for the selected model.

    Example:
    TAFE 7250 -> MF 240, TAFE 45DI
    MF 240 -> TAFE 7250, TAFE 45DI
    TAFE 45DI -> TAFE 7250, MF 240
    """
    normalized_model_name = normalize_text(model_name)

    for group in COMPATIBLE_MODEL_GROUPS:
        normalized_group = [normalize_text(name) for name in group]

        if normalized_model_name in normalized_group:
            return [
                name
                for name in group
                if normalize_text(name) != normalized_model_name
            ]

    return []


def get_season_from_month(month: str):
    if not month:
        return None

    return MONTH_TO_SEASON.get(month.strip().capitalize())


def exponential_smoothing(history_values, alpha=0.4):
    if not history_values:
        return None

    forecast = history_values[0]

    for demand in history_values[1:]:
        forecast = alpha * demand + (1 - alpha) * forecast

    return round(forecast)


def get_forecast_for_part(
    db: Session,
    model_id: int,
    part_id: int,
    base_demand: int,
    season_id: int,
):
    history_rows = (
        db.query(InventoryDemandHistory)
        .filter(
            InventoryDemandHistory.model_id == model_id,
            InventoryDemandHistory.part_id == part_id,
            InventoryDemandHistory.season_id == season_id,
        )
        .order_by(InventoryDemandHistory.id.asc())
        .all()
    )

    history_values = [row.demand_quantity for row in history_rows]

    history = [
        {
            "month": row.month,
            "demand": row.demand_quantity,
        }
        for row in history_rows
    ]

    forecast = exponential_smoothing(history_values)

    if forecast is None:
        forecast = base_demand

    last_actual = history_values[-1] if history_values else None

    if last_actual and last_actual > 0:
        forecast_error = abs(forecast - last_actual)
        forecast_accuracy = round(
            max(0, 100 - ((forecast_error / last_actual) * 100)),
            2,
        )
    else:
        forecast_error = None
        forecast_accuracy = None

    return {
        "history": history,
        "forecastDemand": forecast,
        "lastActualDemand": last_actual,
        "forecastError": forecast_error,
        "forecastAccuracy": forecast_accuracy,
        "forecastMethod": "Season-aware Exponential Smoothing",
        "alpha": 0.4,
    }


def build_model_parts_output(db: Session, machine_model, rule):
    brand = (
        db.query(InventoryBrand)
        .filter(InventoryBrand.id == machine_model.brand_id)
        .first()
    )

    mappings = (
        db.query(InventoryModelPartMapping)
        .filter(InventoryModelPartMapping.model_id == machine_model.id)
        .all()
    )

    parts = []

    for mapping in mappings:
        part = (
            db.query(InventoryPart)
            .filter(InventoryPart.id == mapping.part_id)
            .first()
        )

        if not part:
            continue

        forecast_data = get_forecast_for_part(
            db=db,
            model_id=machine_model.id,
            part_id=part.id,
            base_demand=rule.base_demand,
            season_id=rule.season_id,
        )

        parts.append({
            "partId": part.id,
            "partName": part.name,
            "partType": part.part_type,
            "criticality": mapping.criticality,
            "demandLevel": rule.demand_level,
            "baseDemand": rule.base_demand,
            "history": forecast_data["history"],
            "forecastDemand": forecast_data["forecastDemand"],
            "lastActualDemand": forecast_data["lastActualDemand"],
            "forecastError": forecast_data["forecastError"],
            "forecastAccuracy": forecast_data["forecastAccuracy"],
            "forecastMethod": forecast_data["forecastMethod"],
            "alpha": forecast_data["alpha"],
        })

    return {
        "modelId": machine_model.id,
        "brand": brand.name if brand else None,
        "modelName": machine_model.model_name,
        "parts": parts,
    }


def select_unique_highest_rules(rules):
    unique_rules = {}

    for rule in sorted(rules, key=lambda r: r.base_demand, reverse=True):
        if rule.category_id not in unique_rules:
            unique_rules[rule.category_id] = rule

    return list(unique_rules.values())


def predict_inventory_demand(
    db: Session,
    month: str = None,
    season: str = None,
    stage: str = None,
    category: str = None,
    model: str = None,
    type: str = None,
):
    if type == "high_demand_parts":
        return get_high_demand_parts(db)

    if type == "high_demand_machines":
        return get_high_demand_machines(db)

    if month and not season:
        season = get_season_from_month(month)

    if not season:
        raise ValueError("Please provide month, season, model with month, or type")

    season_obj = (
        db.query(InventorySeason)
        .filter(InventorySeason.name.ilike(season))
        .first()
    )

    if not season_obj:
        raise ValueError("Invalid season")

    stage_obj = None

    if stage:
        stage_obj = (
            db.query(InventoryStage)
            .filter(InventoryStage.name.ilike(stage))
            .first()
        )

        if not stage_obj:
            raise ValueError("Invalid stage")

    category_obj = None

    if category:
        category_obj = (
            db.query(InventoryMachineCategory)
            .filter(InventoryMachineCategory.name.ilike(category))
            .first()
        )

        if not category_obj:
            raise ValueError("Invalid category")

    selected_model = None

    if model:
        selected_model = (
            db.query(InventoryMachineModel)
            .filter(InventoryMachineModel.model_name.ilike(model))
            .first()
        )

        if not selected_model:
            raise ValueError("Invalid model")

        if category_obj and selected_model.category_id != category_obj.id:
            raise ValueError("Selected model does not belong to selected category")

        category_obj = (
            db.query(InventoryMachineCategory)
            .filter(InventoryMachineCategory.id == selected_model.category_id)
            .first()
        )

    rule_query = db.query(InventorySeasonalDemandRule).filter(
        InventorySeasonalDemandRule.season_id == season_obj.id
    )

    if stage_obj:
        rule_query = rule_query.filter(
            InventorySeasonalDemandRule.stage_id == stage_obj.id
        )

    if category_obj:
        rule_query = rule_query.filter(
            InventorySeasonalDemandRule.category_id == category_obj.id
        )

    rules = rule_query.all()
    rules = select_unique_highest_rules(rules)

    machines = []

    for rule in rules:
        category_data = (
            db.query(InventoryMachineCategory)
            .filter(InventoryMachineCategory.id == rule.category_id)
            .first()
        )

        if not category_data:
            continue

        if selected_model:
            models = [selected_model]
        else:
            models = (
                db.query(InventoryMachineModel)
                .filter(InventoryMachineModel.category_id == category_data.id)
                .all()
            )

        model_results = [
            build_model_parts_output(db, machine_model, rule)
            for machine_model in models
        ]

        machines.append({
            "categoryId": category_data.id,
            "category": category_data.name,
            "demandLevel": rule.demand_level,
            "baseDemand": rule.base_demand,
            "models": model_results,
        })

    return {
        "month": month,
        "season": season_obj.name,
        "stage": stage_obj.name if stage_obj else "All stages",
        "category": category_obj.name if category_obj else "All categories",
        "model": selected_model.model_name if selected_model else "All models",
        "machines": machines,
    }


def get_high_demand_parts(db: Session):
    mappings = (
        db.query(InventoryModelPartMapping)
        .filter(InventoryModelPartMapping.criticality == "HIGH")
        .limit(50)
        .all()
    )

    results = []

    for mapping in mappings:
        machine_model = (
            db.query(InventoryMachineModel)
            .filter_by(id=mapping.model_id)
            .first()
        )

        part = (
            db.query(InventoryPart)
            .filter_by(id=mapping.part_id)
            .first()
        )

        if not machine_model or not part:
            continue

        brand = (
            db.query(InventoryBrand)
            .filter_by(id=machine_model.brand_id)
            .first()
        )

        category = (
            db.query(InventoryMachineCategory)
            .filter_by(id=machine_model.category_id)
            .first()
        )

        results.append({
            "category": category.name if category else None,
            "brand": brand.name if brand else None,
            "modelId": machine_model.id,
            "modelName": machine_model.model_name,
            "partId": part.id,
            "partName": part.name,
            "partType": part.part_type,
            "criticality": mapping.criticality,
        })

    return {
        "type": "high_demand_parts",
        "items": results,
    }


def get_high_demand_machines(db: Session):
    categories = db.query(InventoryMachineCategory).all()
    results = []

    for category in categories:
        models = (
            db.query(InventoryMachineModel)
            .filter(InventoryMachineModel.category_id == category.id)
            .all()
        )

        results.append({
            "categoryId": category.id,
            "category": category.name,
            "models": [
                {
                    "modelId": machine_model.id,
                    "modelName": machine_model.model_name,
                }
                for machine_model in models
            ],
        })

    return {
        "type": "high_demand_machines",
        "machines": results,
    }


def flatten_prediction_output(prediction_result):
    flat_list = []

    for machine in prediction_result.get("machines", []):
        for model in machine.get("models", []):
            for part in model.get("parts", []):
                flat_list.append({
                    "category": machine.get("category"),
                    "modelName": model.get("modelName"),
                    "partName": part.get("partName"),
                    "forecastDemand": part.get("forecastDemand", 0),
                    "forecastAccuracy": part.get("forecastAccuracy"),
                })

    return flat_list


def get_part_details_by_model_and_part(
    db: Session,
    model_name: str,
    part_name: str,
):
    machine_model = (
        db.query(InventoryMachineModel)
        .filter(InventoryMachineModel.model_name.ilike(model_name))
        .first()
    )

    if not machine_model:
        return None, None

    part = (
        db.query(InventoryPart)
        .filter(InventoryPart.name.ilike(part_name))
        .first()
    )

    if not part:
        return machine_model, None

    return machine_model, part


def get_substitute_suggestions(
    db: Session,
    model_name: str,
    part_name: str,
):
    machine_model, original_part = get_part_details_by_model_and_part(
        db=db,
        model_name=model_name,
        part_name=part_name,
    )

    if not machine_model or not original_part:
        return {
            "available": False,
            "suggestedParts": [],
            "reason": "Model or part not found in inventory dataset",
        }

    compatible_model_names = get_compatible_model_names(model_name)

    if not compatible_model_names:
        return {
            "available": False,
            "suggestedParts": [],
            "reason": "No compatible model group found for this model",
        }

    suggestions = []
    seen_models = set()

    for compatible_model_name in compatible_model_names:
        compatible_model = (
            db.query(InventoryMachineModel)
            .filter(InventoryMachineModel.model_name.ilike(compatible_model_name))
            .first()
        )

        if not compatible_model:
            continue

        if compatible_model.id in seen_models:
            continue

        # Important:
        # Only suggest if the compatible model has the SAME part.
        mapping = (
            db.query(InventoryModelPartMapping)
            .filter(
                InventoryModelPartMapping.model_id == compatible_model.id,
                InventoryModelPartMapping.part_id == original_part.id,
            )
            .first()
        )

        if not mapping:
            continue

        seen_models.add(compatible_model.id)

        brand = (
            db.query(InventoryBrand)
            .filter(InventoryBrand.id == compatible_model.brand_id)
            .first()
        )

        category = (
            db.query(InventoryMachineCategory)
            .filter(InventoryMachineCategory.id == compatible_model.category_id)
            .first()
        )

        suggestions.append({
            "partId": original_part.id,
            "partName": original_part.name,
            "partType": original_part.part_type,
            "modelId": compatible_model.id,
            "modelName": compatible_model.model_name,
            "brand": brand.name if brand else None,
            "category": category.name if category else None,
            "criticality": mapping.criticality,
            "compatibilityType": "Compatible model group",
            "reason": "Same part available in a compatible machine model",
        })

    return {
        "available": len(suggestions) > 0,
        "suggestedParts": suggestions[:3],
        "reason": "Substitutes found using same part in compatible machine models"
        if suggestions else "No same-part substitute found in compatible models",
    }


def analyze_stock(predicted_items, vendor_stock):
    stock_lookup = {}

    for item in vendor_stock:
        model_name = normalize_text(item.get("modelName"))
        part_name = normalize_text(item.get("partName"))

        key = (model_name, part_name)
        stock_lookup[key] = int(item.get("currentStock", 0) or 0)

    analysis = []

    for item in predicted_items:
        model_name = str(item.get("modelName", "") or "").strip()
        part_name = str(item.get("partName", "") or "").strip()
        forecast_demand = int(item.get("forecastDemand", 0) or 0)

        key = (
            normalize_text(model_name),
            normalize_text(part_name),
        )

        current_stock = stock_lookup.get(key, 0)

        safety_stock = ceil(forecast_demand * 0.25)
        safe_stock = forecast_demand + safety_stock
        need_to_buy = max(safe_stock - current_stock, 0)

        if current_stock < safe_stock:
            status = "LOW_STOCK"
        elif current_stock <= safe_stock * 1.5:
            status = "ENOUGH_STOCK"
        else:
            status = "HIGH_STOCK"

        analysis.append({
            "modelName": model_name,
            "partName": part_name,
            "currentStock": current_stock,
            "forecastDemand": forecast_demand,
            "safetyStock": safety_stock,
            "safeStock": safe_stock,
            "status": status,
            "needToBuy": need_to_buy,
        })

    return {
        "stockAnalysis": analysis,
    }


def analyze_stock_with_substitutes(db: Session, predicted_items, vendor_stock):
    normal_result = analyze_stock(predicted_items, vendor_stock)
    enhanced_analysis = []

    for item in normal_result.get("stockAnalysis", []):
        substitute_suggestion = {
            "available": False,
            "suggestedParts": [],
            "reason": "Substitute suggestion only generated for LOW_STOCK items",
        }

        if item.get("status") == "LOW_STOCK":
            substitute_suggestion = get_substitute_suggestions(
                db=db,
                model_name=item.get("modelName"),
                part_name=item.get("partName"),
            )

        item["substituteSuggestion"] = substitute_suggestion
        enhanced_analysis.append(item)

    return {
        "stockAnalysis": enhanced_analysis,
    }