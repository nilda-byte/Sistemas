from data import init_db


def test_init_db_importable():
    assert callable(init_db)
