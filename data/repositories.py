from datetime import datetime

from data.database import init_db
from data.seed import TEMPLATES

LEGACY_USER_EMAIL = "legacy@miniwins.local"


class HabitRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)
        self.user_repository = UserRepository(self.connection)

    def seed_template(self, template_key, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        for habit in TEMPLATES.get(template_key, []):
            self.add_habit(resolved_user_id, habit)

    def add_habit(self, user_id, habit=None):
        if habit is None:
            habit = user_id
            user_id = None
        resolved_user_id = self._resolve_user_id(user_id)
        self._execute(
            """
            INSERT INTO habits (
                user_id, name, category, emoji, frequency, active,
                suggested_time, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                resolved_user_id,
                habit["name"],
                habit.get("category"),
                habit.get("emoji"),
                habit.get("frequency", "daily"),
                int(habit.get("active", True)),
                habit.get("suggested_time"),
                datetime.utcnow().isoformat(),
            ],
        )

    def list_today_habits(self, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        return [
            dict(row)
            for row in self._fetchall(
                "SELECT * FROM habits WHERE user_id = ? AND active = 1 ORDER BY id DESC",
                [resolved_user_id],
            )
        ]

    def list_habits(self, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        return [
            dict(row)
            for row in self._fetchall(
                "SELECT * FROM habits WHERE user_id = ? ORDER BY id DESC",
                [resolved_user_id],
            )
        ]

    def delete_habit(self, habit_id, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        self._execute(
            "DELETE FROM habit_logs WHERE habit_id = ? AND user_id = ?",
            [habit_id, resolved_user_id],
        )
        self._execute(
            "DELETE FROM habits WHERE id = ? AND user_id = ?",
            [habit_id, resolved_user_id],
        )

    def log_action(self, habit_id, status, note=None, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        habit = self._fetchone(
            "SELECT id FROM habits WHERE id = ? AND user_id = ?",
            [habit_id, resolved_user_id],
        )
        if not habit:
            return
        self._execute(
            """
            INSERT INTO habit_logs (habit_id, user_id, date, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                habit_id,
                resolved_user_id,
                datetime.utcnow().date().isoformat(),
                status,
                datetime.utcnow().isoformat(),
            ],
        )

    def list_all_logs(self, user_id=None):
        resolved_user_id = self._resolve_user_id(user_id)
        return [
            dict(row)
            for row in self._fetchall(
                "SELECT * FROM habit_logs WHERE user_id = ? ORDER BY created_at DESC",
                [resolved_user_id],
            )
        ]

    def list_logs_since(self, user_id, since_date):
        resolved_user_id = self._resolve_user_id(user_id)
        return [
            dict(row)
            for row in self._fetchall(
                """
                SELECT * FROM habit_logs
                WHERE user_id = ? AND date >= ?
                ORDER BY created_at DESC
                """,
                [resolved_user_id, since_date],
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

    def _resolve_user_id(self, user_id):
        if user_id is not None:
            return user_id
        return self.user_repository.get_or_create_legacy_user()


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
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            [email, password_hash, datetime.utcnow().isoformat()],
        )
        return cursor.lastrowid

    def get_or_create_legacy_user(self):
        existing = self.get_by_email(LEGACY_USER_EMAIL)
        if existing:
            return existing["id"]
        return self.create_user(LEGACY_USER_EMAIL, "legacy")

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
