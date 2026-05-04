import os
import json
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import openpyxl

from utils.inventory_service import (
    predict_inventory_demand,
    analyze_stock_with_substitutes,
    flatten_prediction_output,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_inventory_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory Forecasting"],
)


class PredictedItem(BaseModel):
    modelName: str
    partName: str
    forecastDemand: int


class VendorStockItem(BaseModel):
    modelName: str
    partName: str
    currentStock: int


class StockAnalyzeRequest(BaseModel):
    predictedItems: List[PredictedItem]
    vendorStock: List[VendorStockItem]


def normalize_excel_header(value):
    """
    Converts Excel headers into a comparable format.

    Examples:
    'modelName'     -> 'modelname'
    'Model Name'    -> 'modelname'
    'model_name'    -> 'modelname'
    ' modelName '   -> 'modelname'
    """
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def find_header_index(normalized_headers, aliases):
    for alias in aliases:
        normalized_alias = normalize_excel_header(alias)
        if normalized_alias in normalized_headers:
            return normalized_headers.index(normalized_alias)
    return None


def parse_int_safe(value):
    try:
        if value is None:
            return 0

        if isinstance(value, float):
            return int(value)

        return int(str(value).strip())
    except Exception:
        return 0


@router.get("/predict")
def predict_inventory(
    month: Optional[str] = None,
    season: Optional[str] = None,
    stage: Optional[str] = None,
    category: Optional[str] = None,
    model: Optional[str] = None,
    type: Optional[str] = None,
    flatten: bool = False,
    db: Session = Depends(get_inventory_db),
):
    try:
        result = predict_inventory_demand(
            db=db,
            month=month,
            season=season,
            stage=stage,
            category=category,
            model=model,
            type=type,
        )

        if flatten and type is None:
            return {
                "summary": {
                    "month": result.get("month"),
                    "season": result.get("season"),
                    "stage": result.get("stage"),
                    "category": result.get("category"),
                    "model": result.get("model"),
                },
                "predictedItems": flatten_prediction_output(result),
            }

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/analyze")
def stock_analyze(
    request: StockAnalyzeRequest,
    db: Session = Depends(get_inventory_db),
):
    try:
        predicted_items = [item.dict() for item in request.predictedItems]
        vendor_stock = [item.dict() for item in request.vendorStock]

        return analyze_stock_with_substitutes(
            db=db,
            predicted_items=predicted_items,
            vendor_stock=vendor_stock,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/analyze-excel")
async def stock_analyze_excel(
    file: UploadFile = File(...),
    predictedItems: str = Form(...),
    db: Session = Depends(get_inventory_db),
):
    try:
        predicted_items = json.loads(predictedItems)

        try:
            workbook = openpyxl.load_workbook(file.file, data_only=True)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid Excel file. Please upload a valid .xlsx file.",
            )

        sheet = workbook.active

        raw_headers = [cell.value for cell in sheet[1]]
        normalized_headers = [
            normalize_excel_header(header) for header in raw_headers
        ]

        print("EXCEL FILE NAME:", file.filename)
        print("EXCEL RAW HEADERS:", raw_headers)
        print("EXCEL NORMALIZED HEADERS:", normalized_headers)

        model_idx = find_header_index(
            normalized_headers,
            ["modelName", "Model Name", "model_name", "model", "machineModel"],
        )

        part_idx = find_header_index(
            normalized_headers,
            ["partName", "Part Name", "part_name", "part"],
        )

        stock_idx = find_header_index(
            normalized_headers,
            [
                "currentStock",
                "Current Stock",
                "current_stock",
                "stock",
                "quantity",
                "qty",
            ],
        )

        missing_columns = []

        if model_idx is None:
            missing_columns.append("modelName")

        if part_idx is None:
            missing_columns.append("partName")

        if stock_idx is None:
            missing_columns.append("currentStock")

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Missing required column: {', '.join(missing_columns)}. "
                    f"Found headers: {raw_headers}"
                ),
            )

        vendor_stock = []

        for row in sheet.iter_rows(min_row=2, values_only=True):
            model_name = row[model_idx] if model_idx < len(row) else None
            part_name = row[part_idx] if part_idx < len(row) else None
            current_stock = row[stock_idx] if stock_idx < len(row) else None

            if not model_name or not part_name:
                continue

            vendor_stock.append({
                "modelName": str(model_name).strip(),
                "partName": str(part_name).strip(),
                "currentStock": parse_int_safe(current_stock),
            })

        if not vendor_stock:
            raise HTTPException(
                status_code=400,
                detail="No valid stock rows found in Excel file.",
            )

        return analyze_stock_with_substitutes(
            db=db,
            predicted_items=predicted_items,
            vendor_stock=vendor_stock,
        )

    except HTTPException:
        raise

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid predictedItems JSON data.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))