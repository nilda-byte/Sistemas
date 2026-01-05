from collections import Counter
from datetime import datetime, timedelta


class StreakCalculator:
    def calculate(self, logs, today=None):
        today = today or datetime.utcnow().date()
        completed = {log["timestamp"].date() for log in logs if log["status"] == "completed"}
        streak = 0
        cursor = today
        while cursor in completed:
            streak += 1
            cursor -= timedelta(days=1)
        return streak


class XpCalculator:
    def __init__(self, base_xp=10, streak_bonus=2):
        self.base_xp = base_xp
        self.streak_bonus = streak_bonus

    def calculate(self, total_xp, streak):
        earned = self.base_xp + (streak * self.streak_bonus)
        new_total = total_xp + earned
        level = new_total // 100 + 1
        return {"earned": earned, "total": new_total, "level": level}


class BestHourCalculator:
    def best_hour(self, logs):
        completed = [log for log in logs if log["status"] == "completed"]
        if not completed:
            return None
        hours = Counter([log["timestamp"].hour for log in completed])
        best_hour = hours.most_common(1)[0][0]
        minutes = sorted([log["timestamp"].minute for log in completed if log["timestamp"].hour == best_hour])
        median_minute = minutes[len(minutes) // 2] if minutes else 0
        return best_hour, median_minute


class WildcardRule:
    def has_wildcard(self, logs, today=None):
        today = today or datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        skipped = [
            log for log in logs
            if log["status"] == "skipped" and log["timestamp"].date() >= start_of_week
        ]
        return len(skipped) < 1


class SmartReminderEngine:
    def __init__(self, best_hour_calculator=None):
        self.best_hour_calculator = best_hour_calculator or BestHourCalculator()

    def analyze(self, logs, dnd_start=22, dnd_end=7):
        cutoff = datetime.utcnow() - timedelta(days=14)
        recent_logs = [log for log in logs if log["timestamp"] >= cutoff]
        best_hour = self.best_hour_calculator.best_hour(recent_logs)
        ignored = len([log for log in recent_logs if log["status"] == "postponed"])
        intensity = "soft" if ignored >= 3 else "normal"
        suggested = None
        if best_hour:
            hour, minute = best_hour
            if not self._is_dnd(hour, dnd_start, dnd_end):
                suggested = (hour, minute)
        return {"suggested": suggested, "intensity": intensity, "allow_rescue": True}

    @staticmethod
    def _is_dnd(hour, start, end):
        if start <= end:
            return start <= hour <= end
        return hour >= start or hour <= end
