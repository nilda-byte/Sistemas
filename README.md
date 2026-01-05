# MiniWins (Python + Kivy)

MiniWins is a bilingual (ES/EN) habit tracker built entirely in Python with Kivy, designed for Android packaging with Buildozer.

## Requirements
- Python 3.10+
- Buildozer (for Android builds)
- Android SDK/NDK (installed by Buildozer)

## Run locally
```bash
python main.py
```

## Build for Android (APK/AAB)
```bash
buildozer android debug
# or
buildozer android release
```

## Architecture
- **UI**: Kivy Screens (`screens` embedded in `main.py` for now) with ScreenManager.
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
The login flow is required before onboarding and home screens. The current implementation uses a local auth flag stored in SQLite as a placeholder. Replace `AuthRepository.sign_in()` in `data/repositories.py` with your OAuth/Google Sign-In integration using Python (e.g., OAuth device flow and token storage).

## i18n (ES/EN)
Translations are stored in `locales/` and loaded via `gettext`.

## Tests
Unit tests live in `tests/test_logic.py` and cover streaks, XP, best hour, wildcard rules, and smart reminder intensity.

```bash
python -m unittest tests/test_logic.py
```
