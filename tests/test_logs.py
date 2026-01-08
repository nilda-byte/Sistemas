from datetime import datetime, timedelta
import sqlite3

from app import parse_log_timestamp
from data.migrate import ensure_schema
from data.repositories import HabitRepository, UserRepository


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    return connection


def test_list_logs_since_filters_and_normalizes():
    connection = _connection()
    user_repo = UserRepository(connection)
    habit_repo = HabitRepository(connection)

    user_id = user_repo.create_user("logs@example.com", "hash")
    habit_repo.add_habit(user_id, {"name": "Leer", "frequency": "daily", "emoji": "📚"})
    habit_id = habit_repo.list_habits(user_id)[0]["id"]

    base = datetime(2024, 1, 10, 12, 0, 0)
    older = base - timedelta(days=5)
    recent = base - timedelta(days=1)

    connection.execute(
        "INSERT INTO habit_logs (user_id, habit_id, date, status, created_at) VALUES (?, ?, ?, ?, ?)",
        [user_id, habit_id, older.date().isoformat(), "completed", older.isoformat()],
    )
    connection.execute(
        "INSERT INTO habit_logs (user_id, habit_id, date, status, created_at) VALUES (?, ?, ?, ?, ?)",
        [user_id, habit_id, recent.date().isoformat(), "completed", recent.isoformat()],
    )
    connection.commit()

    logs = habit_repo.list_logs_since(user_id, base - timedelta(days=2))
    assert len(logs) == 1
    assert logs[0]["created_at"] == recent.isoformat()
    assert logs[0]["date"] == recent.date().isoformat()


def test_parse_log_timestamp_fallback():
    log = {"timestamp": "2024-01-02T03:04:05"}
    assert parse_log_timestamp(log) == datetime.fromisoformat("2024-01-02T03:04:05")
    assert parse_log_timestamp({"status": "completed"}) is None
