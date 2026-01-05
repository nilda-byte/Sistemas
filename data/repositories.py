from datetime import datetime
from typing import List, Optional

from data.database import get_connection
from data.seed import TEMPLATES


def row_to_dict(row):
    return dict(row) if row else None


class UserRepository:
    def __init__(self):
        self.connection = get_connection()

    def get_by_email(self, email: str):
        cursor = self.connection.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return row_to_dict(row)

    def create_user(self, email: str, password_hash: str):
        self.connection.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash),
        )
        self.connection.commit()


class SettingsRepository:
    def __init__(self):
        self.connection = get_connection()

    def get(self, user_id: int, key: str, default: str):
        cursor = self.connection.execute(
            "SELECT value FROM settings WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        row = cursor.fetchone()
        return row["value"] if row else default

    def set(self, user_id: int, key: str, value: str):
        self.connection.execute(
            "INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value),
        )
        self.connection.commit()


class HabitRepository:
    def __init__(self):
        self.connection = get_connection()

    def seed_template(self, user_id: int, template_key: str):
        for habit in TEMPLATES.get(template_key, []):
            self.add_habit(user_id, habit)

    def add_habit(self, user_id: int, habit: dict):
        self.connection.execute(
            """
            INSERT INTO habits (user_id, name, emoji, frequency, days, target_count, suggested_time, reminders_enabled, calendar_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                habit["name"],
                habit["emoji"],
                habit["frequency"],
                habit.get("days"),
                habit.get("target_count"),
                habit.get("suggested_time"),
                int(habit.get("reminders_enabled", True)),
                int(habit.get("calendar_sync", False)),
            ),
        )
        self.connection.commit()

    def update_habit(self, habit_id: int, payload: dict):
        self.connection.execute(
            """
            UPDATE habits
            SET name = ?, emoji = ?, frequency = ?, days = ?, target_count = ?, suggested_time = ?, reminders_enabled = ?, calendar_sync = ?
            WHERE id = ?
            """,
            (
                payload["name"],
                payload["emoji"],
                payload["frequency"],
                payload.get("days"),
                payload.get("target_count"),
                payload.get("suggested_time"),
                int(payload.get("reminders_enabled", True)),
                int(payload.get("calendar_sync", False)),
                habit_id,
            ),
        )
        self.connection.commit()

    def delete_habit(self, habit_id: int):
        self.connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.connection.commit()

    def list_habits(self, user_id: int):
        cursor = self.connection.execute("SELECT * FROM habits WHERE user_id = ?", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def list_today_habits(self, user_id: int):
        return self.list_habits(user_id)

    def log_action(self, habit_id: int, status: str, note: Optional[str]):
        self.connection.execute(
            "INSERT INTO habit_logs (habit_id, timestamp, status, note) VALUES (?, ?, ?, ?)",
            (habit_id, datetime.utcnow().isoformat(), status, note),
        )
        self.connection.commit()

    def list_logs(self, habit_id: int, days: int = 14):
        cursor = self.connection.execute(
            "SELECT * FROM habit_logs WHERE habit_id = ? ORDER BY timestamp DESC",
            (habit_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_all_logs(self, user_id: int):
        cursor = self.connection.execute(
            """
            SELECT habit_logs.* FROM habit_logs
            JOIN habits ON habits.id = habit_logs.habit_id
            WHERE habits.user_id = ?
            """,
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
