# src/config.py
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.version import __version__
from src.paths import data_path


@dataclass
class Config:
    """Конфигурация приложения"""

    # Версия приложения (единый источник — src/version.py)
    app_version: str = __version__

    # TTS настройки
    model_path: str = "data/models/v3_1_ru.pt"
    sample_rate: int = 48000
    default_voice: str = "aidar"
    default_speed: float = 1.0

    # Доступные голоса
    available_voices: List[str] = field(default_factory=lambda: [
        "aidar", "baya", "kseniya", "xenia", "random"
    ])

    # Пути к данным — абсолютные, через единый модуль src/paths.py
    data_dir: str = field(default_factory=lambda: os.path.dirname(data_path("")))
    models_dir: str = field(default_factory=lambda: data_path("models"))
    dictionaries_dir: str = field(default_factory=lambda: data_path("dictionaries"))
    logs_dir: str = field(default_factory=lambda: data_path("logs"))
    user_data_dir: str = field(default_factory=lambda: data_path("user_data"))

    # Интерфейс
    default_zoom: int = 100
    default_font_size: int = 14
    default_font_family: str = "Segoe UI"
    default_text_color: str = "#000000"
    window_width: int = 1200
    window_height: int = 800

    # T9 (отключён по умолчанию: кнопка в интерфейсе убрана)
    t9_enabled: bool = False
    t9_show_button: bool = False
    t9_dictionary_path: str = field(default_factory=lambda: data_path("dictionaries/t9_dictionary.json"))
    # Динамическое обучение словаря T9 по набранному тексту
    t9_learning_enabled: bool = True
    # Интервал пакетного обучения (мс): текст обучается не при каждой клавише
    t9_learn_interval_ms: int = 5000

    # Другие настройки
    app_name: str = "Free Talk"
    debug: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "app_version": self.app_version,
            "model_path": self.model_path,
            "sample_rate": self.sample_rate,
            "default_voice": self.default_voice,
            "default_speed": self.default_speed,
            "available_voices": self.available_voices,
            "data_dir": self.data_dir,
            "models_dir": self.models_dir,
            "dictionaries_dir": self.dictionaries_dir,
            "logs_dir": self.logs_dir,
            "user_data_dir": self.user_data_dir,
            "default_zoom": self.default_zoom,
            "default_font_size": self.default_font_size,
            "default_font_family": self.default_font_family,
            "default_text_color": self.default_text_color,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "t9_enabled": self.t9_enabled,
            "t9_show_button": self.t9_show_button,
            "t9_dictionary_path": self.t9_dictionary_path,
            "t9_learning_enabled": self.t9_learning_enabled,
            "t9_learn_interval_ms": self.t9_learn_interval_ms,
            "app_name": self.app_name,
            "debug": self.debug,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Создание из словаря"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


# Псевдоним для обратной совместимости
AppConfig = Config