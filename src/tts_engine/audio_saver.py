# src/tts_engine/audio_saver.py
"""
Модуль для сохранения аудио в файл
"""
import os
import soundfile as sf
from datetime import datetime
from typing import Optional, List
import numpy as np
import tempfile

from src.utils.logger import get_logger


class AudioSaver:
    """Класс для сохранения аудио файлов"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self._temp_files = []  # Для отслеживания временных файлов

        # Создаем папку для загрузок если её нет
        self.downloads_dir = os.path.expanduser("~/Downloads/FreeTalk")  # Изменено имя папки
        os.makedirs(self.downloads_dir, exist_ok=True)

    def save(self, audio: np.ndarray, sample_rate: int, filename: Optional[str] = None) -> str:
        """Сохранение аудио в файл с корректным освобождением ресурсов"""
        filepath = None
        try:
            # Генерируем имя файла если не указано
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"FreeTalk_{timestamp}.wav"

            # Полный путь к файлу
            filepath = os.path.join(self.downloads_dir, filename)

            # Сначала сохраняем во временный файл для проверки
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Сохраняем во временный файл
            sf.write(temp_path, audio, sample_rate)

            # Проверяем, что файл создан и не поврежден
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                # Копируем в целевой файл (перезаписываем, если существует)
                import shutil
                shutil.copy2(temp_path, filepath)
                # Удаляем временный файл
                os.unlink(temp_path)

                self.logger.info(f"Аудио сохранено: {filepath}")
                return filepath
            else:
                self.logger.error(f"Временный файл не создан или пуст: {temp_path}")
                return ""

        except Exception as e:
            self.logger.error(f"Ошибка сохранения аудио: {e}")
            # Очищаем временный файл если он существует
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
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

    def cleanup_temp_files(self):
        """Очистка временных файлов"""
        for file in self._temp_files:
            try:
                if os.path.exists(file):
                    os.unlink(file)
            except:
                pass
        self._temp_files.clear()