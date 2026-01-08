from datetime import date, datetime

from data.database import init_db
from data.seed import TEMPLATES

LEGACY_USER_EMAIL = "legacy@miniwins.local"


class HabitRepository:
    def __init__(self, connection=None):
        self.connection = self._resolve_connection(connection)

    def seed_template(self, user_id, template_key):
        for habit in TEMPLATES.get(template_key, []):
            self.add_habit(user_id, habit)

    def add_habit(self, user_id, habit):
        columns = ["user_id", "name"]
        values = [user_id, habit["name"]]

        if self._column_exists("habits", "category"):
            columns.append("category")
            values.append(habit.get("category"))
        if self._column_exists("habits", "emoji"):
            columns.append("emoji")
            values.append(habit.get("emoji") or "✨")
        if self._column_exists("habits", "frequency"):
            columns.append("frequency")
            values.append(habit.get("frequency", "daily"))
        if self._column_exists("habits", "active"):
            columns.append("active")
            values.append(int(habit.get("active", True)))
        if self._column_exists("habits", "suggested_time"):
            columns.append("suggested_time")
            values.append(habit.get("suggested_time"))
        if self._column_exists("habits", "created_at"):
            columns.append("created_at")
            values.append(datetime.utcnow().isoformat())

        placeholders = ", ".join(["?"] * len(columns))
        self._execute(
            f"INSERT INTO habits ({', '.join(columns)}) VALUES ({placeholders})",
            values,
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

    def delete_habit(self, habit_id, user_id=None):
        self._execute("DELETE FROM habit_logs WHERE habit_id = ?", [habit_id])
        self._execute("DELETE FROM habits WHERE id = ?", [habit_id])

    def log_action(self, habit_id, status, note=None, user_id=None):
        if user_id is None:
            habit = self._fetchone("SELECT user_id FROM habits WHERE id = ?", [habit_id])
            if not habit:
                return
            user_id = habit["user_id"]

        action_time = datetime.utcnow()
        date_value = action_time.date().isoformat()
        created_at_value = action_time.isoformat()

        columns = []
        values = []
        if self._column_exists("habit_logs", "habit_id"):
            columns.append("habit_id")
            values.append(habit_id)
        if self._column_exists("habit_logs", "user_id"):
            columns.append("user_id")
            values.append(user_id)
        if self._column_exists("habit_logs", "status"):
            columns.append("status")
            values.append(status)
        if self._column_exists("habit_logs", "date"):
            columns.append("date")
            values.append(date_value)
        if self._column_exists("habit_logs", "created_at"):
            columns.append("created_at")
            values.append(created_at_value)
        if self._column_exists("habit_logs", "timestamp"):
            columns.append("timestamp")
            values.append(created_at_value)
        if note is not None and self._column_exists("habit_logs", "note"):
            columns.append("note")
            values.append(note)

        placeholders = ", ".join(["?"] * len(columns))
        self._execute(
            f"INSERT INTO habit_logs ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )

    def list_all_logs(self, user_id):
        order_column = self._log_order_column()
        query = f"SELECT * FROM habit_logs WHERE user_id = ? ORDER BY {order_column} DESC"
        return [
            self._normalize_log(dict(row))
            for row in self._fetchall(query, [user_id])
        ]

    def list_logs_since(self, user_id, since_dt):
        since_datetime = self._normalize_since_datetime(since_dt)
        if since_datetime is None:
            return []

        has_created_at = self._column_exists("habit_logs", "created_at")
        has_timestamp = self._column_exists("habit_logs", "timestamp")
        has_date = self._column_exists("habit_logs", "date")
        since_iso = since_datetime.isoformat()
        since_date = since_datetime.date().isoformat()

        if has_created_at and has_timestamp:
            query = (
                "SELECT * FROM habit_logs WHERE user_id = ? AND "
                "((created_at != '' AND created_at >= ?) OR (created_at == '' AND timestamp >= ?)) "
                "ORDER BY COALESCE(NULLIF(created_at, ''), timestamp) DESC"
            )
            params = [user_id, since_iso, since_iso]
        elif has_created_at:
            query = "SELECT * FROM habit_logs WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC"
            params = [user_id, since_iso]
        elif has_timestamp:
            query = "SELECT * FROM habit_logs WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC"
            params = [user_id, since_iso]
        elif has_date:
            query = "SELECT * FROM habit_logs WHERE user_id = ? AND date >= ? ORDER BY date DESC"
            params = [user_id, since_date]
        else:
            return []

        return [self._normalize_log(dict(row)) for row in self._fetchall(query, params)]

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

    def _column_exists(self, table, column):
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

    def _log_order_column(self):
        if self._column_exists("habit_logs", "created_at"):
            if self._column_exists("habit_logs", "timestamp"):
                return "COALESCE(NULLIF(created_at, ''), timestamp)"
            return "created_at"
        if self._column_exists("habit_logs", "timestamp"):
            return "timestamp"
        if self._column_exists("habit_logs", "date"):
            return "date"
        return "id"

    def _normalize_log(self, log):
        created_at_value = log.get("created_at") or log.get("timestamp")
        if created_at_value:
            log["created_at"] = created_at_value
        elif log.get("date"):
            log["created_at"] = f"{log['date']}T00:00:00"

        if not log.get("date") and log.get("created_at"):
            log["date"] = log["created_at"][:10]
        return log

    def _normalize_since_datetime(self, since_dt):
        if isinstance(since_dt, datetime):
            return since_dt
        if isinstance(since_dt, date):
            return datetime.combine(since_dt, datetime.min.time())
        if isinstance(since_dt, str):
            try:
                return datetime.fromisoformat(since_dt)
            except ValueError:
                return None
        return None

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
        columns = ["email", "password_hash"]
        values = [email, password_hash]
        if self._column_exists("users", "created_at"):
            columns.append("created_at")
            values.append(datetime.utcnow().isoformat())
        placeholders = ", ".join(["?"] * len(columns))
        cursor = self._execute(
            f"INSERT INTO users ({', '.join(columns)}) VALUES ({placeholders})",
            values,
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

    def _column_exists(self, table, column):
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

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
