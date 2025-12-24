from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nutrition_pipeline_advanced import NutritionPipelineAdvanced
from dbs import DailyLogDB, DEFAULT_TOTALS
from server_ai import router as server_ai_router
from vietnamese_foods_extended import (
    UNIT_CONVERSION,
    VIETNAMESE_FOODS_NUTRITION,
    calculate_nutrition,
    estimate_weight,
    load_learned_foods,
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
app.include_router(server_ai_router)


# ----------------------------
# Request models (spec)
# ----------------------------
class AnalyzeRequest(BaseModel):
    patientId: str = Field(..., description="Unique patient id")
    userId: Optional[str] = "default"
    text: str
    dateKey: str
    locale: Optional[str] = "vi-VN"


class AnalyzeWithDateRequest(BaseModel):
    patientId: str = Field(..., description="Unique patient id")
    userId: Optional[str] = "default"
    text: str
    date: str = Field(..., description="YYYY-MM-DD date to save this entry")
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


class ReviewPendingFoodRequest(BaseModel):
    pendingId: int = Field(..., description="pending_foods.id")
    decision: str = Field(..., description="approve|reject")
    canonicalName: Optional[str] = None
    action: Optional[str] = Field(None, description="alias|new_food")
    foodData: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            # Chỉ hiển thị ví dụ tối giản để tránh phải gửi thêm field không cần thiết.
            "example": {
                "pendingId": 1,
                "decision": "approve",
                "action": "alias",
            }
        }


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


def _run_analyze(
    patient_id: str,
    user_id: Optional[str],
    text: str,
    date_key: str,
    locale: Optional[str],
) -> Dict[str, Any]:
    """Shared analyze handler so different endpoints can save to a specific date."""
    if not patient_id:
        return error_response("VALIDATION_ERROR", "patientId is required")
    if not date_key:
        return error_response("VALIDATION_ERROR", "dateKey is required")

    result = pipeline.process_input(text)
    entry_id = str(int(datetime.utcnow().timestamp() * 1000))
    mapped_foods = to_spec_foods(result.get("foods", []))
    meal_summary = to_meal_summary(result.get("meal_summary", {}))

    confidence_values = []
    for food in result.get("foods", []):
        try:
            confidence_values.append(float(food.get("confidence", 0) or 0))
        except Exception:
            continue
    confidence_meta = None
    if confidence_values:
        confidence_meta = {
            "min": min(confidence_values),
            "max": max(confidence_values),
            "avg": sum(confidence_values) / len(confidence_values),
        }

    deepseek_meta = {
        "used": bool(result.get("deepseek_used")),
        "available": bool(result.get("deepseek_available")),
        "success": bool(result.get("deepseek_success")),
        "trigger": result.get("deepseek_trigger"),
        "error": result.get("deepseek_error"),
        "analysis": result.get("deepseek_analysis"),
        "suggestions": result.get("deepseek_suggestions") or [],
        "raw": result.get("deepseek_raw") if result.get("deepseek_success") else None,
    }

    entry = {
        "entryId": entry_id,
        "text": text,
        "userId": user_id,
        "foods": mapped_foods,
        "mealSummary": meal_summary,
        "createdAt": now_utc(),
        "status": "draft",
    }
    daily_log_db.append_entry(patient_id, date_key, entry)

    return {
        "success": True,
        "data": {
            "foods": mapped_foods,
            "mealSummary": meal_summary,
        },
        "meta": {
            "patientId": patient_id,
            "requestId": entry_id,
            "entryId": entry_id,
            "createdAt": entry["createdAt"],
            "processingMethod": result.get("processing_method"),
            **({"confidence": confidence_meta} if confidence_meta else {}),
            "deepseek": deepseek_meta,
        },
    }


# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def health():
    return {"message": "Nutrition Chat API", "status": "running"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    return _run_analyze(
        request.patientId,
        request.userId,
        request.text,
        request.dateKey,
        request.locale,
    )


@app.post("/analyze-with-date")
async def analyze_with_date(request: AnalyzeWithDateRequest):
    return _run_analyze(
        request.patientId,
        request.userId,
        request.text,
        request.date,
        request.locale,
    )


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


@app.get("/foods")
async def list_foods(
    q: Optional[str] = Query(None, description="Search by food name"),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    query = (q or "").strip().lower()

    foods = []
    for food_name, data in VIETNAMESE_FOODS_NUTRITION.items():
        if query and query not in str(food_name).lower():
            continue
        data = data or {}
        aliases = data.get("aliases", [])
        if not isinstance(aliases, list):
            aliases = []

        foods.append(
            {
                "foodName": food_name,
                "category": data.get("category"),
                "aliases": aliases,
            }
        )

    foods.sort(key=lambda x: str(x.get("foodName", "")).lower())
    sliced = foods[offset : offset + limit]

    units = []
    for unit_name in sorted(UNIT_CONVERSION.keys()):
        info = UNIT_CONVERSION.get(unit_name) or {}
        if isinstance(info, dict):
            units.append({"unit": unit_name, **info})
        else:
            units.append({"unit": unit_name})

    return {
        "success": True,
        "data": {
            "foods": sliced,
            "totalFoods": len(foods),
            "units": units,
        },
    }


@app.get("/admin/pending-foods")
async def admin_pending_foods(
    status: str = Query("pending", description="pending|approved|rejected"),
    action: Optional[str] = Query(None, description="alias|new_food"),
    q: Optional[str] = Query(None, description="Search raw/canonical names"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    items = pipeline.learning_db.get_pending_foods(
        status=status,
        action=action,
        query=q,
        limit=limit,
        offset=offset,
    )
    return {"success": True, "data": {"items": items}}


@app.post("/admin/review-pending-food")
async def admin_review_pending_food(request: ReviewPendingFoodRequest):
    decision = (request.decision or "").strip().lower()
    if decision not in {"approve", "reject"}:
        return error_response("VALIDATION_ERROR", "decision must be approve|reject")

    pending = pipeline.learning_db.get_pending_food(request.pendingId)
    if not pending:
        return error_response("NOT_FOUND", "Pending food not found")

    if decision == "reject":
        ok = pipeline.learning_db.reject_pending_food(request.pendingId)
        if not ok:
            return error_response("NOT_FOUND", "Pending food not found")
        updated = pipeline.learning_db.get_pending_food(request.pendingId)
        return {"success": True, "data": {"pending": updated}}

    # Mặc định luôn coi là new_food nếu client không chỉ định.
    action = (request.action or "new_food").strip().lower()
    if action and action not in {"alias", "new_food"}:
        return error_response("VALIDATION_ERROR", "action must be alias|new_food")

    approved = pipeline.learning_db.approve_pending_food(
        request.pendingId,
        canonical_name=request.canonicalName,
        action=action or None,
        food_data=request.foodData,
        source="admin",
    )
    if not approved:
        return error_response("NOT_FOUND", "Pending food not found")

    # Refresh in-memory dataset & matcher so approval takes effect without restart.
    load_learned_foods(force=True)
    pipeline.extractor.matcher.build_index()

    return {"success": True, "data": {"pending": approved}}


@app.get("/analytics/food-trends")
async def analytics_food_trends(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    limit: int = Query(20, ge=1, le=200),
):
    food_counts: Dict[str, int] = defaultdict(int)
    food_patients: Dict[str, set] = defaultdict(set)
    day_food_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    days_seen: set = set()

    for patient_id, day, entries in daily_log_db.iter_entries_all_patients(from_date, to_date):
        days_seen.add(day)
        for entry in entries or []:
            for food in entry.get("foods", []) or []:
                name = food.get("foodName") or food.get("food_name")
                if not name:
                    continue
                name = str(name).strip()
                if not name:
                    continue
                food_counts[name] += 1
                food_patients[name].add(patient_id)
                day_food_counts[day][name] += 1

    days = sorted(days_seen)
    ranked = sorted(food_counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    top_foods = [
        {
            "foodName": food_name,
            "count": count,
            "uniquePatients": len(food_patients.get(food_name, set())),
        }
        for food_name, count in ranked
    ]

    trend = {
        "days": days,
        "foods": {
            food_name: [day_food_counts[day].get(food_name, 0) for day in days]
            for food_name, _ in ranked
        },
    }

    return {
        "success": True,
        "data": {
            "from": from_date,
            "to": to_date,
            "topFoods": top_foods,
            "trend": trend,
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
