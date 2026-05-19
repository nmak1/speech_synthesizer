# src/gui/main_window.py
import os
import sys
import threading
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QLabel, QFrame, QApplication
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QIcon, QPixmap

from src.gui.text_editor import TextEditor
from src.gui.tts_controls import TTSControls
from src.gui.t9_widget import T9Widget
from src.gui.zoom_slider import ZoomSlider
from src.gui.styles import MAIN_STYLE
from src.tts_engine.silero_tts import SileroTTS
from src.text_processor.t9_predictor import T9Predictor
from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager


class MainWindow(QMainWindow):
    def __init__(self, config_manager, config):
        super().__init__()
        self.config_manager = config_manager
        self.config = config
        self.logger = get_logger()
        self.tts_engine = None
        self.t9_predictor = None
        self._synthesis_lock = threading.Lock()
        self._is_zooming = False

        self.init_ui()
        self.init_components()
        self.load_settings()

    def get_resource_path(self, relative_path):
        """Получение правильного пути к файлам (для разработки и скомпилированной версии)"""
        try:
            # PyInstaller создает временную папку и хранит путь в _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def init_ui(self):
        self.setWindowTitle("Free Talk - Голосовой синтезатор")
        self.setMinimumSize(1200, 800)

        # Загрузка иконки для окна
        icon = QIcon()

        # Пути для поиска иконки
        search_paths = [
            # Путь для скомпилированной версии
            self.get_resource_path("logo.ico"),
            self.get_resource_path("logo.png"),
            self.get_resource_path("logo_big.png"),
            self.get_resource_path("imeg/logo.ico"),
            self.get_resource_path("imeg/logo.png"),
            self.get_resource_path("imeg/logo_big.png"),
            self.get_resource_path("imeg/logo_highres.png"),
            # Пути для установленной версии (Program Files)
            os.path.join(os.path.dirname(sys.executable), "logo.ico"),
            os.path.join(os.path.dirname(sys.executable), "logo.png"),
            os.path.join(os.path.dirname(sys.executable), "logo_big.png"),
            os.path.join(os.path.dirname(sys.executable), "imeg", "logo.ico"),
            os.path.join(os.path.dirname(sys.executable), "imeg", "logo.png"),
            # Локальные пути для разработки
            "logo.ico",
            "logo.png",
            "logo_big.png",
            "imeg/logo.ico",
            "imeg/logo.png",
            "imeg/logo_big.png",
            "imeg/logo_highres.png",
        ]

        icon_loaded = False
        for path in search_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # Добавляем несколько размеров для лучшего отображения
                    for size in [16, 24, 32, 48, 64, 128, 256]:
                        scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        icon.addPixmap(scaled)
                    self.setWindowIcon(icon)
                    self.logger.info(f"Иконка окна загружена: {path}")
                    icon_loaded = True
                    break

        if not icon_loaded:
            self.logger.warning("Иконка окна не найдена, используется стандартная")
            # Пробуем установить иконку через стиль Windows
            try:
                import ctypes
                myappid = 'freetalk.synthesizer.version1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        # Верхняя панель с логотипом
        top = QWidget()
        top.setFixedHeight(220)
        top.setStyleSheet("background-color: #f8f9fa; border-bottom: 2px solid #e0e0e0;")
        top_layout = QHBoxLayout(top)

        # Логотип в верхней панели
        logo_label = QLabel()

        # Пути для логотипа
        logo_paths = [
            self.get_resource_path("logo_big.png"),
            self.get_resource_path("imeg/logo_big.png"),
            self.get_resource_path("imeg/logo_highres.png"),
            os.path.join(os.path.dirname(sys.executable), "logo_big.png"),
            os.path.join(os.path.dirname(sys.executable), "imeg", "logo_big.png"),
            "logo_big.png",
            "imeg/logo_big.png",
            "imeg/logo_highres.png",
        ]

        logo_found = False
        for path in logo_paths:
            if os.path.exists(path):
                pix = QPixmap(path)
                if not pix.isNull():
                    scaled = pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    logo_label.setPixmap(scaled)
                    logo_found = True
                    self.logger.info(f"Логотип загружен: {path}")
                    break

        if not logo_found:
            logo_label.setText("FREE TALK")
            logo_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #4CAF50;")

        logo_label.setFixedSize(200, 200)
        logo_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(logo_label)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(170)
        sep.setStyleSheet("background-color: #cccccc;")
        top_layout.addWidget(sep)

        # Кнопки управления
        self.tts_controls = TTSControls(self.config, self.on_voice_changed)
        top_layout.addWidget(self.tts_controls, 1)

        layout.addWidget(top)

        # Редактор текста
        splitter = QSplitter(Qt.Horizontal)
        self.text_editor = TextEditor(self.config, self.on_text_changed)
        splitter.addWidget(self.text_editor)
        splitter.addWidget(QWidget())
        splitter.setSizes([700, 200])
        layout.addWidget(splitter)

        # T9
        self.t9_widget = T9Widget(self.config, self.on_t9_word_selected)
        layout.addWidget(self.t9_widget)

        # Зум-слайдер
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.zoom_slider = ZoomSlider(self.config.default_zoom, 50, 400, self.on_zoom_changed)
        self.zoom_slider.zoom_finished.connect(self.on_zoom_finished)
        bottom.addWidget(self.zoom_slider)
        layout.addLayout(bottom)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        self.setStyleSheet(MAIN_STYLE)

    def init_components(self):
        try:
            self.tts_engine = SileroTTS(self.config)
            self.t9_predictor = T9Predictor(self.config)
            self.tts_controls.speak_requested.connect(self.on_speak)
            self.tts_controls.download_requested.connect(self.on_download)
            self.status_bar.showMessage("TTS движок загружен")
        except Exception as e:
            self.logger.error(f"Ошибка: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def on_voice_changed(self, voice):
        if self.tts_engine:
            self.tts_engine.set_voice(voice)

    def on_text_changed(self):
        text = self.text_editor.get_text()
        if self.t9_widget and self.t9_widget.is_enabled() and text:
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
        self._is_zooming = True
        try:
            self.text_editor.set_zoom(value)
            self.config.default_zoom = value
            self.config_manager.save_config(self.config)
            QApplication.processEvents()
        finally:
            pass

    def on_zoom_finished(self):
        self._is_zooming = False
        if self.text_editor and hasattr(self.text_editor, 'setFocus'):
            self.text_editor.setFocus()
        QApplication.processEvents()
        self.status_bar.showMessage("Масштаб изменен", 2000)

    def on_speak(self):
        if not self._synthesis_lock.acquire(blocking=False):
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        text = self.text_editor.get_text()
        if not text.strip():
            self._synthesis_lock.release()
            self.tts_controls.enable_buttons()
            return

        self.status_bar.showMessage("Синтез речи...")
        speed = self.tts_controls.get_speed()

        def task():
            try:
                audio = self.tts_engine.synthesize(text, speed)
                if audio is not None:
                    self.tts_engine.play(audio)
                    self.status_bar.showMessage("Готово")
            except Exception as e:
                self.logger.error(f"Ошибка синтеза: {e}")
                self.status_bar.showMessage("Ошибка синтеза")
            finally:
                self._synthesis_lock.release()
                QTimer.singleShot(0, self.tts_controls.enable_buttons)

        threading.Thread(target=task, daemon=True).start()

    def on_download(self):
        if not self._synthesis_lock.acquire(blocking=False):
            self.status_bar.showMessage("Синтез уже выполняется")
            return

        text = self.text_editor.get_text()
        if not text.strip():
            self._synthesis_lock.release()
            self.tts_controls.enable_buttons()
            return

        self.status_bar.showMessage("Синтез для сохранения...")
        speed = self.tts_controls.get_speed()

        def task():
            audio = None
            try:
                audio = self.tts_engine.synthesize(text, speed)
                if audio is not None:
                    download_dir = os.path.expanduser("~/Downloads/FreeTalk")
                    os.makedirs(download_dir, exist_ok=True)

                    filename = f"FreeTalk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    filepath = os.path.join(download_dir, filename)

                    success = self.tts_engine.save_to_file(audio, filepath)

                    if success:
                        self.status_bar.showMessage(f"Сохранено: {filename}")
                        QTimer.singleShot(0, lambda: QMessageBox.information(
                            self, "Успешно", f"Аудио сохранено в:\n{filepath}"
                        ))
                    else:
                        self.status_bar.showMessage("Ошибка сохранения")
                else:
                    self.status_bar.showMessage("Ошибка синтеза")

            except Exception as e:
                self.logger.error(f"Ошибка при скачивании: {e}")
                self.status_bar.showMessage("Ошибка")
            finally:
                self._synthesis_lock.release()
                QTimer.singleShot(0, self.tts_controls.enable_buttons)
                if audio is not None:
                    del audio

        threading.Thread(target=task, daemon=True).start()

    def load_settings(self):
        settings = QSettings("FreeTalk", "App")
        voice = settings.value("last_voice", "aidar")
        self.tts_controls.set_current_voice(voice)
        zoom = settings.value("zoom", 100, type=int)
        self.zoom_slider.set_value(zoom)

    def closeEvent(self, event):
        settings = QSettings("FreeTalk", "App")
        settings.setValue("last_voice", self.tts_controls.get_current_voice())
        settings.setValue("zoom", self.zoom_slider.get_value())
        if hasattr(self.tts_engine, 'cleanup'):
            self.tts_engine.cleanup()
        event.accept()