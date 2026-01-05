import sqlite3

from data.migrate import ensure_schema
from data.repositories import HabitRepository, SettingsRepository, UserRepository
from services.auth import AuthService


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    return connection


def test_user_registration_and_login():
    connection = _connection()
    user_repo = UserRepository(connection)
    auth_service = AuthService(user_repo)

    user = auth_service.register("test@example.com", "Password123")
    assert user is not None

    authenticated = auth_service.authenticate("test@example.com", "Password123")
    assert authenticated is not None

    bad_auth = auth_service.authenticate("test@example.com", "badpass")
    assert bad_auth is None


def test_habits_and_logs_are_user_scoped():
    connection = _connection()
    user_repo = UserRepository(connection)
    user_id = user_repo.create_user("habits@example.com", "hash")

    habit_repo = HabitRepository(connection)
    habit_repo.add_habit(user_id, {"name": "Leer", "frequency": "daily"})
    habits = habit_repo.list_habits(user_id)
    assert len(habits) == 1

    habit_id = habits[0]["id"]
    habit_repo.log_action(habit_id, "completed", user_id=user_id)
    logs = habit_repo.list_all_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["user_id"] == user_id


def test_settings_theme_persists():
    connection = _connection()
    user_repo = UserRepository(connection)
    user_id = user_repo.create_user("theme@example.com", "hash")

    settings_repo = SettingsRepository(connection)
    settings_repo.set(user_id, "theme", "nord")
    assert settings_repo.get(user_id, "theme") == "nord"
