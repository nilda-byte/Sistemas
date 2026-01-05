import json
from datetime import datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from data.database import init_db
from data.repositories import HabitRepository, SettingsRepository
from domain.logic import BestHourCalculator, StreakCalculator, XpCalculator, WildcardRule
from services.auth import AuthService, DEMO_EMAIL
from services.ics_export import generate_ics
from services.smart_reminders import SmartReminderService
from services.theming import apply_theme

DB_CONN = init_db()


def load_translations(lang: str):
    path = Path("i18n") / f"{lang}.json"
    if not path.exists():
        path = Path("i18n") / "es_419.json"
    return json.loads(path.read_text(encoding="utf-8"))


def t(key: str):
    translations = st.session_state.get("translations", {})
    return translations.get(key, key)


def ensure_session():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("language", "es_419")
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("template", None)
    st.session_state.setdefault("onboarded", False)


def render_header():
    try:
        st.image("assets/street_art_header.svg", use_column_width=True)
    except Exception:
        st.markdown("## MiniWins")


def login_screen(auth_service: AuthService):
    render_header()
    st.markdown(f"### {t('login_title')}")
    st.caption(t("login_required"))

    email = st.text_input(t("email"), value=DEMO_EMAIL)
    password = st.text_input(t("password"), type="password")

    if st.button(t("login")):
        user = auth_service.authenticate(email, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("OK")
            st.experimental_rerun()
        else:
            st.error(t("invalid_credentials"))


def onboarding_screen(habit_repo: HabitRepository, settings_repo: SettingsRepository):
    render_header()
    st.markdown(f"### {t('onboarding_title')}")
    st.write(t("slogan"))

    profile = st.radio(
        t("onboarding_profile"),
        [t("profile_student"), t("profile_worker"), t("profile_mixed")],
        horizontal=True,
    )
    template = st.selectbox(
        t("onboarding_template"),
        [t("template_study"), t("template_work"), t("template_wellbeing"), t("template_custom")],
    )

    if st.button(t("continue_label")):
        st.session_state.profile = profile
        st.session_state.template = template
        settings_repo.set(st.session_state.user["id"], "profile", profile)
        settings_repo.set(st.session_state.user["id"], "onboarded", "1")
        if template != t("template_custom"):
            mapping = {
                t("template_study"): "study",
                t("template_work"): "work",
                t("template_wellbeing"): "wellbeing",
            }
            habit_repo.seed_template(st.session_state.user["id"], mapping[template])
        st.session_state.onboarded = True


def today_screen(habit_repo: HabitRepository, settings_repo: SettingsRepository):
    st.markdown(f"## {t('home_today')}")
    habits = habit_repo.list_today_habits(st.session_state.user["id"])

    for habit in habits:
        with st.container(border=True):
            st.markdown(f"### {habit['emoji']} {habit['name']}")
            col1, col2, col3 = st.columns(3)
            if col1.button(t("quick_complete"), key=f"complete_{habit['id']}"):
                habit_repo.log_action(habit["id"], "completed", None)
            if col2.button(t("quick_postpone"), key=f"postpone_{habit['id']}"):
                habit_repo.log_action(habit["id"], "postponed", "15")
            if col3.button(t("quick_skip"), key=f"skip_{habit['id']}"):
                note = st.text_input(t("skip_reason"), key=f"note_{habit['id']}")
                habit_repo.log_action(habit["id"], "skipped", note or None)

    logs = habit_repo.list_all_logs(st.session_state.user["id"])
    parsed_logs = [
        {"timestamp": datetime.fromisoformat(log["timestamp"]), "status": log["status"]}
        for log in logs
    ]
    streak = StreakCalculator().calculate(parsed_logs)
    xp_result = XpCalculator().calculate(total_xp=0, streak=streak)
    wildcard = WildcardRule().has_wildcard(parsed_logs)

    st.info(f"{t('streak')}: {streak} | {t('xp_earned')}: {xp_result['earned']}")
    if wildcard:
        st.info(t("wildcard_available"))

    pomodoro_choice = st.selectbox(t("focus_mode"), [t("pomodoro_25"), t("pomodoro_50")])
    if st.button(t("start")):
        duration = 25 if pomodoro_choice == t("pomodoro_25") else 50
        st.session_state.pomodoro_start = datetime.utcnow()
        st.session_state.pomodoro_duration = duration

    if "pomodoro_start" in st.session_state:
        elapsed = datetime.utcnow() - st.session_state.pomodoro_start
        remaining = max(0, st.session_state.pomodoro_duration * 60 - int(elapsed.total_seconds()))
        st.progress(1 - remaining / (st.session_state.pomodoro_duration * 60))
        st.caption(f"{remaining // 60}:{remaining % 60:02d}")

    reminder_service = SmartReminderService()
    dnd_start = int(settings_repo.get(st.session_state.user["id"], "dnd_start", "22"))
    dnd_end = int(settings_repo.get(st.session_state.user["id"], "dnd_end", "7"))
    recommendation = reminder_service.build_recommendation(logs, dnd_start, dnd_end)
    if recommendation["suggested"]:
        hour, minute = recommendation["suggested"]
        st.info(f"{t('reminder_suggestion')}: {hour:02d}:{minute:02d}")
    if recommendation["intensity"] == "soft":
        st.warning(t("intensity_soft"))

    calendar_data = generate_ics(habits)
    st.download_button(
        t("download_calendar"),
        data=calendar_data,
        file_name="miniwins.ics",
        mime="text/calendar",
    )


def habits_screen(habit_repo: HabitRepository):
    st.markdown(f"## {t('home_habits')}")

    habits = habit_repo.list_habits(st.session_state.user["id"])
    if habits:
        for habit in habits:
            with st.container(border=True):
                st.write(f"{habit['emoji']} {habit['name']}")
                if st.button(t("delete"), key=f"delete_{habit['id']}"):
                    habit_repo.delete_habit(habit["id"])
                    st.experimental_rerun()

    st.markdown(f"### {t('new_habit')}")
    name = st.text_input(t("habit_name"))
    emoji = st.text_input(t("habit_emoji"), value="✨")
    frequency = st.selectbox(t("habit_frequency"), ["daily", "weekly"])
    days = st.multiselect(
        t("habit_days"),
        ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        disabled=frequency == "daily",
    )
    target = st.number_input(t("habit_target"), min_value=0, step=1)
    time = st.text_input(t("habit_time"), value="19:30")
    reminders = st.checkbox(t("habit_reminders"), value=True)
    calendar = st.checkbox(t("habit_calendar"), value=False)

    if st.button(t("save")):
        habit_repo.add_habit(
            st.session_state.user["id"],
            {
                "name": name,
                "emoji": emoji,
                "frequency": frequency,
                "days": ",".join(days) if days else None,
                "target_count": target if target > 0 else None,
                "suggested_time": time if time else None,
                "reminders_enabled": reminders,
                "calendar_sync": calendar,
            },
        )
        st.experimental_rerun()


def stats_screen(habit_repo: HabitRepository):
    st.markdown(f"## {t('stats_title')}")

    logs = habit_repo.list_all_logs(st.session_state.user["id"])
    rows = [
        {
            "date": datetime.fromisoformat(log["timestamp"]).date(),
            "status": log["status"],
            "habit_id": log["habit_id"],
            "timestamp": datetime.fromisoformat(log["timestamp"]),
        }
        for log in logs
    ]
    if not rows:
        st.info(t("no_data"))
        return

    df = pd.DataFrame(rows)
    habits = habit_repo.list_habits(st.session_state.user["id"])
    habit_map = {habit["id"]: habit["name"] for habit in habits}
    df["habit_name"] = df["habit_id"].map(habit_map).fillna("Habit")
    completed = df[df["status"] == "completed"]

    st.subheader(t("daily_completions"))
    daily_counts = completed.groupby("date").size().reset_index(name="count")
    bar = alt.Chart(daily_counts).mark_bar(color="#3cffd0").encode(x="date:T", y="count:Q")
    st.altair_chart(bar, use_container_width=True)

    st.subheader(t("habit_completion_rate"))
    habit_counts = completed.groupby("habit_name").size().reset_index(name="count")
    bar2 = alt.Chart(habit_counts).mark_bar(color="#6b5bff").encode(x="habit_name:N", y="count:Q")
    st.altair_chart(bar2, use_container_width=True)

    best_hour = BestHourCalculator().best_hour(
        [{"timestamp": row["timestamp"], "status": row["status"]} for row in rows]
    )
    if best_hour:
        st.info(f"{t('best_hour')}: {best_hour[0]:02d}:{best_hour[1]:02d}")

    consistency = round((len(completed) / max(len(df), 1)) * 100, 2)
    st.metric(t("weekly_consistency"), f"{consistency}%")

    if not completed.empty:
        completed = completed.copy()
        completed["hour"] = completed["timestamp"].dt.hour
        st.subheader(t("best_hour"))
        hour_chart = alt.Chart(completed).mark_bar(color="#ff5bbd").encode(x="hour:O", y="count():Q")
        st.altair_chart(hour_chart, use_container_width=True)

        total_by_habit = df.groupby("habit_name").size()
        completed_by_habit = completed.groupby("habit_name").size()
        rates = (completed_by_habit / total_by_habit).fillna(0).reset_index(name="rate")
        rate_chart = alt.Chart(rates).mark_bar(color="#3cffd0").encode(x="habit_name:N", y="rate:Q")
        st.altair_chart(rate_chart, use_container_width=True)

        strongest = rates.sort_values("rate", ascending=False).head(1)
        weakest = rates.sort_values("rate", ascending=True).head(1)
        if not strongest.empty:
            st.success(f"{t('strongest_habit')}: {strongest.iloc[0]['habit_name']}")
        if not weakest.empty:
            st.warning(f"{t('weakest_habit')}: {weakest.iloc[0]['habit_name']}")

        streaks = []
        for habit_id, group in df.groupby("habit_id"):
            logs_for_habit = [
                {"timestamp": row["timestamp"], "status": row["status"]}
                for row in group.to_dict("records")
            ]
            streak_value = StreakCalculator().calculate(logs_for_habit)
            streaks.append({"habit_name": habit_map.get(habit_id, str(habit_id)), "streak": streak_value})
        streaks_df = pd.DataFrame(streaks).sort_values("streak", ascending=False).head(5)
        st.subheader(t("streaks_top"))
        streak_chart = alt.Chart(streaks_df).mark_bar(color="#6b5bff").encode(x="habit_name:N", y="streak:Q")
        st.altair_chart(streak_chart, use_container_width=True)


def settings_screen(settings_repo: SettingsRepository):
    st.markdown(f"## {t('home_settings')}")
    current_language = settings_repo.get(st.session_state.user["id"], "language", "es_419")
    language = st.selectbox(t("language"), ["es_419", "en"], index=0 if current_language == "es_419" else 1)
    dnd_start = st.number_input(
        t("dnd_start"), min_value=0, max_value=23, value=int(settings_repo.get(st.session_state.user["id"], "dnd_start", "22"))
    )
    dnd_end = st.number_input(
        t("dnd_end"), min_value=0, max_value=23, value=int(settings_repo.get(st.session_state.user["id"], "dnd_end", "7"))
    )

    if st.button(t("save")):
        settings_repo.set(st.session_state.user["id"], "language", language)
        settings_repo.set(st.session_state.user["id"], "dnd_start", str(dnd_start))
        settings_repo.set(st.session_state.user["id"], "dnd_end", str(dnd_end))
        st.session_state.language = language
        st.session_state.translations = load_translations(language)


def main():
    st.set_page_config(page_title="MiniWins", layout="wide")
    apply_theme()

    ensure_session()
    auth_service = AuthService()
    habit_repo = HabitRepository()
    settings_repo = SettingsRepository()

    language = settings_repo.get(st.session_state.user["id"], "language", "es_419") if st.session_state.user else "es_419"
    st.session_state.language = language
    st.session_state.translations = load_translations(language)

    if not st.session_state.authenticated:
        login_screen(auth_service)
        return

    if st.session_state.user and not st.session_state.get("onboarded"):
        st.session_state.onboarded = settings_repo.get(st.session_state.user["id"], "onboarded", "0") == "1"

    if not st.session_state.get("onboarded"):
        onboarding_screen(habit_repo, settings_repo)
        return

    st.sidebar.title("MiniWins")
    menu = st.sidebar.radio("", [t("home_today"), t("home_habits"), t("home_stats"), t("home_settings")])
    if st.sidebar.button(t("logout")):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.onboarded = False
        st.experimental_rerun()

    if menu == t("home_today"):
        today_screen(habit_repo, settings_repo)
    elif menu == t("home_habits"):
        habits_screen(habit_repo)
    elif menu == t("home_stats"):
        stats_screen(habit_repo)
    else:
        settings_screen(settings_repo)


if __name__ == "__main__":
    main()
