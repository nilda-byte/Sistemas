"""Data layer package for MiniWins."""
from data.database import get_connection, init_db

__all__ = ["get_connection", "init_db"]
