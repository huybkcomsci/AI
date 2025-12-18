from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nutrition_pipeline_advanced import NutritionPipelineAdvanced
from dbs import DailyLogDB, DEFAULT_TOTALS
from vietnamese_foods_extended import (
    calculate_nutrition,
    estimate_weight,
    VIETNAMESE_FOODS_NUTRITION,
)


app = FastAPI(title="Nutrition Chat API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = NutritionPipelineAdvanced()
daily_log_db = DailyLogDB()


# ----------------------------
# Request models (spec)
# ----------------------------
class AnalyzeRequest(BaseModel):
    patientId: str = Field(..., description="Unique patient id")
    userId: Optional[str] = "default"
    text: str
    dateKey: str
    locale: Optional[str] = "vi-VN"


class UpdateQuantityRequest(BaseModel):
    patientId: str
    userId: Optional[str] = "default"
    foodName: str
    newQuantity: float
    newUnit: Optional[str] = None
    dateKey: str
    source: Optional[str] = "inline_edit"


class UpdateFoodPatch(BaseModel):
    foodName: Optional[str] = None
    quantityInfo: Optional[Dict[str, Any]] = None
    nutrition: Optional[Dict[str, Any]] = None


class UpdateFoodRequest(BaseModel):
    patientId: str
    userId: Optional[str] = "default"
    entryId: str
    foodId: str
    patch: UpdateFoodPatch


class DeleteFoodRequest(BaseModel):
    patientId: str
    userId: Optional[str] = "default"
    entryId: str
    foodId: str


class ConfirmMealRequest(BaseModel):
    patientId: str
    userId: Optional[str] = "default"
    entryId: str
    dateKey: str
    confirmed: bool = True
    finalData: Optional[Dict[str, Any]] = None


# ----------------------------
# Helpers
# ----------------------------
def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def error_response(code: str, message: str):
    return {"success": False, "error": {"code": code, "message": message}}


def to_spec_foods(foods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mapped = []
    for idx, food in enumerate(foods, start=1):
        qty = food.get("quantity_info", food.get("quantityInfo", {})) or {}
        no_sugar = bool(food.get("no_sugar") or food.get("noSugar"))
        mapped.append(
            {
                "foodId": food.get("foodId") or f"tmp_{idx}",
                "foodName": food.get("food_name") or food.get("foodName"),
                "quantityInfo": {
                    "amount": qty.get("amount"),
                    "unit": qty.get("unit"),
                    "type": qty.get("type", "absolute"),
                    "confidence": qty.get("confidence", 1.0),
                },
                "nutrition": food.get("nutrition", {}),
                **({"noSugar": True} if no_sugar else {}),
            }
        )
    return mapped


def to_meal_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "foodCount": summary.get("food_count") or summary.get("foodCount") or 0,
        "calories": float(summary.get("calories", 0) or 0),
        "carbs": float(summary.get("carbs", 0) or 0),
        "sugar": float(summary.get("sugar", 0) or 0),
        "protein": float(summary.get("protein", 0) or 0),
        "fat": float(summary.get("fat", 0) or 0),
        "fiber": float(summary.get("fiber", 0) or 0),
    }


def calc_meal_summary_from_foods(foods: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {"foodCount": len(foods), **DEFAULT_TOTALS.copy()}
    for food in foods:
        nutrition = food.get("nutrition", {}) or {}
        for key in DEFAULT_TOTALS:
            summary[key] += float(nutrition.get(key, 0) or 0)
    return summary


def recalc_food_nutrition(food: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculate nutrition when quantity changes."""
    qty = food.get("quantityInfo", {}) or {}
    name = food.get("foodName") or ""
    category = VIETNAMESE_FOODS_NUTRITION.get(name, {}).get("category")
    no_sugar = bool(food.get("noSugar"))
    quantity_info = {
        "amount": qty.get("amount"),
        "unit": qty.get("unit"),
        "type": qty.get("type", "absolute"),
        "confidence": qty.get("confidence", 1.0),
    }
    weight = estimate_weight(quantity_info, category)
    nutrition = calculate_nutrition(name, weight) or {}
    if no_sugar and isinstance(nutrition, dict):
        nutrition["sugar"] = 0.0
    food["nutrition"] = nutrition
    return food


def find_day_for_entry(patient_id: str, entry_id: str) -> Optional[str]:
    """Locate which day contains an entry id for a patient."""
    logs = daily_log_db.get_patient_logs(patient_id)
    for log in logs:
        for entry in log.get("entries", []):
            if entry.get("entryId") == entry_id:
                return log.get("day")
    return None


def get_entry_by_id(log: Dict[str, Any], entry_id: str) -> Optional[Dict[str, Any]]:
    for entry in log.get("entries", []):
        if entry.get("entryId") == entry_id:
            return entry
    return None


# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def health():
    return {"message": "Nutrition Chat API", "status": "running"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    if not request.patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")
    if not request.dateKey:
        return error_response("VALIDATION_ERROR", "dateKey is required")

    result = pipeline.process_input(request.text)
    entry_id = str(int(datetime.utcnow().timestamp() * 1000))
    mapped_foods = to_spec_foods(result.get("foods", []))
    meal_summary = to_meal_summary(result.get("meal_summary", {}))

    entry = {
        "entryId": entry_id,
        "text": request.text,
        "userId": request.userId,
        "foods": mapped_foods,
        "mealSummary": meal_summary,
        "createdAt": now_utc(),
        "status": "draft",
    }
    daily_log_db.append_entry(request.patientId, request.dateKey, entry)

    return {
        "success": True,
        "data": {
            "foods": mapped_foods,
            "mealSummary": meal_summary,
        },
        "meta": {
            "patientId": request.patientId,
            "requestId": entry_id,
            "entryId": entry_id,
            "createdAt": entry["createdAt"],
        },
    }


@app.post("/update-quantity")
async def update_quantity(request: UpdateQuantityRequest):
    if not request.patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")

    log = daily_log_db.get_daily_log(request.patientId, request.dateKey)
    if not log:
        return error_response("NOT_FOUND", "No records found for this date")

    target_entry_id: Optional[str] = None
    for entry in reversed(log.get("entries", [])):
        for food in entry.get("foods", []):
            if str(food.get("foodName", "")).lower() == request.foodName.lower():
                target_entry_id = entry.get("entryId")
                break
        if target_entry_id:
            break

    if not target_entry_id:
        return error_response("NOT_FOUND", "Food not found for this patient/date")

    saved_unit = request.newUnit

    def updater(entry: Dict[str, Any]) -> Dict[str, Any]:
        for food in entry.get("foods", []):
            if str(food.get("foodName", "")).lower() == request.foodName.lower():
                qty = food.get("quantityInfo", {}) or {}
                qty["amount"] = request.newQuantity
                if request.newUnit:
                    qty["unit"] = request.newUnit
                qty["type"] = qty.get("type", "absolute")
                food["quantityInfo"] = qty
                recalc_food_nutrition(food)
                entry["updatedAt"] = now_utc()
                break
        entry["mealSummary"] = calc_meal_summary_from_foods(entry.get("foods", []))
        return entry

    updated_log = daily_log_db.update_entry(
        request.patientId, request.dateKey, target_entry_id, updater
    )
    if not updated_log:
        return error_response("NOT_FOUND", "Entry not found")

    updated_entry = get_entry_by_id(updated_log, target_entry_id) or {}
    for food in updated_entry.get("foods", []):
        if str(food.get("foodName", "")).lower() == request.foodName.lower():
            saved_unit = food.get("quantityInfo", {}).get("unit", saved_unit)
            break

    return {
        "success": True,
        "data": {
            "patientId": request.patientId,
            "foodName": request.foodName,
            "savedQuantity": request.newQuantity,
            "savedUnit": saved_unit,
            "ruleId": "rule_manual",
        },
    }


@app.post("/update-food")
async def update_food(request: UpdateFoodRequest):
    if not request.patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")

    day = find_day_for_entry(request.patientId, request.entryId)
    if not day:
        return error_response("NOT_FOUND", "Entry not found for patient")

    patch = request.patch
    updated_at = now_utc()
    changed = {"ok": False}

    def updater(entry: Dict[str, Any]) -> Dict[str, Any]:
        for food in entry.get("foods", []):
            if food.get("foodId") == request.foodId:
                if patch.foodName:
                    food["foodName"] = patch.foodName
                if patch.quantityInfo:
                    qty = food.get("quantityInfo", {}) or {}
                    qty.update(patch.quantityInfo)
                    qty["type"] = qty.get("type", "absolute")
                    food["quantityInfo"] = qty
                if patch.nutrition:
                    food["nutrition"] = {**food.get("nutrition", {}), **patch.nutrition}
                else:
                    recalc_food_nutrition(food)
                if food.get("noSugar") and isinstance(food.get("nutrition"), dict):
                    food["nutrition"]["sugar"] = 0.0
                changed["ok"] = True
                break
        entry["mealSummary"] = calc_meal_summary_from_foods(entry.get("foods", []))
        entry["updatedAt"] = updated_at
        return entry

    updated_log = daily_log_db.update_entry(
        request.patientId, day, request.entryId, updater
    )
    if not updated_log or not changed["ok"]:
        return error_response("NOT_FOUND", "Food not found in entry")

    return {
        "success": True,
        "data": {
            "patientId": request.patientId,
            "entryId": request.entryId,
            "foodId": request.foodId,
            "updatedAt": updated_at,
        },
    }


@app.post("/delete-food")
async def delete_food(request: DeleteFoodRequest):
    if not request.patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")

    day = find_day_for_entry(request.patientId, request.entryId)
    if not day:
        return error_response("NOT_FOUND", "Entry not found for patient")

    removed = {"ok": False}
    updated_at = now_utc()

    def updater(entry: Dict[str, Any]) -> Dict[str, Any]:
        before = len(entry.get("foods", []))
        entry["foods"] = [
            f for f in entry.get("foods", []) if f.get("foodId") != request.foodId
        ]
        after = len(entry["foods"])
        if before != after:
            removed["ok"] = True
            entry["mealSummary"] = calc_meal_summary_from_foods(entry.get("foods", []))
            entry["updatedAt"] = updated_at
        return entry

    updated_log = daily_log_db.update_entry(
        request.patientId, day, request.entryId, updater
    )
    if not updated_log or not removed["ok"]:
        return error_response("NOT_FOUND", "Food not found in entry")

    updated_entry = get_entry_by_id(updated_log, request.entryId) or {}

    return {
        "success": True,
        "data": {
            "patientId": request.patientId,
            "entryId": request.entryId,
            "deletedFoodId": request.foodId,
            "mealSummary": updated_entry.get("mealSummary", DEFAULT_TOTALS.copy()),
        },
    }


@app.post("/confirm-meal")
async def confirm_meal(request: ConfirmMealRequest):
    if not request.patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")

    day = request.dateKey or find_day_for_entry(request.patientId, request.entryId)
    if not day:
        return error_response("NOT_FOUND", "Entry not found for patient")

    confirmed_at = now_utc() if request.confirmed else None

    def updater(entry: Dict[str, Any]) -> Dict[str, Any]:
        final_data = request.finalData or {}
        if final_data.get("foods"):
            entry["foods"] = final_data["foods"]
        if final_data.get("mealSummary"):
            entry["mealSummary"] = final_data["mealSummary"]
        else:
            entry["mealSummary"] = calc_meal_summary_from_foods(entry.get("foods", []))
        entry["status"] = "confirmed" if request.confirmed else "draft"
        if confirmed_at:
            entry["confirmedAt"] = confirmed_at
        entry["updatedAt"] = now_utc()
        return entry

    updated_log = daily_log_db.update_entry(
        request.patientId, day, request.entryId, updater
    )
    if not updated_log:
        return error_response("NOT_FOUND", "Entry not found for patient")

    return {
        "success": True,
        "data": {
            "patientId": request.patientId,
            "entryId": request.entryId,
            "status": "confirmed" if request.confirmed else "draft",
            "confirmedAt": confirmed_at,
        },
    }


@app.get("/history")
async def history(
    patientId: str = Query(..., description="Patient id"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    if not patientId:
        return error_response("VALIDATION_ERROR", "patientId is required")

    history_data = daily_log_db.get_history(patientId, from_date, to_date)
    return {"success": True, "data": history_data}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
