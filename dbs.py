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
from typing import Any, Dict, List, Optional


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
