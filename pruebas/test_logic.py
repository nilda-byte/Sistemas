"""Compatibilidad: usa las pruebas de tests/test_logic.py."""

__test__ = False

from tests.test_logic import (  # noqa: F401
    test_best_hour_calculator,
    test_streak_calculator,
    test_wildcard_rule,
    test_xp_calculator,
)
