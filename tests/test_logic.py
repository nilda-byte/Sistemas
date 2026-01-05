import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta

from domain.logic import StreakCalculator, XpCalculator, BestHourCalculator, SmartReminderEngine, WildcardRule


class LogicTests(unittest.TestCase):
    def test_streak_calculator(self):
        today = datetime(2024, 3, 10).date()
        logs = [
            {"timestamp": datetime(2024, 3, 10, 8, 0), "status": "completed"},
            {"timestamp": datetime(2024, 3, 9, 8, 0), "status": "completed"},
            {"timestamp": datetime(2024, 3, 7, 8, 0), "status": "completed"},
        ]
        self.assertEqual(2, StreakCalculator().calculate(logs, today))

    def test_xp_calculator(self):
        result = XpCalculator().calculate(total_xp=90, streak=3)
        self.assertEqual(16, result["earned"])
        self.assertEqual(106, result["total"])
        self.assertEqual(2, result["level"])

    def test_best_hour_calculator(self):
        logs = [
            {"timestamp": datetime(2024, 3, 10, 19, 10), "status": "completed"},
            {"timestamp": datetime(2024, 3, 11, 19, 40), "status": "completed"},
            {"timestamp": datetime(2024, 3, 12, 19, 50), "status": "completed"},
        ]
        best = BestHourCalculator().best_hour(logs)
        self.assertEqual((19, 40), best)

    def test_wildcard_rule(self):
        today = datetime(2024, 3, 10).date()
        logs = [
            {"timestamp": datetime(2024, 3, 9, 8, 0), "status": "skipped"},
        ]
        rule = WildcardRule()
        self.assertFalse(rule.has_wildcard(logs, today))
        self.assertTrue(rule.has_wildcard([], today))

    def test_smart_reminder(self):
        logs = [
            {"timestamp": datetime.utcnow() - timedelta(days=1), "status": "postponed"},
            {"timestamp": datetime.utcnow() - timedelta(days=2), "status": "postponed"},
            {"timestamp": datetime.utcnow() - timedelta(days=3), "status": "postponed"},
        ]
        result = SmartReminderEngine().analyze(logs)
        self.assertEqual("soft", result["intensity"])


if __name__ == "__main__":
    unittest.main()
