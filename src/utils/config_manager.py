# src/utils/config_manager.py
import os
import json
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

from src.config import Config, AppConfig
from src.utils.logger import get_logger


class ConfigManager:
    """Менеджер конфигурации"""

    def __init__(self, config_dir: str = None):
        self.logger = get_logger()

        # Определяем путь к папке конфигурации
        if config_dir is None:
            # Для разных ОС используем разные пути
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                self.config_dir = os.path.join(app_data, 'FreeTalk')
            else:  # Linux/Mac
                self.config_dir = os.path.expanduser('~/.config/FreeTalk')
        else:
            self.config_dir = config_dir

        # Создаем папку если её нет
        os.makedirs(self.config_dir, exist_ok=True)

        self.config_file = os.path.join(self.config_dir, 'config.json')

        # Копируем настройки из data/user_data если есть
        self._migrate_old_config()

    def _migrate_old_config(self):
        """Перенос старых настроек из data/user_data"""
        old_config = os.path.join('data', 'user_data', 'config.json')
        if os.path.exists(old_config) and not os.path.exists(self.config_file):
            try:
                shutil.copy(old_config, self.config_file)
                self.logger.info(f"Настройки перенесены из {old_config}")
            except Exception as e:
                self.logger.warning(f"Не удалось перенести настройки: {e}")

    def load_config(self) -> Config:
        """Загрузка конфигурации"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Создаем конфиг из данных
                config = Config()
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                self.logger.info(f"Конфигурация загружена из {self.config_file}")
                return config
            else:
                self.logger.info("Конфигурация не найдена, создана новая")
                return Config()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            return Config()

    def save_config(self, config: Config) -> bool:
        """Сохранение конфигурации"""
        try:
            # Преобразуем в словарь
            if isinstance(config, Config):
                data = config.to_dict()
            else:
                data = config

            # Сохраняем
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Конфигурация сохранена в {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False

    def get_config_path(self) -> str:
        """Получение пути к файлу конфигурации"""
        return self.config_file

    def reset_config(self) -> bool:
        """Сброс конфигурации к значениям по умолчанию"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self.logger.info("Конфигурация сброшена")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сброса конфигурации: {e}")
            return False