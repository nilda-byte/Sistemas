TEMPLATES = {
    "study": [
        {"name": "Repaso diario", "emoji": "📚", "frequency": "daily", "category": "Estudio"},
        {"name": "Pomodoro", "emoji": "⏱️", "frequency": "daily", "category": "Estudio"},
        {"name": "Lectura", "emoji": "📖", "frequency": "daily", "category": "Estudio"},
    ],
    "work": [
        {"name": "Deep work", "emoji": "🧠", "frequency": "daily", "category": "Trabajo"},
        {"name": "Checklist productividad", "emoji": "✅", "frequency": "daily", "category": "Trabajo"},
    ],
    "wellbeing": [
        {
            "name": "Ejercicio",
            "emoji": "🏃",
            "frequency": "weekly",
            "days": "MON,WED,FRI",
            "category": "Bienestar",
        },
        {"name": "Hidratación", "emoji": "💧", "frequency": "daily", "category": "Bienestar"},
        {"name": "Dormir", "emoji": "😴", "frequency": "daily", "category": "Bienestar"},
    ],
}


def seed_templates(user_id, template_key, habit_repository):
    for habit in TEMPLATES.get(template_key, []):
        habit_repository.add_habit(user_id, habit)


if __name__ == "__main__":
    from data.database import init_db
    from data.repositories import HabitRepository

    connection = init_db()
    repo = HabitRepository(connection)
    demo_user_id = 1
    seed_templates(demo_user_id, "study", repo)
    print("Seed completed.")
