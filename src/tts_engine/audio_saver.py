# src/tts_engine/audio_saver.py
"""
Модуль для сохранения аудио в файл
"""
import os
import soundfile as sf
from datetime import datetime
from typing import Optional, List
import numpy as np

from src.utils.logger import get_logger


class AudioSaver:
    """Класс для сохранения аудио файлов"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # Создаем папку для загрузок если её нет
        self.downloads_dir = os.path.expanduser("~/Downloads/VoiceSynthesizer")
        os.makedirs(self.downloads_dir, exist_ok=True)

    def save(self, audio: np.ndarray, sample_rate: int, filename: Optional[str] = None) -> str:
        """Сохранение аудио в файл"""
        try:
            # Генерируем имя файла если не указано
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"speech_{timestamp}.wav"

            # Полный путь к файлу
            filepath = os.path.join(self.downloads_dir, filename)

            # Сохраняем
            sf.write(filepath, audio, sample_rate)

            self.logger.info(f"Аудио сохранено: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Ошибка сохранения аудио: {e}")
            return ""

    def save_multiple(self, audio_parts: List[np.ndarray], sample_rate: int,
                      filename: Optional[str] = None) -> str:
        """Сохранение нескольких аудио частей в один файл"""
        try:
            # Объединяем все части
            combined_audio = np.concatenate(audio_parts)
            return self.save(combined_audio, sample_rate, filename)

        except Exception as e:
            self.logger.error(f"Ошибка сохранения аудио: {e}")
            return ""

    def get_downloads_folder(self) -> str:
        """Получение пути к папке загрузок"""
        return self.downloads_dir