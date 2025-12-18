"""
SQLite-backed storage for patient daily nutrition logs.

Schema:
- patients: patient_id (TEXT PK), created_at
- daily_logs: patient_id (TEXT), day (YYYY-MM-DD), daily_totals (JSON), meals (JSON), last_updated (ISO)
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


DB_PATH = Path(__file__).resolve().parent / "nutrition.db"

DEFAULT_TOTALS = {
    "calories": 0,
    "carbs": 0,
    "sugar": 0,
    "protein": 0,
    "fat": 0,
    "fiber": 0,
}


class DailyLogDB:
    """Lightweight wrapper around sqlite for storing daily logs."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_logs (
                    patient_id TEXT NOT NULL,
                    day TEXT NOT NULL,
                    daily_totals TEXT NOT NULL,
                    meals TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    PRIMARY KEY (patient_id, day)
                )
                """
            )
            conn.commit()

    def ensure_patient(self, patient_id: str) -> None:
        """Create patient row if not exists."""
        if not patient_id:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO patients (patient_id, created_at)
                VALUES (?, ?)
                """,
                (patient_id, datetime.utcnow().isoformat() + "Z"),
            )
            conn.commit()

    def _row_to_log(self, patient_id: str, row: sqlite3.Row) -> Dict[str, Any]:
        day, daily_totals_raw, meals_raw, last_updated = row
        try:
            daily_totals = json.loads(daily_totals_raw)
        except json.JSONDecodeError:
            daily_totals = {}
        try:
            meals = json.loads(meals_raw)
        except json.JSONDecodeError:
            meals = []

        return {
            "patientId": patient_id,
            "day": day,
            "totals": daily_totals or DEFAULT_TOTALS.copy(),
            "entries": meals or [],
            "last_updated": last_updated,
        }

    def get_patient_logs(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return all logs for a patient (empty list if none)."""
        self.ensure_patient(patient_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT day, daily_totals, meals, last_updated
                FROM daily_logs
                WHERE patient_id = ?
                ORDER BY day DESC
                """,
                (patient_id,),
            )
            rows = cursor.fetchall()

        return [self._row_to_log(patient_id, row) for row in rows]

    def get_daily_log(self, patient_id: str, day: str) -> Optional[Dict[str, Any]]:
        """Return a log for a given day or None."""
        self.ensure_patient(patient_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT day, daily_totals, meals, last_updated
                FROM daily_logs
                WHERE patient_id = ? AND day = ?
                """,
                (patient_id, day),
            )
            row = cursor.fetchone()

        if not row:
            return None
        return self._row_to_log(patient_id, row)

    def _recalc_totals(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        totals = DEFAULT_TOTALS.copy()
        for entry in entries or []:
            summary = entry.get("mealSummary", {})
            for key in totals:
                totals[key] += float(summary.get(key, 0) or 0)
        return totals

    def upsert_daily_log(
        self,
        patient_id: str,
        day: str,
        daily_totals: Dict[str, Any],
        meals: List[Dict[str, Any]],
        last_updated: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create/update a daily log. Kept for backward compatibility."""
        last_updated = last_updated or datetime.now().isoformat()
        self.ensure_patient(patient_id)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_logs (patient_id, day, daily_totals, meals, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(patient_id, day) DO UPDATE SET
                    daily_totals = excluded.daily_totals,
                    meals = excluded.meals,
                    last_updated = excluded.last_updated
                """,
                (
                    patient_id,
                    day,
                    json.dumps(daily_totals, ensure_ascii=False),
                    json.dumps(meals, ensure_ascii=False),
                    last_updated,
                ),
            )
            conn.commit()
        return self.get_daily_log(patient_id, day) or {
            "patientId": patient_id,
            "day": day,
            "totals": daily_totals,
            "entries": meals,
            "last_updated": last_updated,
        }

    def save_day(self, patient_id: str, day: str, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Persist a full day's entries and derived totals."""
        self.ensure_patient(patient_id)
        totals = self._recalc_totals(entries)
        return self.upsert_daily_log(patient_id, day, totals, entries)

    def append_entry(self, patient_id: str, day: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Append a new entry to a patient's day."""
        self.ensure_patient(patient_id)
        log = self.get_daily_log(patient_id, day)
        entries = list(log.get("entries", [])) if log else []
        entries.append(entry)
        return self.save_day(patient_id, day, entries)

    def update_entry(
        self,
        patient_id: str,
        day: str,
        entry_id: str,
        updater,
    ) -> Optional[Dict[str, Any]]:
        """
        Apply an updater(entry_dict) -> entry_dict to the matched entry.
        Returns updated day log or None if entry not found.
        """
        log = self.get_daily_log(patient_id, day)
        if not log:
            return None

        entries = []
        found = False
        for entry in log.get("entries", []):
            if entry.get("entryId") == entry_id:
                entry = updater(dict(entry))
                found = True
            entries.append(entry)

        if not found:
            return None

        return self.save_day(patient_id, day, entries)

    def delete_food_in_entry(
        self,
        patient_id: str,
        day: str,
        entry_id: str,
        food_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Delete a food from an entry and recalc totals."""
        def updater(entry: Dict[str, Any]) -> Dict[str, Any]:
            foods = [f for f in entry.get("foods", []) if f.get("foodId") != food_id]
            entry["foods"] = foods
            entry["mealSummary"] = self._recalc_meal_summary(foods)
            return entry

        return self.update_entry(patient_id, day, entry_id, updater)

    def _recalc_meal_summary(self, foods: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {
            "foodCount": len(foods),
            **DEFAULT_TOTALS,
        }
        for food in foods:
            nutrition = food.get("nutrition", {})
            for key in DEFAULT_TOTALS:
                summary[key] += float(nutrition.get(key, 0) or 0)
        return summary

    def delete_daily_log(self, patient_id: str, day: str) -> bool:
        """Delete a log, return True if removed."""
        self.ensure_patient(patient_id)
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_logs WHERE patient_id = ? AND day = ?",
                (patient_id, day),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_history(
        self,
        patient_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a mapping of day -> {totals, entries} within range.
        date_from/date_to inclusive, expect format YYYY-MM-DD.
        """
        self.ensure_patient(patient_id)
        query = """
            SELECT day, daily_totals, meals, last_updated
            FROM daily_logs
            WHERE patient_id = ?
        """
        params: List[Any] = [patient_id]
        if date_from and date_to:
            query += " AND day BETWEEN ? AND ?"
            params.extend([date_from, date_to])
        elif date_from:
            query += " AND day >= ?"
            params.append(date_from)
        elif date_to:
            query += " AND day <= ?"
            params.append(date_to)

        query += " ORDER BY day DESC"

        with self._connect() as conn:
            cursor = conn.execute(query, tuple(params))
            rows = cursor.fetchall()

        days = {}
        for row in rows:
            log = self._row_to_log(patient_id, row)
            days[log["day"]] = {
                "totals": log.get("totals", DEFAULT_TOTALS.copy()),
                "entries": log.get("entries", []),
            }
        return {"patientId": patient_id, "days": days}

    def iter_entries_all_patients(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Iterator[Tuple[str, str, List[Dict[str, Any]]]]:
        """
        Yield (patient_id, day, entries) for all patients within date range (inclusive).
        Expects day format YYYY-MM-DD.
        """
        query = """
            SELECT patient_id, day, meals
            FROM daily_logs
            WHERE 1=1
        """
        params: List[Any] = []

        if date_from and date_to:
            query += " AND day BETWEEN ? AND ?"
            params.extend([date_from, date_to])
        elif date_from:
            query += " AND day >= ?"
            params.append(date_from)
        elif date_to:
            query += " AND day <= ?"
            params.append(date_to)

        query += " ORDER BY day ASC"

        with self._connect() as conn:
            cursor = conn.execute(query, tuple(params))
            for patient_id, day, meals_raw in cursor:
                try:
                    entries = json.loads(meals_raw) if meals_raw else []
                except json.JSONDecodeError:
                    entries = []
                yield patient_id, day, entries or []


class FoodLearningDB:
    """
    SQLite-backed storage for food curation workflow.

    Tables:
    - pending_foods: DeepSeek suggestions awaiting admin approval
    - learned_foods: approved foods (merged into local lookup dataset)
    - learned_aliases: approved alias -> canonical mappings (merged into local lookup dataset)
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_name TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    suggested_action TEXT NOT NULL,
                    confidence REAL,
                    example_input TEXT,
                    source TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    seen_count INTEGER NOT NULL,
                    UNIQUE(raw_name, canonical_name)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_foods (
                    food_name TEXT PRIMARY KEY,
                    food_data TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_aliases (
                    alias TEXT PRIMARY KEY,
                    canonical_name TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_pending_food(
        self,
        raw_name: str,
        canonical_name: str,
        suggested_action: str,
        confidence: Optional[float] = None,
        example_input: Optional[str] = None,
        source: str = "deepseek",
    ) -> None:
        raw_name = (raw_name or "").strip()
        canonical_name = (canonical_name or "").strip()
        suggested_action = (suggested_action or "").strip().lower()

        if not raw_name or not canonical_name:
            return

        if suggested_action not in {"alias", "new_food"}:
            suggested_action = "new_food"

        now = datetime.utcnow().isoformat() + "Z"

        def coerce_conf(val: Optional[float]) -> Optional[float]:
            if val is None:
                return None
            try:
                return float(val)
            except Exception:
                return None

        confidence_value = coerce_conf(confidence)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_foods (
                    raw_name, canonical_name, suggested_action,
                    confidence, example_input, source,
                    status, created_at, updated_at, seen_count
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, 1)
                ON CONFLICT(raw_name, canonical_name) DO UPDATE SET
                    suggested_action = excluded.suggested_action,
                    confidence = CASE
                        WHEN pending_foods.confidence IS NULL THEN excluded.confidence
                        WHEN excluded.confidence IS NULL THEN pending_foods.confidence
                        ELSE MAX(pending_foods.confidence, excluded.confidence)
                    END,
                    example_input = COALESCE(excluded.example_input, pending_foods.example_input),
                    source = excluded.source,
                    updated_at = excluded.updated_at,
                    seen_count = pending_foods.seen_count + 1,
                    status = CASE
                        WHEN pending_foods.status = 'approved' THEN 'approved'
                        ELSE 'pending'
                    END
                """,
                (
                    raw_name,
                    canonical_name,
                    suggested_action,
                    confidence_value,
                    example_input,
                    source,
                    now,
                    now,
                ),
            )
            conn.commit()

    def get_pending_foods(
        self,
        status: str = "pending",
        action: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        status = (status or "pending").strip().lower()
        if status not in {"pending", "approved", "rejected"}:
            status = "pending"

        action = (action or "").strip().lower() or None
        if action and action not in {"alias", "new_food"}:
            action = None

        limit = max(1, min(int(limit or 200), 1000))
        offset = max(0, int(offset or 0))

        sql = """
            SELECT
                id, raw_name, canonical_name, suggested_action,
                confidence, example_input, source,
                status, created_at, updated_at, seen_count
            FROM pending_foods
            WHERE status = ?
        """
        params: List[Any] = [status]

        if action:
            sql += " AND suggested_action = ?"
            params.append(action)

        if query:
            q = f"%{query.strip()}%"
            sql += " AND (raw_name LIKE ? OR canonical_name LIKE ?)"
            params.extend([q, q])

        sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            cursor = conn.execute(sql, tuple(params))
            rows = cursor.fetchall()

        result: List[Dict[str, Any]] = []
        for row in rows:
            (
                row_id,
                raw_name,
                canonical_name,
                suggested_action,
                confidence_value,
                example_input,
                source,
                row_status,
                created_at,
                updated_at,
                seen_count,
            ) = row
            result.append(
                {
                    "id": row_id,
                    "rawName": raw_name,
                    "canonicalName": canonical_name,
                    "suggestedAction": suggested_action,
                    "confidence": confidence_value,
                    "exampleInput": example_input,
                    "source": source,
                    "status": row_status,
                    "createdAt": created_at,
                    "updatedAt": updated_at,
                    "seenCount": seen_count,
                }
            )
        return result

    def get_pending_food(self, pending_id: int) -> Optional[Dict[str, Any]]:
        try:
            pending_id = int(pending_id)
        except Exception:
            return None

        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id, raw_name, canonical_name, suggested_action,
                    confidence, example_input, source,
                    status, created_at, updated_at, seen_count
                FROM pending_foods
                WHERE id = ?
                """,
                (pending_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        (
            row_id,
            raw_name,
            canonical_name,
            suggested_action,
            confidence_value,
            example_input,
            source,
            row_status,
            created_at,
            updated_at,
            seen_count,
        ) = row
        return {
            "id": row_id,
            "rawName": raw_name,
            "canonicalName": canonical_name,
            "suggestedAction": suggested_action,
            "confidence": confidence_value,
            "exampleInput": example_input,
            "source": source,
            "status": row_status,
            "createdAt": created_at,
            "updatedAt": updated_at,
            "seenCount": seen_count,
        }

    def set_pending_status(self, pending_id: int, status: str) -> bool:
        try:
            pending_id = int(pending_id)
        except Exception:
            return False

        status = (status or "").strip().lower()
        if status not in {"pending", "approved", "rejected"}:
            return False

        now = datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE pending_foods SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, pending_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def approve_pending_food(
        self,
        pending_id: int,
        canonical_name: Optional[str] = None,
        action: Optional[str] = None,
        food_data: Optional[Dict[str, Any]] = None,
        source: str = "admin",
    ) -> Optional[Dict[str, Any]]:
        pending = self.get_pending_food(pending_id)
        if not pending:
            return None

        raw_name = (pending.get("rawName") or "").strip()
        canonical_from_pending = (pending.get("canonicalName") or "").strip()
        suggested_action = (pending.get("suggestedAction") or "").strip().lower()

        canonical = (canonical_name or canonical_from_pending).strip()
        chosen_action = (action or suggested_action).strip().lower()
        if chosen_action not in {"alias", "new_food"}:
            chosen_action = suggested_action if suggested_action in {"alias", "new_food"} else "new_food"

        if not canonical:
            return None

        if chosen_action == "alias":
            self.upsert_alias(raw_name, canonical, source=source)
        else:
            minimal_food = {
                "calories_per_100g": 0,
                "carbs_per_100g": 0,
                "sugar_per_100g": 0,
                "protein_per_100g": 0,
                "fat_per_100g": 0,
                "fiber_per_100g": 0,
                "aliases": [raw_name] if raw_name else [canonical],
                "category": "custom",
            }
            merged_food = minimal_food
            if isinstance(food_data, dict) and food_data:
                merged_food = {**minimal_food, **food_data}
                # Ensure the alias is kept.
                aliases = merged_food.get("aliases")
                if not isinstance(aliases, list):
                    aliases = []
                if raw_name and raw_name not in aliases:
                    aliases.append(raw_name)
                if canonical not in aliases:
                    aliases.append(canonical)
                merged_food["aliases"] = aliases

            self.upsert_food(canonical, merged_food, source=source)
            if raw_name and raw_name != canonical:
                self.upsert_alias(raw_name, canonical, source=source)

        self.set_pending_status(pending_id, "approved")
        return self.get_pending_food(pending_id)

    def reject_pending_food(self, pending_id: int) -> bool:
        return self.set_pending_status(pending_id, "rejected")

    def upsert_alias(self, alias: str, canonical_name: str, source: str = "deepseek") -> None:
        alias = (alias or "").strip()
        canonical_name = (canonical_name or "").strip()
        if not alias or not canonical_name:
            return

        now = datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO learned_aliases (alias, canonical_name, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                    canonical_name = excluded.canonical_name,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (alias, canonical_name, source, now, now),
            )
            conn.commit()

    def upsert_food(self, food_name: str, food_data: Dict[str, Any], source: str = "deepseek") -> None:
        food_name = (food_name or "").strip()
        if not food_name:
            return

        now = datetime.utcnow().isoformat() + "Z"
        payload = json.dumps(food_data or {}, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO learned_foods (food_name, food_data, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(food_name) DO UPDATE SET
                    food_data = excluded.food_data,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (food_name, payload, source, now, now),
            )
            conn.commit()

    def get_learned_foods(self) -> Dict[str, Dict[str, Any]]:
        """Return {food_name: food_data_dict}."""
        with self._connect() as conn:
            cursor = conn.execute("SELECT food_name, food_data FROM learned_foods")
            rows = cursor.fetchall()

        foods: Dict[str, Dict[str, Any]] = {}
        for food_name, raw in rows:
            try:
                foods[food_name] = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                foods[food_name] = {}
        return foods

    def get_learned_aliases(self) -> List[Dict[str, str]]:
        """Return list of {alias, canonical_name}."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT alias, canonical_name FROM learned_aliases"
            )
            rows = cursor.fetchall()
        return [{"alias": alias, "canonical_name": canonical} for alias, canonical in rows]
