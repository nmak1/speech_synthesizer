# src/workers.py
"""QThread-воркеры для фоновых операций.

Заменили raw threading.Thread: все обращения к UI идут только через сигналы Qt,
которые безопасно доставляются в главный поток (queued connection).
"""
import time

from PyQt5.QtCore import QThread, pyqtSignal


class ModelReadyWorker(QThread):
    """Ждёт готовности TTS-модели (warm-up) и прогретого аудиопотока.

    Сигналы:
      ready()               — модель готова (или истёк таймаут)
      progress(str)         — статус для статус-бара
    """

    ready = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self, tts_engine, audio_player, timeout_sec: float = 120.0, parent=None):
        super().__init__(parent)
        self.tts_engine = tts_engine
        self.audio_player = audio_player
        self.timeout_sec = timeout_sec
        self._cancelled = False
        self.setObjectName("ModelReadyWorker")

    def cancel(self):
        self._cancelled = True

    def run(self):
        deadline = time.monotonic() + self.timeout_sec
        while not self._cancelled and time.monotonic() < deadline:
            try:
                if self.tts_engine is not None and self.tts_engine.is_warmup_done():
                    if self.audio_player is not None and self.tts_engine.get_sample_rate():
                        try:
                            self.audio_player.prewarm(self.tts_engine.get_sample_rate())
                        except Exception:
                            pass  # prewarm не критичен
                    break
            except Exception:
                break
            time.sleep(0.1)
        # ready() эмитим всегда — UI сам разберётся (в т.ч. после таймаута)
        if not self._cancelled:
            self.ready.emit()


class SynthesizePlayWorker(QThread):
    """Синтезирует текст по предложениям и проигрывает чанки.

    Сигналы:
      first_sample(float)   — задержка до первого сэмпла, мс
      finished_ok()         — воспроизведение завершено
      error(str)            — текст ошибки
    """

    first_sample = pyqtSignal(float)
    finished_ok = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, tts_engine, audio_player, sentences, speed, sample_rate, parent=None):
        super().__init__(parent)
        self.tts_engine = tts_engine
        self.audio_player = audio_player
        self.sentences = list(sentences)
        self.speed = speed
        self.sample_rate = sample_rate
        self._stop = False
        self.setObjectName("SynthesizePlayWorker")

    def stop(self):
        """Мягкая остановка из главного потока (без блокировок UI)."""
        self._stop = True

    def run(self):
        try:
            worker_self = self

            def chunk_generator():
                for s in self.sentences:
                    if self._stop or self.isInterruptionRequested():
                        return
                    audio = self.tts_engine.synthesize(s, self.speed)
                    if audio is not None:
                        yield audio

            def on_first(dt_ms: float):
                # сигнал — безопасный способ попасть в UI-поток
                self.first_sample.emit(dt_ms)

            self.audio_player.play_chunks(
                chunk_generator(),
                self.sample_rate,
                on_finished=self.finished_ok.emit,
                on_first_sample=on_first,
            )
        except Exception as e:
            self.error.emit(str(e))


class SynthesizeSaveWorker(QThread):
    """Синтез всего текста в один массив для последующего сохранения в файл.

    Сигналы:
      audio_ready(object)   — numpy-массив аудио (обработка/диалог — в UI-потоке)
      error(str)
    """

    audio_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, tts_engine, sentences, speed, parent=None):
        super().__init__(parent)
        self.tts_engine = tts_engine
        self.sentences = list(sentences)
        self.speed = speed
        self._stop = False
        self.setObjectName("SynthesizeSaveWorker")

    def stop(self):
        self._stop = True

    def run(self):
        try:
            parts = []
            for s in self.sentences:
                if self._stop or self.isInterruptionRequested():
                    self.error.emit("Отменено")
                    return
                a = self.tts_engine.synthesize(s, self.speed)
                if a is not None:
                    parts.append(a)
            if not parts:
                self.error.emit("Нет аудио: синтез вернул пустой результат")
                return
            import numpy as np
            audio = np.concatenate(parts) if len(parts) > 1 else parts[0]
            self.audio_ready.emit(audio)
        except Exception as e:
            self.error.emit(str(e))
