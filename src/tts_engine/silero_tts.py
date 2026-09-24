# src/tts_engine/silero_tts.py
import os
import sys
import time
import threading
from typing import Optional, List, Callable

import numpy as np
import torch
import soundfile as sf

from src.utils.logger import get_logger


class SileroTTS:
    """Класс для работы с Silero TTS моделью (singleton)."""

    _instance = None
    _model = None
    _sample_rate = None
    _speaker = None
    _device = None
    _lock = threading.Lock()
    _apply_lock = threading.Lock()          # защита от параллельных apply_tts
    _model_ready = threading.Event()
    _warmup_done = threading.Event()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SileroTTS, cls).__new__(cls)
        return cls._instance

    def __init__(self, config, preload: bool = True, warmup: bool = True):
        if getattr(self, "_initialized", False):
            self.config = config
            return
        self._initialized = True

        self.logger = get_logger()
        self.config = config

        self._cache = {}
        self._cache_max_size = 50
        self._cache_lock = threading.Lock()

        if preload:
            threading.Thread(
                target=self._load_and_warmup,
                args=(warmup,),
                daemon=True,
                name="SileroLoader",
            ).start()
        else:
            self._load_model()
            if warmup:
                self._warmup()

    # ---------- Загрузка + warm-up в одном потоке ----------

    def _load_and_warmup(self, do_warmup: bool):
        try:
            self._load_model()
            if do_warmup:
                self._warmup()
        except Exception as e:
            self.logger.error(f"Ошибка инициализации модели: {e}")
        finally:
            # Даже при ошибке — снимаем блокировку, чтобы UI не завис навсегда
            if not SileroTTS._warmup_done.is_set():
                SileroTTS._warmup_done.set()

    def _warmup(self):
        """Двухпроходный warm-up."""
        if SileroTTS._model is None:
            return
        try:
            t0 = time.perf_counter()
            with torch.no_grad():
                _ = SileroTTS._model.apply_tts(
                    text="а",
                    speaker=SileroTTS._speaker or "aidar",
                    sample_rate=SileroTTS._sample_rate or 48000,
                )
                t1 = time.perf_counter()
                _ = SileroTTS._model.apply_tts(
                    text="Привет, как твои дела? У меня всё хорошо.",
                    speaker=SileroTTS._speaker or "aidar",
                    sample_rate=SileroTTS._sample_rate or 48000,
                )
                t2 = time.perf_counter()
            self.logger.info(
                f"Warm-up: pass1={int((t1 - t0) * 1000)}ms, "
                f"pass2={int((t2 - t1) * 1000)}ms, "
                f"total={int((t2 - t0) * 1000)}ms"
            )
        except Exception as e:
            self.logger.warning(f"Warm-up не удался: {e}")
        finally:
            SileroTTS._warmup_done.set()

    def _get_model_path(self) -> str:
        possible_paths = [
            self.config.model_path,
            "data/models/v3_1_ru.pt",
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "v3_1_ru.pt"),
            os.path.join(os.path.dirname(sys.executable), "data", "models", "v3_1_ru.pt"),
        ]
        try:
            base_path = sys._MEIPASS
            possible_paths.append(os.path.join(base_path, "data", "models", "v3_1_ru.pt"))
        except Exception:
            pass

        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Модель найдена: {path}")
                return path
        return self.config.model_path

    def _load_model(self):
        with SileroTTS._lock:
            if SileroTTS._model is not None:
                SileroTTS._model_ready.set()
                return

            try:
                self.logger.info("Загрузка модели Silero TTS...")
                t0 = time.perf_counter()

                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                SileroTTS._device = device

                model_path = self._get_model_path()

                if not os.path.exists(model_path):
                    self.logger.info("Модель не найдена, скачивание...")
                    os.makedirs(os.path.dirname(model_path), exist_ok=True)
                    import urllib.request
                    url = "https://models.silero.ai/models/tts/ru/v3_1_ru.pt"
                    urllib.request.urlretrieve(url, model_path)

                model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
                model.to(device)

                SileroTTS._model = model
                SileroTTS._sample_rate = 48000
                SileroTTS._speaker = self.config.default_voice or "aidar"
                SileroTTS._model_ready.set()

                self.logger.info(
                    f"Модель загружена за {time.perf_counter() - t0:.2f} сек. Устройство: {device}"
                )
            except Exception as e:
                self.logger.error(f"Ошибка загрузки модели: {e}")
                raise

    def is_ready(self) -> bool:
        return SileroTTS._model is not None

    def is_warmup_done(self) -> bool:
        return SileroTTS._warmup_done.is_set()

    # ---------- Синтез ----------

    def synthesize(self, text: str, speed: float = 1.0) -> Optional[np.ndarray]:
        """Синтез речи с детальными таймерами."""
        if not text or not text.strip():
            return None

        t_start = time.perf_counter()

        # Уровень 1: ждём окончания warm-up — иначе race condition с warm-up-потоком
        self._model_ready.wait(timeout=30)
        t0 = time.perf_counter()
        self._warmup_done.wait(timeout=120)
        t_wait = (time.perf_counter() - t0) * 1000

        if SileroTTS._model is None:
            self.logger.error("Модель не загружена")
            return None

        cache_key = (text.strip(), speed, SileroTTS._speaker)
        with self._cache_lock:
            cached = self._cache.get(cache_key)
        if cached is not None:
            self.logger.info(
                f"[SYNTH] CACHE HIT '{text[:25]}...' len={len(text)}"
            )
            return cached

        try:
            # Уровень 2: сериализуем apply_tts
            t0 = time.perf_counter()
            with SileroTTS._apply_lock:
                with torch.no_grad():
                    audio = SileroTTS._model.apply_tts(
                        text=text,
                        speaker=SileroTTS._speaker,
                        sample_rate=SileroTTS._sample_rate,
                    )
            t_tts = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            if speed != 1.0:
                audio = self._apply_speed(audio, speed)
            t_speed = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            audio_np = audio.cpu().numpy()
            t_numpy = (time.perf_counter() - t0) * 1000

            with self._cache_lock:
                if len(self._cache) >= self._cache_max_size:
                    self._cache.pop(next(iter(self._cache)))
                self._cache[cache_key] = audio_np

            t_total = (time.perf_counter() - t_start) * 1000
            self.logger.info(
                f"[SYNTH] '{text[:25]}...' len={len(text)} | "
                f"wait_warmup={t_wait:.0f}ms tts={t_tts:.0f}ms "
                f"speed={t_speed:.0f}ms numpy={t_numpy:.0f}ms "
                f"TOTAL={t_total:.0f}ms"
            )
            return audio_np
        except Exception as e:
            self.logger.error(f"Ошибка синтеза: {e}")
            return None

    def synthesize_stream(
        self,
        chunks: List[str],
        speed: float = 1.0,
        on_first_chunk: Optional[Callable[[np.ndarray], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> List[np.ndarray]:
        results: List[np.ndarray] = []
        for i, chunk in enumerate(chunks):
            if should_stop and should_stop():
                break
            audio = self.synthesize(chunk, speed)
            if audio is None:
                continue
            results.append(audio)
            if i == 0 and on_first_chunk:
                on_first_chunk(audio)
        return results

    def _apply_speed(self, audio: torch.Tensor, speed: float) -> torch.Tensor:
        if speed == 1.0:
            return audio
        if speed > 1.0:
            indices = torch.linspace(0, len(audio) - 1, int(len(audio) / speed)).long()
            return audio[indices]
        indices = torch.linspace(0, len(audio) - 1, int(len(audio) * (1 / speed))).long()
        indices = indices.clamp(0, len(audio) - 1)
        return audio[indices]

    def set_voice(self, voice: str):
        SileroTTS._speaker = voice
        with self._cache_lock:
            self._cache.clear()

    def play(self, audio: np.ndarray):
        try:
            import sounddevice as sd
            sd.play(audio, SileroTTS._sample_rate)
            sd.wait()
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения: {e}")

    def save_to_file(self, audio: np.ndarray, filepath: str) -> bool:
        try:
            sf.write(filepath, audio, SileroTTS._sample_rate)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения: {e}")
            return False

    def get_sample_rate(self) -> int:
        return SileroTTS._sample_rate or self.config.sample_rate

    def cleanup(self):
        with self._cache_lock:
            self._cache.clear()
        self.logger.info("Ресурсы очищены")