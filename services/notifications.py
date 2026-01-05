from plyer import notification


class NotificationService:
    def notify(self, title, message, intensity="normal"):
        notification.notify(title=title, message=message, timeout=5)
