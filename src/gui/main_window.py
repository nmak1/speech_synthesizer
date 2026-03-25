# src/gui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

from src.gui.text_editor import TextEditor
from src.gui.tts_controls import TTSControls
from src.gui.t9_widget import T9Widget
from src.gui.zoom_slider import ZoomSlider
from src.gui.styles import MAIN_STYLE
from src.tts_engine.silero_tts import SileroTTS
from src.text_processor.t9_predictor import T9Predictor
from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager
import os
import threading


class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager, config):
        super().__init__()
        self.config_manager = config_manager
        self.config = config
        self.logger = get_logger()

        self.tts_engine = None
        self.t9_predictor = None

        self.init_ui()
        self.init_components()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle(f"Голосовой синтезатор v{self.config.app_version}")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.tts_controls = TTSControls(self.config, self.on_voice_changed)
        main_layout.addWidget(self.tts_controls)

        splitter = QSplitter(Qt.Horizontal)

        self.text_editor = TextEditor(self.config, self.on_text_changed)
        splitter.addWidget(self.text_editor)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)

        splitter.setSizes([600, 200])
        main_layout.addWidget(splitter)

        self.t9_widget = T9Widget(self.config, self.on_t9_word_selected)
        main_layout.addWidget(self.t9_widget)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.zoom_slider = ZoomSlider(
            self.config.default_zoom,
            self.config.min_zoom,
            self.config.max_zoom,
            self.on_zoom_changed
        )
        bottom_layout.addWidget(self.zoom_slider)

        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        self.setStyleSheet(MAIN_STYLE)

    def init_components(self):
        try:
            self.logger.info("Инициализация TTS движка...")
            self.tts_engine = SileroTTS(self.config)
            self.status_bar.showMessage("TTS движок загружен")

            self.logger.info("Инициализация T9 предсказателя...")
            self.t9_predictor = T9Predictor(self.config)

            # Подключаем сигналы
            self.tts_controls.speak_requested.connect(self.on_speak)
            self.tts_controls.download_requested.connect(self.on_download)

        except Exception as e:
            self.logger.error(f"Ошибка инициализации компонентов: {e}")
            self.status_bar.showMessage(f"Ошибка: {e}")

    def on_voice_changed(self, voice_name: str):
        self.logger.info(f"Выбран голос: {voice_name}")
        if self.tts_engine:
            self.tts_engine.set_voice(voice_name)
            self.status_bar.showMessage(f"Выбран голос: {voice_name}")

    def on_text_changed(self):
        """Обработчик изменения текста для T9"""
        if not self.t9_widget or not self.t9_widget.is_enabled():
            return

        text = self.text_editor.get_text()
        if not text:
            self.t9_widget.update_suggestions([])
            return

        # Получаем последнее слово
        # Разбиваем по пробелам и знакам препинания
        import re
        words = re.findall(r'[\wа-яА-ЯёЁ]+', text)

        if words:
            # Берем последнее слово
            current_word = words[-1]

            # Если слово не пустое, получаем предсказания
            if current_word and len(current_word) >= 1:
                predictions = self.t9_predictor.predict(current_word)

                # Логируем для отладки
                self.logger.debug(f"T9: слово='{current_word}', предсказания={predictions}")

                self.t9_widget.update_suggestions(predictions)
            else:
                self.t9_widget.update_suggestions([])
        else:
            self.t9_widget.update_suggestions([])

    def on_t9_word_selected(self, word: str):
        current_text = self.text_editor.get_text()
        words = current_text.split()

        if words:
            words[-1] = word
            new_text = " ".join(words)
            self.text_editor.set_text(new_text)
        else:
            self.text_editor.set_text(word)

    def on_zoom_changed(self, zoom_value: int):
        self.text_editor.set_zoom(zoom_value)
        self.config.default_zoom = zoom_value
        self.config_manager.save_config(self.config)

    def on_speak(self):
        """Обработка озвучивания"""
        if not self.tts_engine:
            self.status_bar.showMessage("TTS движок не загружен")
            return

        text = self.text_editor.get_text()
        if not text or not text.strip():
            self.status_bar.showMessage("Введите текст для озвучивания")
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите текст для озвучивания")
            return

        self.logger.info(f"Озвучивание текста: {text[:100]}...")
        self.status_bar.showMessage("Синтез речи...")
        speed = self.tts_controls.get_speed()

        def synthesize_and_play():
            try:
                # Синтез
                audio = self.tts_engine.synthesize(text, speed)

                if audio is not None:
                    self.logger.info(f"Аудио синтезировано, длина: {len(audio)} samples")
                    self.status_bar.showMessage("Воспроизведение...")
                    # Воспроизведение
                    self.tts_engine.play(audio)
                    self.status_bar.showMessage("Готово")
                    self.logger.info("Воспроизведение завершено")
                else:
                    error_msg = "Ошибка синтеза речи"
                    self.logger.error(error_msg)
                    self.status_bar.showMessage(error_msg)
                    QMessageBox.warning(self, "Ошибка",
                                        "Не удалось синтезировать речь. Проверьте текст и попробуйте снова.")

            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                self.logger.error(error_msg)
                self.status_bar.showMessage(error_msg)
                QMessageBox.critical(self, "Ошибка", error_msg)
            finally:
                # Возвращаем кнопку в исходное состояние
                self.tts_controls.on_speak_finished()

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=synthesize_and_play, daemon=True)
        thread.start()

    def on_download(self):
        """Обработка сохранения"""
        if not self.tts_engine:
            self.status_bar.showMessage("TTS движок не загружен")
            return

        text = self.text_editor.get_text()
        if not text or not text.strip():
            self.status_bar.showMessage("Введите текст для сохранения")
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите текст для сохранения")
            return

        self.logger.info(f"Сохранение текста: {text[:100]}...")
        self.status_bar.showMessage("Синтез для сохранения...")
        speed = self.tts_controls.get_speed()

        def synthesize_and_save():
            try:
                # Синтез
                audio = self.tts_engine.synthesize(text, speed)

                if audio is not None:
                    self.logger.info(f"Аудио синтезировано, длина: {len(audio)} samples")

                    # Сохраняем
                    from datetime import datetime
                    filename = f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    download_dir = os.path.expanduser("~/Downloads/VoiceSynthesizer")
                    os.makedirs(download_dir, exist_ok=True)
                    filepath = os.path.join(download_dir, filename)

                    if self.tts_engine.save_to_file(audio, filepath):
                        success_msg = f"Аудио сохранено: {filename}"
                        self.logger.info(success_msg)
                        self.status_bar.showMessage(success_msg)
                        QMessageBox.information(self, "Успешно", f"Аудио сохранено в:\n{filepath}")
                    else:
                        error_msg = "Ошибка сохранения файла"
                        self.logger.error(error_msg)
                        self.status_bar.showMessage(error_msg)
                        QMessageBox.warning(self, "Ошибка", "Не удалось сохранить аудио файл")
                else:
                    error_msg = "Ошибка синтеза речи"
                    self.logger.error(error_msg)
                    self.status_bar.showMessage(error_msg)
                    QMessageBox.warning(self, "Ошибка", "Не удалось синтезировать речь")

            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                self.logger.error(error_msg)
                self.status_bar.showMessage(error_msg)
                QMessageBox.critical(self, "Ошибка", error_msg)
            finally:
                self.tts_controls.on_download_finished()

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=synthesize_and_save, daemon=True)
        thread.start()

    def load_settings(self):
        settings = QSettings("VoiceSynthesizer", "App")

        last_voice = settings.value("last_voice", self.config.available_voices[0])
        if isinstance(last_voice, str):
            self.tts_controls.set_current_voice(last_voice)
            self.on_voice_changed(last_voice)

        zoom = settings.value("zoom", self.config.default_zoom, type=int)
        self.zoom_slider.set_value(zoom)

        t9_enabled = settings.value("t9_enabled", False, type=bool)
        if t9_enabled and self.t9_widget:
            self.t9_widget.enable()

    def closeEvent(self, event):
        settings = QSettings("VoiceSynthesizer", "App")
        settings.setValue("last_voice", self.tts_controls.get_current_voice())
        settings.setValue("zoom", self.zoom_slider.get_value())
        settings.setValue("t9_enabled", self.t9_widget.is_enabled() if self.t9_widget else False)
        event.accept()