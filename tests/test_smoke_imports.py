import importlib
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data import init_db


def test_init_db_importable():
    assert callable(init_db)


def test_app_importable():
    pytest.importorskip("altair")
    pytest.importorskip("pandas")
    pytest.importorskip("streamlit")
    module = importlib.import_module("app")
    assert hasattr(module, "main")
