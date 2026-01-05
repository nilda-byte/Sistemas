# MiniWins (Streamlit)

MiniWins es un habit tracker web para estudiantes y trabajadores con gamificación, i18n ES/EN, recordatorios inteligentes y exportación de calendario.

## Requisitos (Windows 11)
- Python 3.11 instalado (desde https://python.org)
- Git (opcional) para clonar el repositorio

## Instalación paso a paso (Windows 11)
1. Abre **PowerShell**.
2. Ve a la carpeta del proyecto:
   ```powershell
   cd C:\ruta\al\proyecto\MiniWins
   ```
3. Crea y activa un entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Instala dependencias:
   ```powershell
   pip install -r requirements.txt
   ```
5. Ejecuta la app:
   ```powershell
   streamlit run app.py
   ```

## Credenciales demo
- **Email:** demo@miniwins.app
- **Password:** Demo1234!

## Estructura
- `app.py`: aplicación Streamlit.
- `data/`: SQLite, repositorios y seeds.
- `domain/`: lógica de rachas, XP y mejores horas.
- `services/`: auth, recordatorios inteligentes e ICS.
- `i18n/`: traducciones ES/EN en JSON.
- `assets/`: ilustraciones estilo street art (fallback si no cargan).
- `tests/`: pruebas unitarias con pytest.

## Tests
```powershell
python -m pytest
```

## Notas
- Base de datos SQLite se crea automáticamente al iniciar la app.
- El onboarding carga hábitos seed según la plantilla seleccionada.
- Exporta calendario con el botón “Descargar calendario (.ics)” e impórtalo en Google Calendar.
