# src/tts_engine/audio_player.py
"""
Модуль для воспроизведения аудио
"""
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable

from src.utils.logger import get_logger


class AudioPlayer:
    """Класс для воспроизведения аудио"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.is_playing = False
        self.is_paused = False
        self.current_thread = None
        self.audio_queue = queue.Queue()

        # Параметры воспроизведения
        self.volume = 1.0
        self.speed = config.default_speed

    def play(self, audio: np.ndarray, sample_rate: int, callback: Optional[Callable] = None):
        """Воспроизведение аудио"""
        if self.is_playing:
            self.stop()

        self.is_playing = True
        self.is_paused = False

        def play_thread():
            try:
                # Применяем громкость
                audio_to_play = audio * self.volume

                # Воспроизводим
                sd.play(audio_to_play, sample_rate)

                # Ждем окончания воспроизведения
                while self.is_playing and not self.is_paused:
                    if not sd.get_stream().active:
                        break
                    time.sleep(0.1)

                sd.stop()

                if callback:
                    callback()

            except Exception as e:
                self.logger.error(f"Ошибка воспроизведения: {e}")
            finally:
                self.is_playing = False

        self.current_thread = threading.Thread(target=play_thread, daemon=True)
        self.current_thread.start()

    def stop(self):
        """Остановка воспроизведения"""
        self.is_playing = False
        self.is_paused = False
        sd.stop()

    def pause(self):
        """Пауза воспроизведения"""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            sd.stop()

    def resume(self):
        """Возобновление воспроизведения"""
        # Для упрощения не реализуем возобновление
        pass

    def set_volume(self, volume: float):
        """Установка громкости (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def set_speed(self, speed: float):
        """Установка скорости воспроизведения"""
        self.speed = max(0.5, min(2.0, speed))

    def is_playing_audio(self) -> bool:
        """Проверка, воспроизводится ли аудио"""
        return self.is_playing