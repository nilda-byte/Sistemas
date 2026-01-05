from data import init_db


def test_init_db_smoke():
    connection = init_db()
    cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "users" in tables
