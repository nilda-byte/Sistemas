try:
    from jnius import autoclass
except Exception:  # pragma: no cover - optional dependency on desktop
    autoclass = None


class CalendarService:
    def create_event(self, title, description, start_ms, end_ms):
        if not autoclass:
            return False
        ContentValues = autoclass('android.content.ContentValues')
        CalendarContract = autoclass('android.provider.CalendarContract')
        content_resolver = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver()
        values = ContentValues()
        values.put(CalendarContract.Events.TITLE, title)
        values.put(CalendarContract.Events.DESCRIPTION, description)
        values.put(CalendarContract.Events.DTSTART, start_ms)
        values.put(CalendarContract.Events.DTEND, end_ms)
        values.put(CalendarContract.Events.EVENT_TIMEZONE, 'UTC')
        content_resolver.insert(CalendarContract.Events.CONTENT_URI, values)
        return True
