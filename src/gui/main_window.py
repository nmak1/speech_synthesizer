# src/gui/main_window.py
"""
Главное окно приложения Free Talk
"""
import os
import sys
import threading
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QLabel, QFrame  # Добавлен QFrame
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QIcon, QPixmap

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

    def create_logo_label(self):
        """Создание метки с логотипом - принудительное масштабирование"""
        logo_path = "logo.png"

        if os.path.exists(logo_path):
            try:
                # Загружаем оригинал
                original_pixmap = QPixmap(logo_path)
                if not original_pixmap.isNull():
                    # Принудительно масштабируем до 180x140
                    scaled_pixmap = original_pixmap.scaled(
                        180, 140,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )

                    logo_label = QLabel()
                    logo_label.setPixmap(scaled_pixmap)
                    logo_label.setFixedSize(180, 140)
                    logo_label.setScaledContents(True)  # Важно! Принудительное масштабирование
                    logo_label.setToolTip("Free Talk")
                    logo_label.setAlignment(Qt.AlignCenter)
                    logo_label.setStyleSheet("""
                        QLabel {
                            background-color: #f8f9fa;
                            border: 1px solid #e0e0e0;
                            border-radius: 5px;
                        }
                    """)

                    self.logger.info(f"Логотип загружен: {logo_path} -> 180x140")
                    return logo_label
            except Exception as e:
                self.logger.error(f"Ошибка загрузки логотипа: {e}")

        # Если нет логотипа, создаем текстовую метку
        logo_label = QLabel("Free Talk")
        logo_label.setFixedSize(180, 140)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        return logo_label

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle(f"Free Talk - Голосовой синтезатор v{self.config.app_version}")
        self.setMinimumSize(1200, 800)

        # Установка иконки приложения
        if os.path.exists("logo.ico"):
            self.setWindowIcon(QIcon("logo.ico"))
        elif os.path.exists("logo.png"):
            self.setWindowIcon(QIcon("logo.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Верхняя панель - делаем её выше для большого логотипа
        top_panel = QWidget()
        top_panel.setFixedHeight(150)
        top_panel.setMinimumHeight(150)
        top_panel.setMaximumHeight(150)
        top_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)

        # Добавляем логотип
        logo_label = self.create_logo_label()
        if logo_label:
            top_layout.addWidget(logo_label, 0)

        # Добавляем разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedWidth(3)
        separator.setFixedHeight(120)
        separator.setStyleSheet("background-color: #cccccc;")
        top_layout.addWidget(separator)

        # Панель управления TTS
        self.tts_controls = TTSControls(self.config, self.on_voice_changed)
        top_layout.addWidget(self.tts_controls, 1)

        main_layout.addWidget(top_panel)

        # Горизонтальный сплиттер для редактора
        splitter = QSplitter(Qt.Horizontal)

        # Редактор текста
        self.text_editor = TextEditor(self.config, self.on_text_changed)
        splitter.addWidget(self.text_editor)

        # Правая панель (можно добавить дополнительные настройки)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)

        splitter.setSizes([700, 200])
        main_layout.addWidget(splitter)

        # Панель T9
        self.t9_widget = T9Widget(self.config, self.on_t9_word_selected)
        main_layout.addWidget(self.t9_widget)

        # Нижняя панель с зум-слайдером
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

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Применяем стили
        self.setStyleSheet(MAIN_STYLE)

    def init_components(self):
        """Инициализация рабочих компонентов"""
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
            QMessageBox.critical(self, "Ошибка", f"Не удалось инициализировать компоненты:\n{str(e)}")

    def on_voice_changed(self, voice_name: str):
        """Обработчик смены голоса"""
        self.logger.info(f"Выбран голос: {voice_name}")
        if self.tts_engine:
            self.tts_engine.set_voice(voice_name)
            self.status_bar.showMessage(f"Выбран голос: {voice_name}")

    def on_text_changed(self):
        """Обработчик изменения текста"""
        if not self.t9_widget:
            return

        text = self.text_editor.get_text()
        if self.t9_widget.is_enabled() and text:
            words = text.split()
            if words:
                last_word = words[-1]
                if self.t9_predictor:
                    predictions = self.t9_predictor.predict(last_word)
                    self.t9_widget.update_suggestions(predictions)
                else:
                    self.t9_widget.update_suggestions([])
            else:
                self.t9_widget.update_suggestions([])
        else:
            self.t9_widget.update_suggestions([])

    def on_t9_word_selected(self, word: str):
        """Обработчик выбора слова из T9"""
        current_text = self.text_editor.get_text()
        words = current_text.split()

        if words:
            words[-1] = word
            new_text = " ".join(words)
            self.text_editor.set_text(new_text)
        else:
            self.text_editor.set_text(word)

    def on_zoom_changed(self, zoom_value: int):
        """Обработчик изменения масштаба"""
        self.text_editor.set_zoom(zoom_value)
        self.config.default_zoom = zoom_value
        self.config_manager.save_config(self.config)
        self.status_bar.showMessage(f"Масштаб: {zoom_value}%")

    def on_speak(self):
        """Обработка озвучивания"""
        if not self.tts_engine:
            self.status_bar.showMessage("TTS движок не загружен")
            QMessageBox.warning(self, "Ошибка", "TTS движок не загружен")
            self.tts_controls.enable_buttons()
            return

        text = self.text_editor.get_text()
        if not text or not text.strip():
            self.status_bar.showMessage("Введите текст для озвучивания")
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите текст для озвучивания")
            self.tts_controls.enable_buttons()
            return

        self.logger.info(f"Озвучивание текста: {text[:100]}...")
        self.status_bar.showMessage("Синтез речи...")
        speed = self.tts_controls.get_speed()

        def synthesize_and_play():
            try:
                audio = self.tts_engine.synthesize(text, speed)

                if audio is not None:
                    self.logger.info(f"Аудио синтезировано, длина: {len(audio)} samples")
                    self.status_bar.showMessage("Воспроизведение...")
                    self.tts_engine.play(audio)
                    self.status_bar.showMessage("Готово")
                else:
                    error_msg = "Ошибка синтеза речи"
                    self.logger.error(error_msg)
                    self.status_bar.showMessage(error_msg)
                    QMessageBox.warning(self, "Ошибка",
                                        "Не удалось синтезировать речь.\nПроверьте текст и попробуйте снова.")

            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                self.logger.error(error_msg)
                self.status_bar.showMessage(error_msg)
                QMessageBox.critical(self, "Ошибка", error_msg)
            finally:
                self.tts_controls.enable_buttons()

        thread = threading.Thread(target=synthesize_and_play, daemon=True)
        thread.start()

    def on_download(self):
        """Обработка сохранения"""
        if not self.tts_engine:
            self.status_bar.showMessage("TTS движок не загружен")
            QMessageBox.warning(self, "Ошибка", "TTS движок не загружен")
            self.tts_controls.enable_buttons()
            return

        text = self.text_editor.get_text()
        if not text or not text.strip():
            self.status_bar.showMessage("Введите текст для сохранения")
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите текст для сохранения")
            self.tts_controls.enable_buttons()
            return

        self.logger.info(f"Сохранение текста: {text[:100]}...")
        self.status_bar.showMessage("Синтез для сохранения...")
        speed = self.tts_controls.get_speed()

        def synthesize_and_save():
            try:
                audio = self.tts_engine.synthesize(text, speed)

                if audio is not None:
                    filename = f"FreeTalk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    download_dir = os.path.expanduser("~/Downloads/FreeTalk")
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
                self.tts_controls.enable_buttons()

        thread = threading.Thread(target=synthesize_and_save, daemon=True)
        thread.start()

    def load_settings(self):
        """Загрузка сохраненных настроек"""
        settings = QSettings("FreeTalk", "App")

        last_voice = settings.value("last_voice", self.config.available_voices[0])
        if isinstance(last_voice, str):
            self.tts_controls.set_current_voice(last_voice)
            self.on_voice_changed(last_voice)

        zoom = settings.value("zoom", self.config.default_zoom, type=int)
        self.zoom_slider.set_value(zoom)
        self.on_zoom_changed(zoom)

        t9_enabled = settings.value("t9_enabled", False, type=bool)
        if t9_enabled and self.t9_widget:
            self.t9_widget.enable()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш - предотвращаем аварийное закрытие"""
        event.ignore()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self, 'Выход',
            'Вы уверены, что хотите выйти из Free Talk?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            settings = QSettings("FreeTalk", "App")
            settings.setValue("last_voice", self.tts_controls.get_current_voice())
            settings.setValue("zoom", self.zoom_slider.get_value())
            settings.setValue("t9_enabled", self.t9_widget.is_enabled() if self.t9_widget else False)

            self.logger.info("Приложение Free Talk закрыто")
            event.accept()
        else:
            event.ignore()