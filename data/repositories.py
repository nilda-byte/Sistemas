from datetime import datetime

from data.seed import TEMPLATES


class HabitRepository:
    def __init__(self, db):
        self.db = db

    def seed_template(self, template_key):
        for habit in TEMPLATES.get(template_key, []):
            self.add_habit(habit)

    def add_habit(self, habit):
        self.db.execute(
            """
            INSERT INTO habits (name, emoji, frequency, days, target_count, suggested_time, reminders_enabled, calendar_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
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

    def get_today_habits(self):
        return [dict(row) for row in self.db.fetchall("SELECT * FROM habits")]

    def log_action(self, habit_id, status, note=None):
        self.db.execute(
            "INSERT INTO habit_logs (habit_id, timestamp, status, note) VALUES (?, ?, ?, ?)",
            [habit_id, datetime.utcnow().isoformat(), status, note],
        )


class SettingsRepository:
    def __init__(self, db):
        self.db = db

    def get_language(self):
        row = self.db.fetchone("SELECT value FROM settings WHERE key = 'language'")
        return row["value"] if row else "en"

    def set_language(self, language):
        self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('language', ?)",
            [language],
        )


class AuthRepository:
    def __init__(self, db):
        self.db = db

    @property
    def is_authenticated(self):
        row = self.db.fetchone("SELECT value FROM auth WHERE key = 'authenticated'")
        return row and row["value"] == "1"

    def sign_in(self):
        self.db.execute("INSERT OR REPLACE INTO auth (key, value) VALUES ('authenticated', '1')")

    def sign_out(self):
        self.db.execute("DELETE FROM auth WHERE key = 'authenticated'")
