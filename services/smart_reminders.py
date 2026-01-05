from datetime import datetime

from domain.logic import SmartReminderEngine


class SmartReminderService:
    def __init__(self):
        self.engine = SmartReminderEngine()

    def build_recommendation(self, logs, dnd_start, dnd_end):
        parsed_logs = []
        for log in logs:
            parsed_logs.append({
                "timestamp": datetime.fromisoformat(log["timestamp"]),
                "status": log["status"],
            })
        return self.engine.analyze(parsed_logs, dnd_start=dnd_start, dnd_end=dnd_end)
