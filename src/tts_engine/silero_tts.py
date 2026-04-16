# src/tts_engine/silero_tts.py
import torch
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
import re
import urllib.request
from typing import Optional
import warnings
import time

warnings.filterwarnings("ignore", category=UserWarning)

from src.utils.logger import get_logger


class SileroTTS:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sample_rate = config.sample_rate

        self.model = None
        self.current_voice = None
        self.available_voices = config.available_voices

        self.logger.info(f"Используется устройство: {self.device}")

        self._load_model()

    def _load_model(self):
        """Загрузка модели Silero TTS"""
        try:
            self.logger.info("Загрузка модели Silero TTS...")

            model_path = os.path.join(self.config.models_dir, "v3_1_ru.pt")

            if os.path.exists(model_path):
                self.logger.info(f"Загрузка модели из файла: {model_path}")
                self.model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
                self.model.to(self.device)
                self.logger.info("Модель успешно загружена")
                return
            else:
                self.logger.info("Локальная модель не найдена. Скачивание...")
                self._download_model(model_path)

        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise

    def _download_model(self, model_path: str):
        """Скачивание модели"""
        try:
            url = "https://models.silero.ai/models/tts/ru/v3_1_ru.pt"
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    if int(percent) % 10 == 0:
                        self.logger.info(f"Прогресс: {percent:.1f}%")

            urllib.request.urlretrieve(url, model_path, report_progress)
            self.logger.info("Модель скачана, загружаем...")

            self.model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
            self.model.to(self.device)
            self.logger.info("Модель успешно загружена")

        except Exception as e:
            self.logger.error(f"Ошибка скачивания: {e}")
            raise

    def set_voice(self, voice_name: str):
        if voice_name not in self.available_voices:
            voice_name = "aidar"
        self.current_voice = voice_name
        self.logger.info(f"Установлен голос: {voice_name}")

    def _add_pauses_to_text(self, text: str) -> str:
        """Добавляет паузы для лучшего произношения окончаний"""
        # Добавляем пробелы вокруг знаков препинания для пауз
        text = re.sub(r'([.,!?;:])', r' \1 ', text)

        # Добавляем дополнительную паузу перед концом предложения
        if text.endswith('?'):
            text = text[:-1] + ' ? '
        elif text.endswith('!'):
            text = text[:-1] + ' ! '
        elif text.endswith('.'):
            text = text[:-1] + ' . '
        else:
            text = text + ' . '

        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def synthesize(self, text: str, speed: float = 1.0) -> Optional[np.ndarray]:
        if not self.model:
            return None

        if not self.current_voice:
            self.set_voice(self.available_voices[0])

        try:
            text = text.strip()
            if not text:
                return None

            # Добавляем паузы для лучшего произношения
            processed_text = self._add_pauses_to_text(text)

            self.logger.info(f"Синтез текста: '{processed_text}'")

            # Синтез аудио
            audio = self.model.apply_tts(
                text=processed_text,
                speaker=self.current_voice,
                sample_rate=self.sample_rate
            )

            if torch.is_tensor(audio):
                audio = audio.cpu().numpy()

            if audio is None or len(audio) == 0:
                return None

            # Увеличиваем громкость
            audio = audio * 1.2

            # Нормализация
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val

            # Добавляем плавное затухание в конце (200 мс)
            fade_duration = int(0.2 * self.sample_rate)
            if len(audio) > fade_duration:
                fade_out = np.linspace(1, 0, fade_duration)
                audio[-fade_duration:] *= fade_out

            # Добавляем небольшую паузу в конце (тишина)
            pause_duration = int(0.3 * self.sample_rate)  # 300 мс тишины
            pause = np.zeros(pause_duration)
            audio = np.concatenate([audio, pause])

            if speed != 1.0:
                audio = self._change_speed(audio, speed)

            return audio

        except Exception as e:
            self.logger.error(f"Ошибка синтеза: {e}")
            return None

    def play(self, audio: np.ndarray):
        try:
            if audio is not None and len(audio) > 0:
                sd.play(audio, self.sample_rate)
                sd.wait()
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения: {e}")

    def save_to_file(self, audio: np.ndarray, filepath: str) -> bool:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            sf.write(filepath, audio, self.sample_rate)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения: {e}")
            return False

    def _change_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        try:
            old_len = len(audio)
            new_len = int(old_len / speed)
            indices = np.linspace(0, old_len - 1, new_len).astype(np.int32)
            indices = indices[indices < old_len]
            return audio[indices]
        except:
            return audio