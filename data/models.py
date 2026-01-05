from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Habit:
    id: int
    user_id: int
    name: str
    emoji: str
    frequency: str
    days: Optional[str]
    target_count: Optional[int]
    suggested_time: Optional[str]
    reminders_enabled: int
    calendar_sync: int


@dataclass
class HabitLog:
    id: int
    habit_id: int
    timestamp: str
    status: str
    note: Optional[str]
