from datetime import datetime, timedelta

from domain.logic import BestHourCalculator, StreakCalculator, WildcardRule, XpCalculator


def test_streak_calculator():
    today = datetime(2024, 3, 10).date()
    logs = [
        {"timestamp": datetime(2024, 3, 10, 8, 0), "status": "completed"},
        {"timestamp": datetime(2024, 3, 9, 8, 0), "status": "completed"},
        {"timestamp": datetime(2024, 3, 7, 8, 0), "status": "completed"},
    ]
    assert StreakCalculator().calculate(logs, today) == 2


def test_xp_calculator():
    result = XpCalculator().calculate(total_xp=90, streak=3)
    assert result["earned"] == 16
    assert result["total"] == 106
    assert result["level"] == 2


def test_best_hour_calculator():
    logs = [
        {"timestamp": datetime(2024, 3, 10, 19, 10), "status": "completed"},
        {"timestamp": datetime(2024, 3, 11, 19, 40), "status": "completed"},
        {"timestamp": datetime(2024, 3, 12, 19, 50), "status": "completed"},
    ]
    assert BestHourCalculator().best_hour(logs) == (19, 40)


def test_wildcard_rule():
    today = datetime(2024, 3, 10).date()
    logs = [{"timestamp": datetime(2024, 3, 9, 8, 0), "status": "skipped"}]
    rule = WildcardRule()
    assert rule.has_wildcard(logs, today) is False
    assert rule.has_wildcard([], today) is True
