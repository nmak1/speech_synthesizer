# src/tts_engine/audio_player.py
"""
Модуль для воспроизведения аудио через постоянный OutputStream.

Ключевые решения:
- OutputStream открывается ОДИН РАЗ (prewarm) и живёт всё время.
- play_chunks() НЕ трогает поток через abort — это ломало воспроизведение.
- Замеры prep/write помогают понять, где задержка.
"""
import threading
import time
from typing import Optional, Callable, Iterable

import numpy as np
import sounddevice as sd

from src.utils.logger import get_logger


class AudioPlayer:
    """Плеер с переиспользуемым OutputStream и поддержкой очереди чанков."""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self._sample_rate: Optional[int] = None
        self._stream: Optional[sd.OutputStream] = None
        self._stop_flag = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._worker_lock = threading.Lock()

        self.volume = 1.0
        self.speed = getattr(config, "default_speed", 1.0)

    # ---------- Публичный API ----------

    def prewarm(self, sample_rate: int):
        """Открывает OutputStream заранее."""
        try:
            self.ensure_stream(sample_rate)
            self.logger.info("AudioPlayer: поток прогрет")
        except Exception as e:
            self.logger.warning(f"AudioPlayer: не удалось прогреть поток: {e}")

    def ensure_stream(self, sample_rate: int):
        """Гарантирует, что поток создан и запущен."""
        if self._stream is None or self._sample_rate != sample_rate:
            self._close_stream()
            self._sample_rate = sample_rate
            t0 = time.perf_counter()
            self._stream = sd.OutputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=1024,
                latency="low",
            )
            self._stream.start()
            self.logger.info(
                f"OutputStream открыт за {(time.perf_counter() - t0) * 1000:.0f} мс "
                f"(latency={self._stream.latency})"
            )
        elif not self._stream.active:
            # Поток был создан, но не запущен — запускаем
            try:
                self._stream.start()
                self.logger.info("OutputStream перезапущен")
            except Exception as e:
                self.logger.warning(f"Не удалось перезапустить поток: {e}")
                self._close_stream()
                self._sample_rate = None
                self.ensure_stream(sample_rate)

    def play_chunks(
        self,
        chunks_iter: Iterable[np.ndarray],
        sample_rate: int,
        on_finished: Optional[Callable[[], None]] = None,
        on_first_sample: Optional[Callable[[float], None]] = None,
    ):
        """
        Проигрывает чанки по мере поступления.
        Поток НЕ трогаем (никаких abort), чтобы не сломать воспроизведение.
        """
        # Дожидаемся предыдущего воркера (не более 3 сек)
        with self._worker_lock:
            old = self._worker
        if old and old.is_alive():
            old.join(timeout=3.0)

        self._stop_flag.clear()
        self.ensure_stream(sample_rate)
        t_play_start = time.perf_counter()

        def worker():
            first = True
            try:
                for chunk in chunks_iter:
                    if self._stop_flag.is_set():
                        break
                    if chunk is None or len(chunk) == 0:
                        continue

                    t_prep = time.perf_counter()
                    data = (chunk * self.volume).astype(np.float32, copy=False)
                    if data.ndim == 1:
                        data = data.reshape(-1, 1)
                    t_prep_ms = (time.perf_counter() - t_prep) * 1000

                    if first:
                        total_before_write = (time.perf_counter() - t_play_start) * 1000

                    t_write = time.perf_counter()
                    self._stream.write(data)
                    t_write_ms = (time.perf_counter() - t_write) * 1000

                    if first:
                        first = False
                        chunk_sec = len(chunk) / sample_rate
                        self.logger.info(
                            f"[AUDIO] Первый сэмпл: до_write={total_before_write:.0f}мс, "
                            f"prep={t_prep_ms:.0f}мс, write={t_write_ms:.0f}мс, "
                            f"chunk={chunk_sec:.2f}с"
                        )
                        if on_first_sample:
                            on_first_sample(total_before_write)
            except Exception as e:
                self.logger.error(f"Ошибка воспроизведения: {e}")
            finally:
                if on_finished:
                    on_finished()

        with self._worker_lock:
            self._worker = threading.Thread(target=worker, daemon=True)
            self._worker.start()

    def play(self, audio: np.ndarray, sample_rate: int, callback: Optional[Callable] = None):
        """Совместимость с прежним API."""
        self.play_chunks(iter([audio]), sample_rate, on_finished=callback)

    def stop(self):
        """Мягкая остановка: просим воркер выйти."""
        self._stop_flag.set()

    def hard_stop(self):
        """Жёсткая остановка: abort + перезапуск. Только при явном прерывании."""
        self._stop_flag.set()
        if self._stream is not None:
            try:
                self._stream.abort()
                self._stream.start()
            except Exception:
                pass

    def pause(self):
        pass

    def resume(self):
        pass

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))

    def set_speed(self, speed: float):
        self.speed = max(0.5, min(2.0, speed))

    def is_playing_audio(self) -> bool:
        with self._worker_lock:
            w = self._worker
        return w is not None and w.is_alive()

    def _close_stream(self):
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def cleanup(self):
        self.stop()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1.0)
        self._close_stream()