# MiniWins (Python + Streamlit)

MiniWins is a bilingual (ES/EN) habit tracker built entirely in Python. The Streamlit app is the primary UI for local development and the main runtime target.

## Requirements
- Python 3.11+

## Run the Streamlit app (Windows/macOS/Linux)
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Legacy Kivy UI (optional)
The Kivy UI lives in `main.py` and remains available for reference. Android packaging still uses Buildozer.

```bash
python main.py
```

```bash
buildozer android debug
# or
buildozer android release
```

## Architecture
- **UI**: Streamlit in `app.py` (primary), optional Kivy screens in `main.py`.
- **Domain**: `domain/logic.py` for streaks, XP, best hour, smart reminders, wildcard.
- **Data**: SQLite via `data/database.py` + repositories in `data/repositories.py`.
- **Services**: Android bridges for notifications and calendar via `services/`.

## Permissions
Configured in `buildozer.spec`:
- `POST_NOTIFICATIONS`
- `READ_CALENDAR`
- `WRITE_CALENDAR`
- `INTERNET`

## Login (mandatory)
The login flow is required before onboarding and home screens. The current implementation uses a local demo user stored in SQLite as a placeholder. Replace `UserRepository` in `data/repositories.py` with your OAuth/Google Sign-In integration using Python (e.g., OAuth device flow and token storage).

## i18n (ES/EN)
Translations are stored in `locales/` and loaded via `gettext`.

## Tests
Unit tests live in `tests/test_logic.py` and cover streaks, XP, best hour, wildcard rules, and smart reminder intensity.

```bash
python -m unittest tests/test_logic.py
pytest tests/test_smoke_imports.py
```
