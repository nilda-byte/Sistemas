from datetime import datetime
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


def habit_card(habit, app):
    card = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8), size_hint_y=None)
    card.height = dp(120)
    title = Label(text=f"{habit['emoji']} {habit['name']}", size_hint_y=None, height=dp(24))
    actions = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
    complete = Button(text=app.translate("quick_complete"))
    postpone = Button(text=app.translate("quick_postpone"))
    skip = Button(text=app.translate("quick_skip"))

    complete.bind(on_release=lambda *_: app.habit_repository.log_action(habit["id"], "completed"))
    postpone.bind(on_release=lambda *_: app.habit_repository.log_action(habit["id"], "postponed"))
    skip.bind(on_release=lambda *_: app.habit_repository.log_action(habit["id"], "skipped"))

    actions.add_widget(complete)
    actions.add_widget(postpone)
    actions.add_widget(skip)
    card.add_widget(title)
    card.add_widget(actions)
    return card
