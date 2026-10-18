# src/version.py
"""Единственный источник версии приложения.

Все модули (config, main, release, CI) должны брать версию отсюда.
"""

MAJOR = 2
MINOR = 1
PATCH = 0

__version__ = f"{MAJOR}.{MINOR}.{PATCH}"

# AUMID для Windows (taskbar / уведомления)
APP_USER_MODEL_ID = "freetalk.synthesizer.app"
