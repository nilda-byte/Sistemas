import gettext
import os
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen

from data.database import Database
from data.repositories import HabitRepository, SettingsRepository, AuthRepository
from domain.logic import XpCalculator, StreakCalculator, BestHourCalculator, SmartReminderEngine, WildcardRule
from services.notifications import NotificationService
from services.calendar_sync import CalendarService

KV = """
#:import utils ui.utils

<RootScreenManager>:
    SplashScreen:
    LoginScreen:
    OnboardingScreen:
    HomeScreen:

<SplashScreen>:
    name: "splash"
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(12)
        Label:
            text: "MiniWins"
            font_size: "26sp"
        Label:
            text: app.translate("slogan")

<LoginScreen>:
    name: "login"
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(16)
        Label:
            text: app.translate("login_required")
            font_size: "20sp"
        Button:
            text: app.translate("continue_google")
            on_release: root.on_google_login()
        Label:
            text: app.auth_banner
            color: (1, 0.4, 0.4, 1) if app.auth_banner else (0, 0, 0, 0)

<OnboardingScreen>:
    name: "onboarding"
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(10)
        Label:
            text: app.translate("onboarding_title")
            font_size: "20sp"
        Label:
            text: app.translate("slogan")
        Label:
            text: app.translate("onboarding_profile")
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: app.translate("profile_student")
                on_release: root.select_profile("student")
            Button:
                text: app.translate("profile_worker")
                on_release: root.select_profile("worker")
            Button:
                text: app.translate("profile_mixed")
                on_release: root.select_profile("mixed")
        Label:
            text: app.translate("onboarding_template")
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: app.translate("template_study")
                on_release: root.select_template("study")
            Button:
                text: app.translate("template_work")
                on_release: root.select_template("work")
            Button:
                text: app.translate("template_wellbeing")
                on_release: root.select_template("wellbeing")
        Button:
            text: app.translate("template_custom")
            on_release: root.select_template("custom")
        Button:
            text: app.translate("continue_label")
            disabled: not root.can_continue
            on_release: root.finish_onboarding()

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(12)
        Label:
            text: app.translate("home_today")
            font_size: "20sp"
        ScrollView:
            GridLayout:
                id: habits_container
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: app.translate("focus_mode")
                on_release: root.show_focus_mode()
            Button:
                text: app.translate("home_stats")
                on_release: root.show_stats()
            Button:
                text: app.translate("home_settings")
                on_release: root.show_settings()
"""


class RootScreenManager(ScreenManager):
    pass


class SplashScreen(Screen):
    pass


class LoginScreen(Screen):
    def on_google_login(self):
        app = App.get_running_app()
        app.auth_repository.sign_in()
        if app.auth_repository.is_authenticated:
            app.go_to("onboarding")


class OnboardingScreen(Screen):
    profile = StringProperty("")
    template = StringProperty("")
    can_continue = BooleanProperty(False)

    def select_profile(self, profile):
        self.profile = profile
        self._update_continue()

    def select_template(self, template):
        self.template = template
        self._update_continue()
        if template in {"study", "work", "wellbeing"}:
            app = App.get_running_app()
            app.habit_repository.seed_template(template)

    def _update_continue(self):
        self.can_continue = bool(self.profile and self.template)

    def finish_onboarding(self):
        App.get_running_app().go_to("home")


class HomeScreen(Screen):
    def on_pre_enter(self):
        self.refresh_habits()

    def refresh_habits(self):
        container = self.ids.habits_container
        container.clear_widgets()
        app = App.get_running_app()
        for habit in app.habit_repository.get_today_habits():
            container.add_widget(utils.habit_card(habit, app))

    def show_focus_mode(self):
        App.get_running_app().notification_service.notify(
            title="MiniWins",
            message=App.get_running_app().translate("focus_mode"),
            intensity="normal",
        )

    def show_stats(self):
        App.get_running_app().notification_service.notify(
            title="MiniWins",
            message=App.get_running_app().translate("stats_weekly"),
            intensity="soft",
        )

    def show_settings(self):
        App.get_running_app().toggle_language()
        self.refresh_habits()


class MiniWinsApp(App):
    auth_banner = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = Database()
        self.habit_repository = HabitRepository(self.database)
        self.settings_repository = SettingsRepository(self.database)
        self.auth_repository = AuthRepository(self.database)
        self.notification_service = NotificationService()
        self.calendar_service = CalendarService()
        self._translator = None
        self._current_language = self.settings_repository.get_language()

    def build(self):
        Window.clearcolor = (0.96, 0.96, 0.98, 1)
        Builder.load_string(KV)
        if not self.auth_repository.is_authenticated:
            self.auth_banner = self.translate("auth_mock")
        return RootScreenManager()

    def on_start(self):
        self.go_to("login" if not self.auth_repository.is_authenticated else "home")

    def go_to(self, screen_name):
        self.root.current = screen_name

    def translate(self, key):
        self._ensure_translator()
        return self._translator.gettext(key)

    def _ensure_translator(self):
        locale_dir = os.path.join(os.path.dirname(__file__), "locales")
        self._translator = gettext.translation(
            "app",
            localedir=locale_dir,
            languages=[self._current_language],
            fallback=True,
        )

    def toggle_language(self):
        self._current_language = "es" if self._current_language == "en" else "en"
        self.settings_repository.set_language(self._current_language)
        self._ensure_translator()


if __name__ == "__main__":
    MiniWinsApp().run()
