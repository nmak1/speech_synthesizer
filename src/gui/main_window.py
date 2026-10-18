# src/gui/main_window.py
import os
import sys
import re
from datetime import datetime
from typing import List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QMessageBox, QLabel, QFrame, QApplication,
    QSizePolicy, QFileDialog, QAction
)
from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence

from src.gui.text_editor import TextEditor
from src.gui.tts_controls import TTSControls
from src.gui.t9_widget import T9Widget
from src.gui.format_bar import FormatBar
from src.gui.zoom_slider import ZoomSlider
from src.gui.styles import MAIN_STYLE
from src.tts_engine.silero_tts import SileroTTS
from src.tts_engine.audio_player import AudioPlayer
from src.text_processor.t9_predictor import T9Predictor
from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager
from src.workers import ModelReadyWorker, SynthesizePlayWorker, SynthesizeSaveWorker
from src.paths import find_resource, resource_path
from src.version import __version__, APP_USER_MODEL_ID


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")


class MainWindow(QMainWindow):
    def __init__(self, config_manager, config):
        super().__init__()
        self.config_manager = config_manager
        self.config = config
        self.logger = get_logger()
        self.tts_engine: Optional[SileroTTS] = None
        self.audio_player: Optional[AudioPlayer] = None
        self.t9_predictor = None
        self._synthesis_busy = False
        self._is_zooming = False
        self._model_worker: Optional[ModelReadyWorker] = None
        self._play_worker: Optional[SynthesizePlayWorker] = None
        self._save_worker: Optional[SynthesizeSaveWorker] = None

        self.init_ui()
        self.init_actions()
        self.init_components()
        self.load_settings()
    # ---------- Ресурсы ----------

    @staticmethod
    def get_resource_path(relative_path: str) -> str:
        """Единый резолвер ресурсов (dev / PyInstaller) — см. src/paths.py."""
        return resource_path(relative_path)

    # ---------- UI ----------

    def init_ui(self):
        self.setWindowTitle(f"Free Talk v{__version__} - Голосовой синтезатор")
        self.setMinimumSize(1200, 800)

        # --- Иконка окна ---
        icon = QIcon()
        icon_path = find_resource(
            "imeg/logo.ico", "logo.ico", "imeg/logo.png", "logo.png"
        )
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                for size in [16, 24, 32, 48, 64, 128, 256]:
                    icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.setWindowIcon(icon)
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
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

        logo_path = find_resource("imeg/logo.png", "logo.png", "imeg/logo.ico", "logo.ico")

        if logo_path:
            pix = QPixmap(logo_path)
            if not pix.isNull():
                pix.setDevicePixelRatio(1.0)
                scaled = pix.scaled(
                    LOGO_MAX_W, LOGO_MAX_H,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                logo_label.setPixmap(scaled)
                logo_label.setAlignment(Qt.AlignCenter)
                self.logger.info(f"Логотип загружен: {logo_path}")
            else:
                logo_path = None

        if not logo_path:
            self.logger.warning("Логотип не найден через src/paths.find_resource")
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

        # --- Панель форматирования (шрифты, размер, цвет) ---
        self.format_bar = FormatBar(self.config)
        self.format_bar.font_changed.connect(self.text_editor.set_font_family)
        self.format_bar.size_changed.connect(self.text_editor.set_font_size)
        self.format_bar.color_changed.connect(self.text_editor.set_text_color)
        self.format_bar.bold_toggled.connect(self.text_editor.set_bold)
        self.format_bar.italic_toggled.connect(self.text_editor.set_italic)
        self.text_editor.format_changed.connect(self._sync_format_bar)
        layout.addWidget(self.format_bar)

        # --- T9 (кнопка включения убрана из интерфейса по решению пользователя;
        #     знаки препинания остаются доступны) ---
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

    # ---------- Горячие клавиши ----------

    def init_actions(self):
        """Действия с горячими клавишами (работают глобально в окне)."""
        def make(text, shortcut, slot):
            act = QAction(text, self)
            act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(slot)
            self.addAction(act)
            return act

        self.act_speak = make("Озвучить текст", "Ctrl+Return", self.on_speak)
        self.act_download = make("Сохранить аудио", "Ctrl+S", self.on_download)
        self.act_stop = make("Остановить воспроизведение", "Esc", self.on_stop_playback)
        self.act_clear = make("Очистить текст", "Ctrl+Del", self.on_clear_text)
        self.act_focus = make("Фокус в редактор", "Alt+R", lambda: self.text_editor.text_edit.setFocus())
        self.act_zoom_in = make("Увеличить масштаб", "Ctrl++", lambda: self._change_zoom(+10))
        self.act_zoom_out = make("Уменьшить масштаб", "Ctrl+-", lambda: self._change_zoom(-10))
        self.act_zoom_reset = make("Сбросить масштаб", "Ctrl+0", lambda: self._set_zoom(100))
        self.act_quit = make("Выход", "Ctrl+Q", self.close)

        # Меню «Файл» — действия видны и с подсказками клавиш
        file_menu = self.menuBar().addMenu("Файл")
        for act in (self.act_speak, self.act_download, None, self.act_clear, self.act_quit):
            if act is None:
                file_menu.addSeparator()
            else:
                file_menu.addAction(act)
        view_menu = self.menuBar().addMenu("Вид")
        for act in (self.act_zoom_in, self.act_zoom_out, self.act_zoom_reset):
            view_menu.addAction(act)

    def _change_zoom(self, delta: int):
        self._set_zoom(self.zoom_slider.get_value() + delta)

    def _set_zoom(self, value: int):
        value = max(50, min(400, value))
        self.zoom_slider.set_value(value)
        self.on_zoom_changed(value)
        self.on_zoom_finished()

    def on_stop_playback(self):
        """Esc — остановить текущее воспроизведение/синтез."""
        stopped = False
        if self._play_worker is not None and self._play_worker.isRunning():
            self._play_worker.stop()
            stopped = True
        if self.audio_player and self.audio_player.is_playing_audio():
            self.audio_player.hard_stop()
            stopped = True
        if stopped:
            self.status_bar.showMessage("Воспроизведение остановлено", 2000)

    def on_clear_text(self):
        self.text_editor.set_text("")
        self.text_editor.text_edit.setFocus()

    # ---------- Компоненты ----------

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

        # Динамическое обучение словаря T9 по набранному тексту (пакетно)
        if self.t9_predictor is not None and getattr(self.config, "t9_learning_enabled", True):
            self.text_editor.set_predictor(self.t9_predictor)
            self._learn_timer = QTimer(self)
            self._learn_timer.setSingleShot(True)
            self._learn_timer.setInterval(getattr(self.config, "t9_learn_interval_ms", 5000))
            self._learn_timer.timeout.connect(self._flush_t9_learning)
            self.text_editor.learn_requested.connect(self._schedule_t9_learning)

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

        # QThread-воркер вместо raw threading.Thread: ready() — сигнал в UI-поток
        self._model_worker = ModelReadyWorker(self.tts_engine, self.audio_player, parent=self)
        self._model_worker.ready.connect(self._on_model_ready)
        self._model_worker.start()

    # ---------- Динамическое обучение T9 ----------

    def _schedule_t9_learning(self, text: str):
        """Откладываем обучение; перечитываем текст в момент срабатывания таймера."""
        self._learn_timer.start()

    def _flush_t9_learning(self):
        if self.t9_predictor is None:
            return
        try:
            self.t9_predictor.learn_from_text(self.text_editor.get_text())
        except Exception as e:
            self.logger.warning(f"Обучение T9-словаря не удалось: {e}")

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
            words = re.findall(r"\S+", text)
            last = words[-1] if words else ""
            # чистим префикс от знаков препинания, ищем по буквам/цифрам
            prefix = re.sub(r"[^\w-]", "", last, flags=re.UNICODE)
            if prefix:
                predictions = self.t9_predictor.predict(prefix)
                self.t9_widget.update_suggestions(predictions)
            else:
                self.t9_widget.update_suggestions([])

    def _sync_format_bar(self):
        """Синхронизировать панель формата с текущим выделением в редакторе."""
        try:
            fmt = self.text_editor.current_format()
            self.format_bar.sync_from_editor(**fmt)
        except Exception as e:
            self.logger.debug(f"Не удалось синхронизировать панель формата: {e}")

    def on_t9_word_selected(self, word):
        """Замена последнего 'слова' (учитывая знаки препинания) или вставка пунктуации."""
        text = self.text_editor.get_text()

        # Пунктуация из панели T9 — добавляем к тексту
        if not re.search(r"[\w]", word, flags=re.UNICODE):
            new_text = f"{text}{word} " if text else word
            self.text_editor.set_text(new_text)
            return

        # Обычное слово из подсказок: заменяем последний токен
        match = re.search(r"\S*$", text)
        token = match.group(0) if match else ""
        m = re.match(r"^([^\w]*)(.*?)([^\w]*)$", token, flags=re.UNICODE)
        if m:
            leading, core, trailing = m.groups()
            new_token = leading + word + trailing
            start = len(text) - len(token)
            new_text = text[:start] + new_token + text[start + len(token):]
        else:
            new_text = (text + " " + word).strip()
        self.text_editor.set_text(new_text)

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
        if self._synthesis_busy:
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        text = self.text_editor.get_text()
        if not text.strip():
            self.tts_controls.enable_buttons()
            return

        # Прерываем предыдущее воспроизведение только если оно активно
        if self._play_worker is not None and self._play_worker.isRunning():
            self._play_worker.stop()
        if self.audio_player and self.audio_player.is_playing_audio():
            self.audio_player.hard_stop()

        speed = self.tts_controls.get_speed()
        self.status_bar.showMessage("Синтез речи...")
        self.tts_controls.disable_buttons()

        sentences = self._split_sentences(text)
        self._synthesis_busy = True

        # QThread вместо raw threading.Thread — все события в UI через сигналы
        self._play_worker = SynthesizePlayWorker(
            self.tts_engine, self.audio_player, sentences, speed,
            self.tts_engine.get_sample_rate(), parent=self,
        )
        self._play_worker.first_sample.connect(self._on_first_sample)
        self._play_worker.finished_ok.connect(self._finish_synthesis)
        self._play_worker.error.connect(self._on_synthesis_error)
        self._play_worker.start()

    def _on_synthesis_error(self, message: str):
        self.logger.error(f"Ошибка синтеза: {message}")
        self.status_bar.showMessage("Ошибка синтеза")
        self._finish_synthesis()

    def _on_first_sample(self, dt_ms: float):
        self.status_bar.showMessage(f"Воспроизведение (задержка ~{dt_ms:.0f} мс)", 5000)

    def _finish_synthesis(self):
        self.status_bar.showMessage("Готово", 3000)
        try:
            self.tts_controls.enable_buttons()
        except Exception:
            pass
        self._synthesis_busy = False

    # ---------- Скачивание ----------

    def on_download(self):
        if self._synthesis_busy:
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        text = self.text_editor.get_text()
        if not text.strip():
            self.tts_controls.enable_buttons()
            return

        self.status_bar.showMessage("Синтез для сохранения...")
        speed = self.tts_controls.get_speed()
        sentences = self._split_sentences(text)
        self._synthesis_busy = True
        self.tts_controls.disable_buttons()

        # QThread: синтез в фоне, диалог сохранения открывается в UI-потоке
        self._save_worker = SynthesizeSaveWorker(self.tts_engine, sentences, speed, parent=self)
        self._save_worker.audio_ready.connect(self._on_download_ready)
        self._save_worker.error.connect(self._on_save_error)
        self._save_worker.start()

    def _on_save_error(self, message: str):
        self.logger.error(f"[DOWNLOAD] ошибка: {message}")
        if message != "Отменено":
            self.status_bar.showMessage("Ошибка синтеза")
        self.tts_controls.enable_buttons()
        self._synthesis_busy = False

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
            # Включаем кнопки и освобождаем флаг занятости
            self.tts_controls.enable_buttons()
            self._synthesis_busy = False

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

        # Панель формата — синхронизируем с редактором после загрузки его настроек
        self._sync_format_bar()

    def closeEvent(self, event):
        settings = QSettings("FreeTalk", "App")
        try:
            settings.setValue("last_voice", self.tts_controls.get_current_voice())
            settings.setValue("zoom", self.zoom_slider.get_value())
        except Exception:
            pass
        # Форсируем сохранение текста/формата редактора
        try:
            self.text_editor.save_settings()
        except Exception:
            pass
        # Форсируем обучение словаря на недообработанном тексте
        try:
            if hasattr(self, "_learn_timer") and self._learn_timer.isActive():
                self._learn_timer.stop()
                self._flush_t9_learning()
        except Exception:
            pass

        # Останавливаем все QThread-воркеры корректно
        for worker in (self._model_worker, self._play_worker, self._save_worker):
            if worker is not None and worker.isRunning():
                try:
                    if hasattr(worker, "cancel"):
                        worker.cancel()
                    elif hasattr(worker, "stop"):
                        worker.stop()
                    worker.requestInterruption()
                    worker.wait(2000)
                except Exception:
                    pass

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