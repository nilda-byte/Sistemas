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
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

```bash
python data/migrate.py
python data/seed.py
```

## Architecture
- **UI**: Streamlit in `app.py` (primary), optional Kivy screens in `main.py`.
- **Domain**: `domain/logic.py` for streaks, XP, best hour, smart reminders, wildcard.
- **Data**: SQLite via `data/database.py` + repositories in `data/repositories.py`.
- **Services**: Android bridges for notifications and calendar via `services/`.

## Ejecutar la app
```bash
streamlit run app.py
```

## Login (mandatory)
The login flow is required before onboarding and home screens. The current implementation uses a local demo user stored in SQLite as a placeholder. Replace `UserRepository` in `data/repositories.py` with your OAuth/Google Sign-In integration using Python (e.g., OAuth device flow and token storage).

## Tema (Catppuccin Latte / Nord)
- El tema por defecto es **Catppuccin Latte**.
- Puedes cambiarlo en **Ajustes** o desde la **sidebar**. Se guarda por usuario.

## Tests
```bash
python -m unittest tests/test_logic.py
pytest tests/test_smoke_imports.py
```

## Arquitectura
- **UI**: `app.py` (Streamlit)
- **Domain**: `domain/logic.py`
- **Data**: `data/database.py`, `data/migrate.py`, `data/repositories.py`
- **Servicios**: `services/`
