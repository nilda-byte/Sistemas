from __future__ import annotations

import sqlite3
from datetime import datetime


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    _create_tables(connection)
    _ensure_columns(connection)
    connection.commit()


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            emoji TEXT,
            frequency TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            suggested_time TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(habit_id) REFERENCES habits(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS auth (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )


def _ensure_columns(connection: sqlite3.Connection) -> None:
    _add_column_if_missing(
        connection,
        "users",
        "created_at",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(connection, "habits", "user_id", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(connection, "habits", "category", "TEXT")
    _add_column_if_missing(connection, "habits", "emoji", "TEXT")
    _add_column_if_missing(connection, "habits", "active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(connection, "habits", "suggested_time", "TEXT")
    _add_column_if_missing(
        connection,
        "habits",
        "created_at",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(connection, "habit_logs", "user_id", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(connection, "habit_logs", "date", "TEXT NOT NULL DEFAULT ''")
    _add_column_if_missing(connection, "habit_logs", "status", "TEXT NOT NULL DEFAULT ''")
    _add_column_if_missing(
        connection,
        "habit_logs",
        "created_at",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(connection, "settings", "user_id", "INTEGER NOT NULL DEFAULT 1")

    connection.execute(
        "UPDATE users SET created_at = ? WHERE created_at = ''",
        [datetime.utcnow().isoformat()],
    )
    connection.execute(
        "UPDATE habits SET created_at = ? WHERE created_at = ''",
        [datetime.utcnow().isoformat()],
    )
    connection.execute(
        "UPDATE habit_logs SET created_at = ? WHERE created_at = ''",
        [datetime.utcnow().isoformat()],
    )


def _add_column_if_missing(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    if not _table_exists(connection, table):
        return
    if _column_exists(connection, table, column):
        return
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        [table],
    )
    return cursor.fetchone() is not None


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = connection.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


if __name__ == "__main__":
    from data.database import get_connection

    conn = get_connection()
    ensure_schema(conn)
    print("Migration completed.")
