# MiniWins (Streamlit)

MiniWins es un habit tracker bilingüe (ES/EN) en Python, con interfaz principal en Streamlit y datos locales en SQLite.

## Requisitos
- Python 3.11+

## Instalación
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Migraciones y seed
```bash
python data/migrate.py
python data/seed.py
```

> `miniwins.db` es local y no se versiona en git.

## Ejecutar la app
```bash
streamlit run app.py
```

## Credenciales demo
- Email: `demo@miniwins.app`
- Password: `Demo1234!`

## Tema (Catppuccin Latte / Nord)
- El tema por defecto es **Catppuccin Latte**.
- Puedes cambiarlo en **Ajustes** o desde la **sidebar**. Se guarda por usuario.

## Tests
```bash
ruff check .
pytest -q
```

## Arquitectura
- **UI**: `app.py` (Streamlit)
- **Domain**: `domain/logic.py`
- **Data**: `data/database.py`, `data/migrate.py`, `data/repositories.py`
- **Servicios**: `services/`
