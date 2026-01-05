import bcrypt

from data.repositories import UserRepository

DEMO_EMAIL = "demo@miniwins.app"
DEMO_PASSWORD = "Demo1234!"


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.ensure_demo_user()

    def ensure_demo_user(self):
        if not self.user_repo.get_by_email(DEMO_EMAIL):
            password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
            self.user_repo.create_user(DEMO_EMAIL, password_hash)

    def authenticate(self, email: str, password: str):
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None
