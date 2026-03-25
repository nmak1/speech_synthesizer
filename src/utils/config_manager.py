# src/utils/config_manager.py
"""
Модуль для управления конфигурацией приложения
"""
import os
import json
import pickle
from typing import Any, Dict
from dataclasses import asdict

from src.config import AppConfig
from src.utils.logger import get_logger


class ConfigManager:
    """Класс для управления конфигурацией"""

    def __init__(self):
        self.logger = get_logger()
        self.config_file = os.path.join(
            os.path.expanduser("~"),
            ".voicesynthesizer",
            "config.json"
        )

        # Создаем папку для конфига
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

    def load_config(self) -> AppConfig:
        """Загрузка конфигурации из файла"""
        config = AppConfig()

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Обновляем конфиг
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                self.logger.info("Конфигурация загружена")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")

        return config

    def save_config(self, config: AppConfig):
        """Сохранение конфигурации в файл"""
        try:
            data = asdict(config)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("Конфигурация сохранена")

        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")