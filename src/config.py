# src/config.py
"""
Модуль для работы с конфигурацией приложения
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class AppConfig:
    """Класс конфигурации приложения"""
    app_name: str = "VoiceSynthesizer"
    app_version: str = "1.0.0"

    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, "data")
    user_data_dir: str = os.path.join(data_dir, "user_data")
    dictionaries_dir: str = os.path.join(data_dir, "dictionaries")
    logs_dir: str = os.path.join(data_dir, "logs")

    available_voices: list = field(default_factory=lambda: [
        "aidar", "baya", "kseniya", "xenia", "eugene", "random"
    ])
    sample_rate: int = 48000
    device: str = "cpu"

    default_speed: float = 1.0
    default_pause_duration: float = 0.5
    sentence_pause: float = 0.3  # Пауза внутри предложения
    # Настройки пауз для лучшего произношения окончаний
    end_pause_duration: float = 0.3  # Дополнительная пауза в конце
    min_pause_duration: float = 0.2
    max_pause_duration: float = 1.0

    # Настройки обработки
    auto_add_punctuation: bool = True  # Автоматически добавлять точку в конце
    enhance_endings: bool = True  # Улучшать окончания

    default_zoom: int = 100
    min_zoom: int = 50
    max_zoom: int = 400

    default_font: str = "Arial"
    default_font_size: int = 12
    default_text_color: str = "#000000"

    t9_enabled: bool = False
    t9_max_suggestions: int = 5

    models_dir: str = os.path.join(data_dir, "models")

    # Настройки обработки текста
    enable_preprocessing: bool = True  # Включить предобработку текста
    enable_postprocessing: bool = True  # Включить постобработку аудио


    def __post_init__(self):
        for dir_path in [self.data_dir, self.user_data_dir, self.dictionaries_dir,
                         self.logs_dir, self.models_dir]:
            os.makedirs(dir_path, exist_ok=True)