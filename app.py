import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from data.database import init_db
from data.repositories import HabitRepository, SettingsRepository, UserRepository
from data.seed import TEMPLATES
from domain.logic import BestHourCalculator, StreakCalculator, XpCalculator, WildcardRule
from services.auth import AuthService, DEMO_EMAIL, DEMO_PASSWORD
from services.ics_export import generate_ics
from services.smart_reminders import SmartReminderService
from services.theming import apply_theme, theme_options

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
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("email", None)
    st.session_state.setdefault("language", "es_419")
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("template", None)
    st.session_state.setdefault("onboarded", False)
    st.session_state.setdefault("theme", "catppuccin-latte")


def render_header():
    st.markdown("# MiniWins")
    st.caption("Hoy cuenta. Cada mini win suma.")


def parse_log_timestamp(log):
    raw_value = log.get("created_at") or log.get("timestamp")
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def _valid_email(email: str) -> bool:
    return re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email or "") is not None


def login_screen(auth_service: AuthService, settings_repo: SettingsRepository):
    render_header()

    tabs = st.tabs(["Iniciar sesión", "Crear cuenta"])
    with tabs[0]:
        with st.form("login_form"):
            st.subheader("Bienvenido de nuevo")
            email = st.text_input("Email", value=DEMO_EMAIL)
            password = st.text_input("Password", type="password", value=DEMO_PASSWORD)
            submit = st.form_submit_button("Entrar")

        if submit:
            user = auth_service.authenticate(email, password)
            if user:
                _set_authenticated(user, settings_repo)
                st.success("¡Mini win logrado! 🎉")
                st.experimental_rerun()
            else:
                st.error("Credenciales inválidas. Inténtalo de nuevo.")

        if st.button("Entrar con demo"):
            user = auth_service.authenticate(DEMO_EMAIL, DEMO_PASSWORD)
            if user:
                _set_authenticated(user, settings_repo)
                st.experimental_rerun()

    with tabs[1]:
        with st.form("signup_form"):
            st.subheader("Crear cuenta")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirmar password", type="password", key="signup_confirm")
            submit = st.form_submit_button("Crear cuenta")

        if submit:
            if not _valid_email(email):
                st.error("Ingresa un email válido.")
                return
            if len(password) < 8:
                st.error("El password debe tener al menos 8 caracteres.")
                return
            if password != confirm:
                st.error("Los passwords no coinciden.")
                return
            user = auth_service.register(email, password)
            if not user:
                st.error("Ese email ya está registrado.")
                return
            _set_authenticated(user, settings_repo)
            st.success("Cuenta creada. ¡Bienvenido!")
            st.experimental_rerun()


def _set_authenticated(user, settings_repo: SettingsRepository):
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.email = user["email"]
    theme = settings_repo.get(user["id"], "theme", "catppuccin-latte")
    st.session_state.theme = theme


def onboarding_screen(habit_repo: HabitRepository, settings_repo: SettingsRepository):
    render_header()
    st.markdown("### Configura tus primeros hábitos")
    st.write("Elige 3 a 5 hábitos para empezar con buen ritmo.")

    mode = st.radio("¿Cómo quieres empezar?", ["Usar plantilla", "Crear hábitos propios"])

    if mode == "Usar plantilla":
        template_key = st.selectbox(
            "Plantilla",
            ["study", "work", "wellbeing"],
            format_func={"study": "Estudio", "work": "Trabajo", "wellbeing": "Bienestar"}.get,
        )
        template_habits = TEMPLATES.get(template_key, [])
        options = [habit["name"] for habit in template_habits]
        selected = st.multiselect("Selecciona hábitos", options)
    else:
        template_key = None
        selected = []
        raw_habits = st.text_area(
            "Escribe tus hábitos (uno por línea)",
            placeholder="Ej: Tomar agua\nLeer 20 minutos\nCaminar 15 min",
        )

    if st.button("Continuar"):
        if mode == "Usar plantilla":
            if not (3 <= len(selected) <= 5):
                st.error("Selecciona entre 3 y 5 hábitos para continuar.")
                return
            for habit in template_habits:
                if habit["name"] in selected:
                    habit_repo.add_habit(st.session_state.user_id, habit)
        else:
            habits = [line.strip() for line in raw_habits.splitlines() if line.strip()]
            if not (3 <= len(habits) <= 5):
                st.error("Ingresa entre 3 y 5 hábitos para continuar.")
                return
            for habit_name in habits:
                habit_repo.add_habit(
                    st.session_state.user_id,
                    {
                        "name": habit_name,
                        "emoji": "✨",
                        "frequency": "daily",
                        "category": "Personal",
                    },
                )

        settings_repo.set(st.session_state.user_id, "onboarded", "1")
        st.session_state.onboarded = True
        st.experimental_rerun()


