# src/config.py
import os
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    app_name: str = "Free Talk"
    app_version: str = "1.0.0"

    # Пути
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, "data")
    models_dir: str = os.path.join(data_dir, "models")
    dictionaries_dir: str = os.path.join(data_dir, "dictionaries")
    user_data_dir: str = os.path.join(data_dir, "user_data")
    logs_dir: str = os.path.join(data_dir, "logs")

    # Голоса
    available_voices: list = field(default_factory=lambda: [
        "aidar", "baya", "kseniya", "xenia", "eugene", "random"
    ])

    # Настройки синтеза
    sample_rate: int = 48000
    device: str = "cpu"
    default_speed: float = 0.95  # Уменьшили с 1.0 до 0.95 (медленнее на 15%)
    min_speed: float = 0.5
    max_speed: float = 2.0
    default_pause_duration: float = 0.5

    # Настройки интерфейса
    default_zoom: int = 100
    min_zoom: int = 50
    max_zoom: int = 400
    default_font: str = "Segoe UI"
    default_font_size: int = 12
    t9_enabled: bool = False
    t9_max_suggestions: int = 5

    def __post_init__(self):
        for dir_path in [self.data_dir, self.models_dir, self.dictionaries_dir,
                         self.user_data_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)