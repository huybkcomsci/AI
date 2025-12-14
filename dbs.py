"""
SQLite-backed storage for patient daily nutrition logs.

Schema (table daily_logs):
- patient_id (TEXT, PK with day)
- day (TEXT, YYYY-MM-DD)
- daily_totals (JSON string)
- meals (JSON string)
- last_updated (ISO timestamp)
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent / "nutrition.db"


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
            "daily_totals": daily_totals,
            "meals": meals,
            "last_updated": last_updated,
        }

    def get_patient_logs(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return all logs for a patient (empty list if none)."""
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

    def upsert_daily_log(
        self,
        patient_id: str,
        day: str,
        daily_totals: Dict[str, Any],
        meals: List[Dict[str, Any]],
        last_updated: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create/update a daily log."""
        last_updated = last_updated or datetime.now().isoformat()
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
            "daily_totals": daily_totals,
            "meals": meals,
            "last_updated": last_updated,
        }

    def delete_daily_log(self, patient_id: str, day: str) -> bool:
        """Delete a log, return True if removed."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_logs WHERE patient_id = ? AND day = ?",
                (patient_id, day),
            )
            conn.commit()
            return cursor.rowcount > 0
