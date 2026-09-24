# src/config.py
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Config:
    """Конфигурация приложения"""

    # Версия приложения
    app_version: str = "2.0.0"

    # TTS настройки
    model_path: str = "data/models/v3_1_ru.pt"
    sample_rate: int = 48000
    default_voice: str = "aidar"
    default_speed: float = 1.0

    # Доступные голоса
    available_voices: List[str] = field(default_factory=lambda: [
        "aidar", "baya", "kseniya", "xenia", "random"
    ])

    # Пути к данным
    data_dir: str = "data"
    models_dir: str = "data/models"
    dictionaries_dir: str = "data/dictionaries"
    logs_dir: str = "data/logs"
    user_data_dir: str = "data/user_data"

    # Интерфейс
    default_zoom: int = 100
    default_font_size: int = 14
    window_width: int = 1200
    window_height: int = 800

    # T9
    t9_enabled: bool = True
    t9_dictionary_path: str = "data/dictionaries/t9_dictionary.json"

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
            "window_width": self.window_width,
            "window_height": self.window_height,
            "t9_enabled": self.t9_enabled,
            "t9_dictionary_path": self.t9_dictionary_path,
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