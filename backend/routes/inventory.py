from collections import defaultdict
from typing import List, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db_session import SessionLocal
from models.part import Part

# CHANGE THIS LINE ONLY if these models are in a different file
from models.research import (
    SalesTransaction,
    InventoryStock,
    CompatibilityLabel,
    FeedbackEvent,
)

from models.schemas import (
    ForecastItemResponse,
    InventoryRecommendResponse,
)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def aggregate_monthly_sales(transactions: List[SalesTransaction]) -> List[int]:
    """
    Convert raw sales transactions into monthly total demand.
    Example:
    Jan -> 5, Feb -> 8, Mar -> 6, Apr -> 10
    Returns: [5, 8, 6, 10]
    """
    monthly_totals: Dict[str, int] = defaultdict(int)

    for tx in transactions:
        month_key = tx.date.strftime("%Y-%m")
        monthly_totals[month_key] += tx.quantity

    sorted_months = sorted(monthly_totals.items(), key=lambda x: x[0])

    return [qty for _, qty in sorted_months]


def simple_exponential_smoothing(
    demand_series: List[int],
    alpha: float = 0.6
) -> float:
    """
    Forecast next-period demand using Simple Exponential Smoothing.
    """
    if not demand_series:
        return 0.0

    if len(demand_series) == 1:
        return float(demand_series[0])

    forecast = float(demand_series[0])

    for actual in demand_series[1:]:
        forecast = alpha * actual + (1 - alpha) * forecast

    return round(forecast, 2)


def compute_feedback_score(feedbacks: List[FeedbackEvent]) -> float:
    """
    Compute simple substitute usefulness score.
    accept = +1
    reject = -1
    """
    if not feedbacks:
        return 0.0

    score = 0

    for item in feedbacks:
        value = item.feedback.strip().lower()

        if value == "accept":
            score += 1
        elif value == "reject":
            score -= 1

    return round(score / len(feedbacks), 2)


@router.get("/forecast", response_model=List[ForecastItemResponse])
def get_inventory_forecast(
    vendor_id: str = Query(...),
    db: Session = Depends(get_db)
):
    transactions = (
        db.query(SalesTransaction)
        .filter(SalesTransaction.vendor_id == vendor_id)
        .order_by(SalesTransaction.part_id, SalesTransaction.date)
        .all()
    )

    part_transaction_map = {}

    for tx in transactions:
        part_transaction_map.setdefault(tx.part_id, []).append(tx)

    results = []

    for part_id, txs in part_transaction_map.items():
        monthly_demand = aggregate_monthly_sales(txs)
        forecast = simple_exponential_smoothing(monthly_demand, alpha=0.6)

        part = db.query(Part).filter(Part.id == part_id).first()

        results.append({
            "part_id": part_id,
            "part_name": part.name if part else f"Part {part_id}",
            "monthly_demand": monthly_demand,
            "forecast_next_month": forecast
        })

    return results


@router.get("/recommend", response_model=InventoryRecommendResponse)
def get_inventory_recommendations(
    vendor_id: str = Query(...),
    db: Session = Depends(get_db)
):
    inventory_rows = (
        db.query(InventoryStock)
        .filter(InventoryStock.vendor_id == vendor_id)
        .all()
    )

    reorder_list = []
    suggested_substitutes = []

    for stock_item in inventory_rows:
        transactions = (
            db.query(SalesTransaction)
            .filter(
                SalesTransaction.vendor_id == vendor_id,
                SalesTransaction.part_id == stock_item.part_id
            )
            .order_by(SalesTransaction.date)
            .all()
        )

        monthly_demand = aggregate_monthly_sales(transactions)
        forecast = simple_exponential_smoothing(monthly_demand, alpha=0.6)

        part = db.query(Part).filter(Part.id == stock_item.part_id).first()
        part_name = part.name if part else f"Part {stock_item.part_id}"

        if forecast > stock_item.stock_level or stock_item.stock_level <= stock_item.reorder_point:
            reorder_qty = max(0, round(forecast - stock_item.stock_level))

            reorder_list.append({
                "part_id": stock_item.part_id,
                "part_name": part_name,
                "current_stock": stock_item.stock_level,
                "reorder_point": stock_item.reorder_point,
                "forecast_next_month": forecast,
                "recommended_reorder_qty": reorder_qty,
                "reason": "Forecasted demand exceeds stock or stock is below reorder point"
            })

            compatibility_rows = (
                db.query(CompatibilityLabel)
                .filter(
                    CompatibilityLabel.label == 1,
                    (
                        (CompatibilityLabel.part_id_1 == stock_item.part_id) |
                        (CompatibilityLabel.part_id_2 == stock_item.part_id)
                    )
                )
                .all()
            )

            for comp in compatibility_rows:
                substitute_id = (
                    comp.part_id_2 if comp.part_id_1 == stock_item.part_id
                    else comp.part_id_1
                )

                substitute_part = db.query(Part).filter(Part.id == substitute_id).first()
                substitute_name = substitute_part.name if substitute_part else f"Part {substitute_id}"

                substitute_feedbacks = (
                    db.query(FeedbackEvent)
                    .filter(
                        FeedbackEvent.part_id == stock_item.part_id,
                        FeedbackEvent.recommended_part_id == substitute_id
                    )
                    .all()
                )

                feedback_score = compute_feedback_score(substitute_feedbacks)

                suggested_substitutes.append({
                    "original_part_id": stock_item.part_id,
                    "original_part_name": part_name,
                    "substitute_part_id": substitute_id,
                    "substitute_part_name": substitute_name,
                    "feedback_score": feedback_score,
                    "reason": "Compatible substitute for a high-demand or low-stock part"
                })

    seen = set()
    unique_substitutes = []

    for item in suggested_substitutes:
        key = (item["original_part_id"], item["substitute_part_id"])
        if key not in seen:
            seen.add(key)
            unique_substitutes.append(item)

    unique_substitutes.sort(key=lambda x: x["feedback_score"], reverse=True)

    return {
        "reorder_list": reorder_list,
        "suggested_substitutes": unique_substitutes
    }