import sqlite3
from pathlib import Path

from data.migrate import ensure_schema

DB_PATH = Path("miniwins.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    ensure_schema(connection)
    return connection


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.connection = init_db()

    def execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        self.connection.commit()
        return cursor

    def fetchall(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchall()

    def fetchone(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchone()
