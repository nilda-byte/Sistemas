from datetime import datetime

from data.database import init_db
from data.seed import TEMPLATES


class HabitRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)

    def seed_template(self, user_id, template_key):
        for habit in TEMPLATES.get(template_key, []):
            self.add_habit(user_id, habit)

    def add_habit(self, user_id, habit):
        self._execute(
            """
            INSERT INTO habits (
                user_id, name, emoji, frequency, days, target_count,
                suggested_time, reminders_enabled, calendar_sync
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                user_id,
                habit["name"],
                habit["emoji"],
                habit["frequency"],
                habit.get("days"),
                habit.get("target_count"),
                habit.get("suggested_time"),
                int(habit.get("reminders_enabled", True)),
                int(habit.get("calendar_sync", False)),
            ],
        )

    def list_today_habits(self, user_id):
        return self.list_habits(user_id)

    def list_habits(self, user_id):
        return [
            dict(row)
            for row in self._fetchall(
                "SELECT * FROM habits WHERE user_id = ? ORDER BY id DESC",
                [user_id],
            )
        ]

    def delete_habit(self, habit_id):
        self._execute("DELETE FROM habit_logs WHERE habit_id = ?", [habit_id])
        self._execute("DELETE FROM habits WHERE id = ?", [habit_id])

    def log_action(self, habit_id, status, note=None):
        habit = self._fetchone("SELECT user_id FROM habits WHERE id = ?", [habit_id])
        if not habit:
            return
        self._execute(
            "INSERT INTO habit_logs (habit_id, user_id, timestamp, status, note) VALUES (?, ?, ?, ?, ?)",
            [habit_id, habit["user_id"], datetime.utcnow().isoformat(), status, note],
        )

    def list_all_logs(self, user_id):
        return [
            dict(row)
            for row in self._fetchall(
                "SELECT * FROM habit_logs WHERE user_id = ? ORDER BY timestamp DESC",
                [user_id],
            )
        ]

    def _execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()
        return cursor

    def _fetchall(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchall()

    def _fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchone()

    def _resolve_connection(self, connection):
        if connection is None:
            return init_db()
        return connection.connection if hasattr(connection, "connection") else connection


class SettingsRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)

    def get(self, user_id, key, default=None):
        row = self._fetchone(
            "SELECT value FROM settings WHERE user_id = ? AND key = ?",
            [user_id, key],
        )
        return row["value"] if row else default

    def set(self, user_id, key, value):
        self._execute(
            "INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)",
            [user_id, key, value],
        )

    def _execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()
        return cursor

    def _fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchone()

    def _resolve_connection(self, connection):
        if connection is None:
            return init_db()
        return connection.connection if hasattr(connection, "connection") else connection


class UserRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)

    def get_by_email(self, email):
        row = self._fetchone("SELECT * FROM users WHERE email = ?", [email])
        return dict(row) if row else None

    def create_user(self, email, password_hash):
        cursor = self._execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            [email, password_hash],
        )
        return cursor.lastrowid

    def _execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()
        return cursor

    def _fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchone()

    def _resolve_connection(self, connection):
        if connection is None:
            return init_db()
        return connection.connection if hasattr(connection, "connection") else connection


class AuthRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)

    @property
    def is_authenticated(self):
        row = self._fetchone("SELECT value FROM auth WHERE key = 'authenticated'")
        return row and row["value"] == "1"

    def sign_in(self):
        self._execute("INSERT OR REPLACE INTO auth (key, value) VALUES ('authenticated', '1')")

    def sign_out(self):
        self._execute("DELETE FROM auth WHERE key = 'authenticated'")

    def _execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()
        return cursor

    def _fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchone()

    def _resolve_connection(self, connection):
        if connection is None:
            return init_db()
        return connection.connection if hasattr(connection, "connection") else connection