def today_screen(habit_repo: HabitRepository, settings_repo: SettingsRepository):
    st.markdown("## Hoy")
    st.caption("Marca tus mini wins y suma racha.")
    habits = habit_repo.list_today_habits(st.session_state.user_id)

    if not habits:
        st.info("Aún no tienes hábitos. Ve a Hábitos para crear uno nuevo.")
        return

    for habit in habits:
        with st.container(border=True):
            st.markdown(f"### {habit.get('emoji') or '✨'} {habit['name']}")
            st.caption(habit.get("category") or "General")
            col1, col2 = st.columns(2)
            if col1.button("Completar", key=f"complete_{habit['id']}"):
                habit_repo.log_action(habit["id"], "completed", user_id=st.session_state.user_id)
            if col2.button("Saltar", key=f"skip_{habit['id']}"):
                habit_repo.log_action(habit["id"], "skipped", user_id=st.session_state.user_id)

    logs = habit_repo.list_all_logs(st.session_state.user_id)
    parsed_logs = []
    for log in logs:
        log_timestamp = parse_log_timestamp(log)
        if not log_timestamp:
            continue
        parsed_logs.append({"timestamp": log_timestamp, "status": log["status"]})
    streak = StreakCalculator().calculate(parsed_logs)
    xp_result = XpCalculator().calculate(total_xp=0, streak=streak)
    wildcard = WildcardRule().has_wildcard(parsed_logs)

    st.info(f"Racha: {streak} | XP ganado hoy: {xp_result['earned']}")
    if wildcard:
        st.info("Tienes un wildcard disponible esta semana.")

    reminder_service = SmartReminderService()
    dnd_start = int(settings_repo.get(st.session_state.user_id, "dnd_start", "22"))
    dnd_end = int(settings_repo.get(st.session_state.user_id, "dnd_end", "7"))
    recommendation = reminder_service.build_recommendation(logs, dnd_start, dnd_end)
    if recommendation["suggested"]:
        hour, minute = recommendation["suggested"]
        st.info(f"Mejor hora sugerida: {hour:02d}:{minute:02d}")

    calendar_data = generate_ics(habits)
    st.download_button(
        "Descargar calendario",
        data=calendar_data,
        file_name="miniwins.ics",
        mime="text/calendar",
    )


def habits_screen(habit_repo: HabitRepository):
    st.markdown("## Hábitos")

    habits = habit_repo.list_habits(st.session_state.user_id)
    if habits:
        for habit in habits:
            with st.container(border=True):
                st.write(f"{habit.get('emoji') or '✨'} {habit['name']}")
                st.caption(habit.get("category") or "General")
                if st.button("Eliminar", key=f"delete_{habit['id']}"):
                    habit_repo.delete_habit(habit["id"], user_id=st.session_state.user_id)
                    st.experimental_rerun()

    st.markdown("### Nuevo hábito")
    name = st.text_input("Nombre del hábito")
    category = st.selectbox("Categoría", ["Salud", "Trabajo", "Estudio", "Bienestar", "Personal"])
    emoji = st.text_input("Emoji", value="✨")
    frequency = st.selectbox("Frecuencia", ["daily", "weekly"])
    suggested_time = st.text_input("Hora sugerida (HH:MM)", value="19:30")

    if st.button("Guardar"):
        if not name:
            st.error("Ingresa un nombre para el hábito.")
            return
        habit_repo.add_habit(
            st.session_state.user_id,
            {
                "name": name,
                "category": category,
                "emoji": emoji,
                "frequency": frequency,
                "suggested_time": suggested_time or None,
            },
        )
        st.experimental_rerun()


