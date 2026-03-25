# src/utils/file_manager.py
"""
Модуль для работы с файлами
"""
import os
import shutil
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.utils.logger import get_logger


class FileManager:
    """Класс для управления файлами"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

    def save_text_file(self, text: str, filename: Optional[str] = None) -> str:
        """Сохранение текста в файл"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"text_{timestamp}.txt"

            filepath = os.path.join(self.config.user_data_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

            self.logger.info(f"Текст сохранен: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Ошибка сохранения текста: {e}")
            return ""

    def load_text_file(self, filepath: str) -> Optional[str]:
        """Загрузка текста из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            return text

        except Exception as e:
            self.logger.error(f"Ошибка загрузки текста: {e}")
            return None

    def save_json(self, data: Dict[str, Any], filename: str) -> bool:
        """Сохранение данных в JSON файл"""
        try:
            filepath = os.path.join(self.config.user_data_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения JSON: {e}")
            return False

    def load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """Загрузка данных из JSON файла"""
        try:
            filepath = os.path.join(self.config.user_data_dir, filename)

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return None

        except Exception as e:
            self.logger.error(f"Ошибка загрузки JSON: {e}")
            return None

    def delete_file(self, filepath: str) -> bool:
        """Удаление файла"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Ошибка удаления файла: {e}")
            return False

    def get_files_in_directory(self, directory: str, extension: str = "") -> List[str]:
        """Получение списка файлов в директории"""
        try:
            files = []
            for file in os.listdir(directory):
                if not extension or file.endswith(extension):
                    files.append(os.path.join(directory, file))
            return files

        except Exception as e:
            self.logger.error(f"Ошибка получения списка файлов: {e}")
            return []