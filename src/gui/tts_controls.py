# src/gui/tts_controls.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton,
    QLabel, QSlider, QVBoxLayout, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class TTSControls(QWidget):
    voice_changed = pyqtSignal(str)
    speed_changed = pyqtSignal(float)
    speak_requested = pyqtSignal()
    download_requested = pyqtSignal()

    def __init__(self, config, on_voice_changed=None):
        super().__init__()
        self.config = config

        if on_voice_changed:
            self.voice_changed.connect(on_voice_changed)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # Группа выбора голоса
        voice_group = QGroupBox("Голос")
        voice_layout = QVBoxLayout(voice_group)

        self.voice_combo = QComboBox()
        for voice in self.config.available_voices:
            display_name = f"Голос {voice}_ru"
            self.voice_combo.addItem(display_name, voice)

        self.voice_combo.currentIndexChanged.connect(self.on_voice_selected)
        voice_layout.addWidget(self.voice_combo)
        layout.addWidget(voice_group)

        # Группа настройки скорости
        speed_group = QGroupBox("Скорость")
        speed_layout = QVBoxLayout(speed_group)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)  # 50% = 0.5
        self.speed_slider.setMaximum(150)  # 150% = 1.5
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("100%")
        self.speed_label.setAlignment(Qt.AlignCenter)
        speed_layout.addWidget(self.speed_label)
        layout.addWidget(speed_group)

        # Кнопки
        buttons_layout = QVBoxLayout()

        self.speak_btn = QPushButton("Озвучить")
        self.speak_btn.setFixedSize(200, 110)
        self.speak_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.speak_btn.clicked.connect(self.on_speak_clicked)
        buttons_layout.addWidget(self.speak_btn)

        self.download_btn = QPushButton("Скачать")
        self.download_btn.setFixedSize(200, 110)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.download_btn.clicked.connect(self.on_download_clicked)
        buttons_layout.addWidget(self.download_btn)

        layout.addLayout(buttons_layout)
        layout.addStretch()

    def on_speak_clicked(self):
        """Обработчик кнопки Озвучить"""
        self.speak_btn.setEnabled(False)
        self.speak_btn.setText("Синтез...")
        self.speak_requested.emit()

    def on_download_clicked(self):
        """Обработчик кнопки Скачать"""
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Сохранение...")
        self.download_requested.emit()

    def enable_buttons(self):
        """Включение кнопок"""
        self.speak_btn.setEnabled(True)
        self.speak_btn.setText("Озвучить")
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Скачать")

    def on_voice_selected(self, index):
        voice = self.voice_combo.itemData(index)
        self.voice_changed.emit(voice)

    def on_speed_changed(self, value):
        speed = value / 100.0
        self.speed_label.setText(f"{value}%")
        self.speed_changed.emit(speed)

    def set_current_voice(self, voice_name):
        index = self.voice_combo.findData(voice_name)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)

    def get_current_voice(self):
        return self.voice_combo.currentData()

    def get_speed(self):
        return self.speed_slider.value() / 100.0

    def enable_buttons(self):
        """Включение кнопок после завершения операции"""
        self.speak_btn.setEnabled(True)
        self.speak_btn.setText("Озвучить")
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Скачать")