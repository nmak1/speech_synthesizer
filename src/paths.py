# src/paths.py
"""Единая точка определения путей ресурсов приложения.

Решает проблему разбросанных по коду относительных путей ("imeg/logo.ico",
"data/models/..." и т.п.), которые ломались при запуске из PyInstaller или
из другой рабочей директории.

Логика:
- dev (обычный запуск python main.py): корень проекта = parent папки src/
- frozen (PyInstaller): корень = sys._MEIPASS для read-only ресурсов
  (логотипы, модели) и dirname(sys.executable) для writable-данных (data/)
"""
import os
import sys
from functools import lru_cache


@lru_cache(maxsize=1)
def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


@lru_cache(maxsize=1)
def app_root() -> str:
    """Корень для read-only ресурсов (иконки, логотипы, bundled data)."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # src/paths.py -> src -> корень проекта
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@lru_cache(maxsize=1)
def user_data_root() -> str:
    """Корень для записываемых данных (логи, словари, пользовательский конфиг).

    В frozen-режиме НЕ пишем в _MEIPASS (временная папка удаляется),
    используем соседний с exe каталог.
    """
    if is_frozen():
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(app_root(), "data")


def resource_path(relative: str) -> str:
    """Абсолютный путь к ресурсу (read-only): 'imeg/logo.png' -> ..."""
    return os.path.join(app_root(), *relative.split("/"))


def find_resource(*candidates: str):
    """Возвращает первый существующий абсолютный путь среди кандидатов."""
    for rel in candidates:
        p = resource_path(rel)
        if os.path.exists(p):
            return p
    return None


def data_path(relative: str) -> str:
    """Абсолютный путь к записываемым данным: 'dictionaries/x.json' -> ..."""
    return os.path.join(user_data_root(), *relative.split("/"))