def stats_screen(habit_repo: HabitRepository):
    st.markdown("## Estadísticas")

    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).date().isoformat()
    logs = habit_repo.list_logs_since(st.session_state.user_id, thirty_days_ago)

    if not logs:
        st.info("Aún no hay registros. Completa un hábito para ver tu progreso.")
        return

    rows = []
    for log in logs:
        log_timestamp = parse_log_timestamp(log)
        if not log_timestamp:
            continue
        date_value = log.get("date") or log_timestamp.date().isoformat()
        rows.append(
            {
                "date": datetime.fromisoformat(date_value).date(),
                "status": log["status"],
                "habit_id": log["habit_id"],
                "timestamp": log_timestamp,
            }
        )

    df = pd.DataFrame(rows)
    habits = habit_repo.list_habits(st.session_state.user_id)
    habit_map = {habit["id"]: habit["name"] for habit in habits}
    df["habit_name"] = df["habit_id"].map(habit_map).fillna("Hábito")
    completed = df[df["status"] == "completed"]

    st.subheader("Completados por día (últimos 30 días)")
    daily_counts = completed.groupby("date").size().reset_index(name="count")
    bar = alt.Chart(daily_counts).mark_bar(color="#8839ef").encode(x="date:T", y="count:Q")
    st.altair_chart(bar, use_container_width=True)

    st.subheader("Tasa de completado por hábito")
    habit_counts = completed.groupby("habit_name").size().reset_index(name="count")
    bar2 = alt.Chart(habit_counts).mark_bar(color="#04a5e5").encode(x="habit_name:N", y="count:Q")
    st.altair_chart(bar2, use_container_width=True)

    st.subheader("Racha actual por hábito")
    streaks = []
    for habit_id, group in df.groupby("habit_id"):
        logs_for_habit = [
            {"timestamp": row["timestamp"], "status": row["status"]}
            for row in group.to_dict("records")
        ]
        streak_value = StreakCalculator().calculate(logs_for_habit)
        streaks.append({"habit_name": habit_map.get(habit_id, str(habit_id)), "streak": streak_value})

    streaks_df = pd.DataFrame(streaks).sort_values("streak", ascending=False)
    st.dataframe(streaks_df, use_container_width=True)

    best_hour = BestHourCalculator().best_hour(
        [{"timestamp": row["timestamp"], "status": row["status"]} for row in rows]
    )
    if best_hour:
        st.info(f"Mejor hora: {best_hour[0]:02d}:{best_hour[1]:02d}")


def settings_screen(settings_repo: SettingsRepository):
    st.markdown("## Ajustes")
    current_language = settings_repo.get(st.session_state.user_id, "language", "es_419")
    language = st.selectbox(
        "Idioma",
        ["es_419", "en"],
        index=0 if current_language == "es_419" else 1,
    )
    dnd_start = st.number_input(
        "No molestar desde",
        min_value=0,
        max_value=23,
        value=int(settings_repo.get(st.session_state.user_id, "dnd_start", "22")),
    )
    dnd_end = st.number_input(
        "No molestar hasta",
        min_value=0,
        max_value=23,
        value=int(settings_repo.get(st.session_state.user_id, "dnd_end", "7")),
    )

    st.caption("El tema se cambia desde el selector del sidebar.")

    if st.button("Guardar ajustes"):
        settings_repo.set(st.session_state.user_id, "language", language)
        settings_repo.set(st.session_state.user_id, "dnd_start", str(dnd_start))
        settings_repo.set(st.session_state.user_id, "dnd_end", str(dnd_end))
        st.session_state.language = language
        st.session_state.translations = load_translations(language)
        st.experimental_rerun()


def main():
    st.set_page_config(page_title="MiniWins", layout="wide")
    ensure_session()

    user_repo = UserRepository(DB_CONN)
    auth_service = AuthService(user_repo)
    habit_repo = HabitRepository(DB_CONN)
    settings_repo = SettingsRepository(DB_CONN)

    theme = settings_repo.get(st.session_state.user_id, "theme", st.session_state.theme)
    st.session_state.theme = theme
    apply_theme(st.session_state.theme)

    language = (
        settings_repo.get(st.session_state.user_id, "language", "es_419")
        if st.session_state.user_id
        else "es_419"
    )
    st.session_state.language = language
    st.session_state.translations = load_translations(language)

    if not st.session_state.authenticated:
        login_screen(auth_service, settings_repo)
        return

    if st.session_state.user_id and not st.session_state.get("onboarded"):
        st.session_state.onboarded = settings_repo.get(st.session_state.user_id, "onboarded", "0") == "1"

    st.sidebar.title("MiniWins")
    st.sidebar.caption(st.session_state.email or "")
    theme_labels = list(theme_options().values())
    theme_keys = list(theme_options().keys())
    current_theme = st.session_state.theme
    theme_index = theme_keys.index(current_theme) if current_theme in theme_keys else 0
    sidebar_theme = st.sidebar.selectbox("Tema", theme_labels, index=theme_index, key="theme_select")
    selected_theme_key = theme_keys[theme_labels.index(sidebar_theme)]
    if selected_theme_key != current_theme:
        settings_repo.set(st.session_state.user_id, "theme", selected_theme_key)
        st.session_state.theme = selected_theme_key
        apply_theme(selected_theme_key)

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.email = None
        st.session_state.onboarded = False
        st.experimental_rerun()

    if not st.session_state.get("onboarded"):
        onboarding_screen(habit_repo, settings_repo)
        return

    menu = st.sidebar.radio(
        "Navegación",
        ["Hoy", "Hábitos", "Stats", "Ajustes"],
        label_visibility="collapsed",
    )

    if menu == "Hoy":
        today_screen(habit_repo, settings_repo)
    elif menu == "Hábitos":
        habits_screen(habit_repo)
    elif menu == "Stats":
        stats_screen(habit_repo)
    else:
        settings_screen(settings_repo)


if __name__ == "__main__":
    main()
