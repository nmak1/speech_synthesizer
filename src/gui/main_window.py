# src/gui/main_window.py
import os
import sys
import re
import time
import threading
from datetime import datetime
from typing import List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QMessageBox, QLabel, QFrame, QApplication,
    QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

from src.gui.text_editor import TextEditor
from src.gui.tts_controls import TTSControls
from src.gui.t9_widget import T9Widget
from src.gui.zoom_slider import ZoomSlider
from src.gui.styles import MAIN_STYLE
from src.tts_engine.silero_tts import SileroTTS
from src.tts_engine.audio_player import AudioPlayer
from src.text_processor.t9_predictor import T9Predictor
from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")


class MainWindow(QMainWindow):
    _first_sample_signal = pyqtSignal(float)
    _ready_signal = pyqtSignal()
    _play_finished_signal = pyqtSignal()
    _download_ready_signal = pyqtSignal(object)

    def __init__(self, config_manager, config):
        super().__init__()
        self.config_manager = config_manager
        self.config = config
        self.logger = get_logger()
        self.tts_engine: Optional[SileroTTS] = None
        self.audio_player: Optional[AudioPlayer] = None
        self.t9_predictor = None
        self._synthesis_lock = threading.Lock()
        self._stop_current = threading.Event()
        self._is_zooming = False

        self.init_ui()
        self.init_components()
        self.load_settings()

        self._first_sample_signal.connect(self._on_first_sample)
        self._ready_signal.connect(self._on_model_ready)
        self._play_finished_signal.connect(self._finish_synthesis)  # ← новый
        self._download_ready_signal.connect(self._on_download_ready)
    # ---------- Ресурсы ----------

    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    # ---------- UI ----------

    def init_ui(self):
        self.setWindowTitle("Free Talk - Голосовой синтезатор")
        self.setMinimumSize(1200, 800)

        # --- Иконка окна ---
        icon = QIcon()
        icon_paths = [
            self.get_resource_path("imeg/logo.ico"),
            self.get_resource_path("logo.ico"),
            os.path.join(os.path.dirname(sys.executable), "imeg", "logo.ico"),
            os.path.join(os.path.dirname(sys.executable), "logo.ico"),
            "imeg/logo.ico",
            "logo.ico",
        ]
        icon_loaded = False
        for path in icon_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    for size in [16, 24, 32, 48, 64, 128, 256]:
                        icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.setWindowIcon(icon)
                    icon_loaded = True
                    break
        if not icon_loaded:
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("freetalk.synthesizer.version1.0")
            except Exception:
                pass

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- Верхняя панель ---
        top = QWidget()
        top.setMinimumHeight(280)
        top.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        top.setStyleSheet("background-color: #f8f9fa; border-bottom: 2px solid #e0e0e0;")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 16, 16, 16)
        top_layout.setSpacing(16)

        # --- Логотип (сохраняем пропорции) ---
        logo_label = QLabel()
        LOGO_MAX_W = 260
        LOGO_MAX_H = 180

        logo_paths = [
            self.get_resource_path("imeg/logo.png"),
            self.get_resource_path("logo.png"),
            os.path.join(os.path.dirname(sys.executable), "imeg", "logo.png"),
            os.path.join(os.path.dirname(sys.executable), "logo.png"),
            "imeg/logo.png",
            "logo.png",
        ]

        logo_found = False
        for path in logo_paths:
            if not os.path.exists(path):
                continue
            pix = QPixmap(path)
            if pix.isNull():
                continue
            pix.setDevicePixelRatio(1.0)
            scaled = pix.scaled(
                LOGO_MAX_W, LOGO_MAX_H,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            logo_label.setPixmap(scaled)
            logo_label.setFixedSize(LOGO_MAX_W, LOGO_MAX_H)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_found = True
            self.logger.info(
                f"Логотип загружен: {path}, "
                f"исходник {pix.width()}x{pix.height()}, "
                f"после scale {scaled.width()}x{scaled.height()}"
            )
            break

        if not logo_found:
            self.logger.warning(f"Логотип не найден, проверены пути: {logo_paths}")
            logo_label.setText("FREE\nTALK")
            logo_label.setStyleSheet("""
                font-size: 42px;
                font-weight: bold;
                color: #4CAF50;
                background: transparent;
            """)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setFixedSize(LOGO_MAX_W, LOGO_MAX_H)

        top_layout.addWidget(logo_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(200)
        sep.setStyleSheet("background-color: #cccccc;")
        top_layout.addWidget(sep)

        # --- Панель управления TTS ---
        self.tts_controls = TTSControls(self.config, self.on_voice_changed)
        top_layout.addWidget(self.tts_controls, 1)
        layout.addWidget(top)

        # --- Редактор текста ---
        self.text_editor = TextEditor(self.config, self.on_text_changed)
        layout.addWidget(self.text_editor, 1)

        # --- T9 ---
        self.t9_widget = T9Widget(self.config, self.on_t9_word_selected)
        layout.addWidget(self.t9_widget)

        # --- Зум ---
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.zoom_slider = ZoomSlider(self.config.default_zoom, 50, 400, self.on_zoom_changed)
        self.zoom_slider.zoom_finished.connect(self.on_zoom_finished)
        bottom.addWidget(self.zoom_slider)
        layout.addLayout(bottom)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Загрузка модели...")
        self.setStyleSheet(MAIN_STYLE)

    def init_components(self):
        """Инициализация фоновых компонентов. Все ошибки — в лог и QMessageBox."""
        try:
            self.tts_engine = SileroTTS(self.config, preload=True, warmup=True)
        except Exception as e:
            self.logger.error(f"Ошибка создания SileroTTS: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка TTS", f"Не удалось создать движок TTS:\n{e}")
            return

        try:
            self.audio_player = AudioPlayer(self.config)
        except Exception as e:
            self.logger.error(f"Ошибка создания AudioPlayer: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка AudioPlayer", str(e))
            return

        try:
            self.t9_predictor = T9Predictor(self.config)
        except Exception as e:
            self.logger.error(f"Ошибка создания T9Predictor: {e}", exc_info=True)
            # T9 не критичен — продолжаем без него
            self.t9_predictor = None

        try:
            self.tts_controls.speak_requested.connect(self.on_speak)
            self.tts_controls.download_requested.connect(self.on_download)
        except Exception as e:
            self.logger.error(f"Ошибка подключения сигналов: {e}", exc_info=True)

        # Блокируем кнопки до окончания warm-up
        try:
            self.tts_controls.disable_buttons()
        except Exception:
            pass
        self.status_bar.showMessage("TTS движок загружается в фоне...")

        threading.Thread(target=self._wait_model_ready, daemon=True).start()

    def _wait_model_ready(self):
        """Фоновый поток: ждёт готовности модели и шлёт сигнал в UI."""
        for _ in range(1200):  # до 120 сек
            if self.tts_engine and self.tts_engine.is_warmup_done():
                if self.audio_player and self.tts_engine.get_sample_rate():
                    try:
                        self.audio_player.prewarm(self.tts_engine.get_sample_rate())
                    except Exception as e:
                        self.logger.warning(f"Prewarm не удался: {e}")

                self._ready_signal.emit()
                return
            time.sleep(0.1)

        self.logger.warning("Модель не готова за 120 сек")
        self._ready_signal.emit()

    def _on_model_ready(self):
        """Вызывается в главном потоке, когда модель и warm-up готовы."""
        try:
            self.tts_controls.enable_buttons()
        except Exception:
            pass
        self.status_bar.showMessage("Готов к работе")

    # ---------- Обработчики ----------

    def on_voice_changed(self, voice):
        if self.tts_engine:
            self.tts_engine.set_voice(voice)

    def on_text_changed(self):
        if not hasattr(self, "text_editor") or self.text_editor is None:
            return
        if not hasattr(self, "t9_widget") or self.t9_widget is None:
            return
        if not hasattr(self, "t9_predictor") or self.t9_predictor is None:
            return

        text = self.text_editor.get_text()
        if self.t9_widget.is_enabled() and text:
            words = text.split()
            if words:
                predictions = self.t9_predictor.predict(words[-1])
                self.t9_widget.update_suggestions(predictions)

    def on_t9_word_selected(self, word):
        text = self.text_editor.get_text()
        words = text.split()
        if words:
            words[-1] = word
            self.text_editor.set_text(" ".join(words))
        else:
            self.text_editor.set_text(word)

    def on_zoom_changed(self, value):
        """Вызывается при каждом движении ползунка — конфиг НЕ сохраняем."""
        self._is_zooming = True
        try:
            self.text_editor.set_zoom(value)
            self.config.default_zoom = value
        finally:
            pass

    def on_zoom_finished(self):
        """Вызывается, когда пользователь отпустил ползунок — сохраняем один раз."""
        self._is_zooming = False
        if self.text_editor and hasattr(self.text_editor, "setFocus"):
            self.text_editor.setFocus()

        try:
            self.config_manager.save_config(self.config)
        except Exception as e:
            self.logger.warning(f"Не удалось сохранить конфиг: {e}")

        QApplication.processEvents()
        self.status_bar.showMessage("Масштаб изменён", 2000)

    # ---------- Синтез ----------

    def _split_sentences(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []
        parts = SENTENCE_SPLIT_RE.split(text)
        result: List[str] = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if len(p) > 220:
                sub = re.split(r"(?<=[,;:])\s+", p)
                buf = ""
                for s in sub:
                    if len(buf) + len(s) + 1 <= 220:
                        buf = f"{buf} {s}".strip()
                    else:
                        if buf:
                            result.append(buf)
                        buf = s
                if buf:
                    result.append(buf)
            else:
                result.append(p)
        return result

    def on_speak(self):
        if not self._synthesis_lock.acquire(blocking=False):
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        text = self.text_editor.get_text()
        if not text.strip():
            self._synthesis_lock.release()
            self.tts_controls.enable_buttons()
            return

        # Прерываем предыдущее воспроизведение только если оно активно
        if self.audio_player and self.audio_player.is_playing_audio():
            self._stop_current.set()
            self.audio_player.hard_stop()
        self._stop_current = threading.Event()

        speed = self.tts_controls.get_speed()
        self.status_bar.showMessage("Синтез речи...")
        self.tts_controls.disable_buttons()

        sentences = self._split_sentences(text)

        def task():
            try:
                sample_rate = self.tts_engine.get_sample_rate()

                def chunk_generator():
                    for i, s in enumerate(sentences):
                        if self._stop_current.is_set():
                            return
                        audio = self.tts_engine.synthesize(s, speed)
                        if audio is None:
                            continue
                        yield audio

                def on_first(dt_ms: float):
                    self._first_sample_signal.emit(dt_ms)

                self.logger.info("Клик → старт воспроизведения: измеряется в on_first_sample")

                self.audio_player.play_chunks(
                    chunk_generator(),
                    sample_rate,
                    on_finished=self._on_play_finished,
                    on_first_sample=on_first,
                )
            except Exception as e:
                self.logger.error(f"Ошибка синтеза: {e}", exc_info=True)
                self.status_bar.showMessage("Ошибка синтеза")
                self._finish_synthesis()

        threading.Thread(target=task, daemon=True).start()

    def _on_first_sample(self, dt_ms: float):
        self.status_bar.showMessage(f"Воспроизведение (задержка ~{dt_ms:.0f} мс)", 5000)

    def _on_play_finished(self):
        """Вызывается из worker-потока AudioPlayer. Шлём сигнал в UI."""
        self._play_finished_signal.emit()

    def _finish_synthesis(self):
        self.status_bar.showMessage("Готово", 3000)
        try:
            self.tts_controls.enable_buttons()
        except Exception:
            pass
        try:
            self._synthesis_lock.release()
        except RuntimeError:
            pass

    # ---------- Скачивание ----------

    def on_download(self):
        self.logger.info("[DOWNLOAD] on_download ВЫЗВАН")

        if not self._synthesis_lock.acquire(blocking=False):
            self.logger.warning("[DOWNLOAD] lock занят — выход")
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        self.logger.info("[DOWNLOAD] lock взят")

        text = self.text_editor.get_text()
        if not text.strip():
            self.logger.warning("[DOWNLOAD] текст пустой — выход")
            self._synthesis_lock.release()
            self.tts_controls.enable_buttons()
            return

        self.status_bar.showMessage("Синтез для сохранения...")
        speed = self.tts_controls.get_speed()
        sentences = self._split_sentences(text)
        self.logger.info(f"[DOWNLOAD] старт синтеза, {len(sentences)} предложений")

        def task():
            audio_parts = []
            try:
                for i, s in enumerate(sentences):
                    a = self.tts_engine.synthesize(s, speed)
                    if a is not None:
                        audio_parts.append(a)

                if not audio_parts:
                    self.logger.warning("[DOWNLOAD] нет аудио — выход")
                    QTimer.singleShot(0, lambda: self.status_bar.showMessage("Ошибка синтеза"))
                    return

                import numpy as np
                audio = np.concatenate(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
                self.logger.info(f"[DOWNLOAD] аудио собрано, длина: {len(audio)} сэмплов")

                # Передаём аудио в главный поток для диалога
                self._download_ready_signal.emit(audio)
            except Exception as e:
                self.logger.error(f"[DOWNLOAD] ошибка: {e}", exc_info=True)
                QTimer.singleShot(0, lambda: self.status_bar.showMessage("Ошибка синтеза"))
                QTimer.singleShot(0, self.tts_controls.enable_buttons)
                try:
                    self._synthesis_lock.release()
                except RuntimeError:
                    pass

        threading.Thread(target=task, daemon=True).start()

    def _on_download_ready(self, audio):
        """Вызывается в главном потоке после синтеза. Открывает диалог сохранения."""
        try:
            # Предлагаем папку ~/Downloads/FreeTalk и имя файла по умолчанию
            default_dir = os.path.expanduser("~/Downloads/FreeTalk")
            os.makedirs(default_dir, exist_ok=True)
            default_name = f"FreeTalk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            default_path = os.path.join(default_dir, default_name)

            # Диалог выбора файла
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить аудио",
                default_path,
                "WAV файлы (*.wav);;Все файлы (*.*)"
            )

            if not filepath:
                # Пользователь отменил
                self.logger.info("[DOWNLOAD] пользователь отменил диалог")
                self.status_bar.showMessage("Сохранение отменено", 3000)
                return

            # Сохраняем
            if self.tts_engine.save_to_file(audio, filepath):
                self.logger.info(f"[DOWNLOAD] успешно сохранено: {filepath}")
                self.status_bar.showMessage(f"Сохранено: {os.path.basename(filepath)}", 5000)
                QMessageBox.information(
                    self, "Успешно",
                    f"Аудио сохранено в:\n{filepath}"
                )
            else:
                self.logger.error("[DOWNLOAD] save_to_file вернул False")
                self.status_bar.showMessage("Ошибка сохранения")
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить файл")
        finally:
            # Отпускаем lock и включаем кнопки
            self.tts_controls.enable_buttons()
            try:
                self._synthesis_lock.release()
                self.logger.info("[DOWNLOAD] lock отпущен")
            except RuntimeError:
                pass

    # ---------- Настройки ----------

    def load_settings(self):
        """Загрузка настроек. Безопасно — если UI ещё не готов, не падаем."""
        settings = QSettings("FreeTalk", "App")

        # Голос
        if hasattr(self, "tts_controls") and self.tts_controls is not None:
            voice = settings.value("last_voice", "aidar")
            try:
                self.tts_controls.set_current_voice(voice)
            except Exception as e:
                self.logger.warning(f"Не удалось установить голос: {e}")

        # Зум
        if hasattr(self, "zoom_slider") and self.zoom_slider is not None:
            zoom = settings.value("zoom", 100, type=int)
            try:
                self.zoom_slider.set_value(zoom)
            except Exception as e:
                self.logger.warning(f"Не удалось установить зум: {e}")

    def closeEvent(self, event):
        settings = QSettings("FreeTalk", "App")
        try:
            settings.setValue("last_voice", self.tts_controls.get_current_voice())
            settings.setValue("zoom", self.zoom_slider.get_value())
        except Exception:
            pass

        self._stop_current.set()
        if self.audio_player:
            try:
                self.audio_player.cleanup()
            except Exception:
                pass
        if self.tts_engine and hasattr(self.tts_engine, "cleanup"):
            try:
                self.tts_engine.cleanup()
            except Exception:
                pass
        event.accept()