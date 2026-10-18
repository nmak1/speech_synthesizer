# tests/conftest.py
"""Общая фикстура для тестов FreeTalk (pytest + pytest-qt).

TTS/аудио-зависимости (torch, sounddevice) изолируются: GUI-тесты используют
реальные виджеты, но не реальный синтез.
"""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture()
def tmp_config(tmp_path):
    """Config с путями во временную директорию — без side-effects на data/."""
    from src.config import Config

    return Config(
        data_dir=str(tmp_path),
        models_dir=str(tmp_path / "models"),
        dictionaries_dir=str(tmp_path / "dictionaries"),
        logs_dir=str(tmp_path / "logs"),
        user_data_dir=str(tmp_path / "user_data"),
        t9_dictionary_path=str(tmp_path / "dictionaries" / "t9_dictionary.json"),
    )


@pytest.fixture()
def isolated_settings():
    """QSettings в отдельный файл — тесты не трогают реальные настройки."""
    from PyQt5.QtCore import QSettings

    QSettings.clearApplication()
    QSettings.setOrganizationName("FreeTalkTest")
    QSettings.setApplicationName("FreeTalkTest")
    yield
    s = QSettings("FreeTalkTest", "FreeTalkTest")
    s.clear()
    QSettings.setOrganizationName("FreeTalk")
    QSettings.setApplicationName("App")
