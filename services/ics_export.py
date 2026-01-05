from datetime import datetime, timedelta


def generate_ics(habits):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MiniWins//EN"]
    now = datetime.utcnow()
    for habit in habits:
        if not habit.get("suggested_time"):
            continue
        try:
            dt = datetime.strptime(habit["suggested_time"], "%H:%M")
        except ValueError:
            continue
        start = now.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
        end = start + timedelta(minutes=10)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"SUMMARY:MiniWins: {habit['name']}",
                f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\n".join(lines)
