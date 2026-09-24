# src/gui/tts_controls.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QSlider, QLabel, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class TTSControls(QWidget):
    """Виджет управления TTS (Пункт 4 — крупные элементы)."""

    speak_requested = pyqtSignal()
    download_requested = pyqtSignal()

    # --- Размеры (увеличены под требования Пункта 4) ---
    BTN_H = 64            # было 40
    BTN_MIN_W = 200       # было 120
    BTN_FONT = 20         # было 14
    LABEL_FONT = 18       # было ~12
    COMBO_MIN_H = 52
    COMBO_MIN_W = 220
    SLIDER_MIN_W = 240
    SLIDER_H = 48
    SPACING = 16          # было 8

    def __init__(self, config, on_voice_changed=None):
        super().__init__()
        self.config = config
        self.on_voice_changed = on_voice_changed
        self.current_voice = getattr(config, "default_voice", "aidar") or "aidar"
        self.current_speed = 1.0

        if not getattr(self.config, "available_voices", None):
            self.config.available_voices = ["aidar", "baya", "kseniya", "xenia", "random"]

        self.init_ui()

    # ---------- UI ----------

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.SPACING)

        group = QGroupBox("Управление голосом")
        group.setStyleSheet(self._groupbox_style())
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(20, 28, 20, 20)
        group_layout.setSpacing(self.SPACING)

        # Верхняя строка: голос и скорость
        top_row = QHBoxLayout()
        top_row.setSpacing(self.SPACING)

        voice_label = QLabel("Голос:")
        voice_label.setFont(QFont("Segoe UI", self.LABEL_FONT, QFont.Bold))
        voice_label.setMinimumWidth(90)          # было setFixedWidth(40)
        top_row.addWidget(voice_label)

        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.config.available_voices)
        self.voice_combo.setCurrentText(self.current_voice)
        self.voice_combo.setMinimumHeight(self.COMBO_MIN_H)
        self.voice_combo.setMinimumWidth(self.COMBO_MIN_W)
        self.voice_combo.setFont(QFont("Segoe UI", self.LABEL_FONT))
        self.voice_combo.setStyleSheet(self._combo_style())
        self.voice_combo.currentTextChanged.connect(self.on_voice_selected)
        top_row.addWidget(self.voice_combo, 1)

        speed_label = QLabel("Скорость:")
        speed_label.setFont(QFont("Segoe UI", self.LABEL_FONT, QFont.Bold))
        speed_label.setMinimumWidth(120)         # было setFixedWidth(60)
        top_row.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.setMinimumWidth(self.SLIDER_MIN_W)
        self.speed_slider.setFixedHeight(self.SLIDER_H)
        self.speed_slider.setStyleSheet(self._slider_style())
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        top_row.addWidget(self.speed_slider, 2)

        self.speed_label = QLabel("1.0x")
        self.speed_label.setFont(QFont("Segoe UI", self.LABEL_FONT, QFont.Bold))
        self.speed_label.setMinimumWidth(80)     # было setFixedWidth(40)
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet(
            "QLabel { color: #333; background: #f5f5f5; "
            "border: 1px solid #ddd; border-radius: 6px; padding: 6px; }"
        )
        top_row.addWidget(self.speed_label)

        group_layout.addLayout(top_row)

        # Нижняя строка: кнопки
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(self.SPACING)
        bottom_row.addStretch()

        self.speak_btn = QPushButton("▶  Озвучить")
        self.speak_btn.setMinimumHeight(self.BTN_H)
        self.speak_btn.setMinimumWidth(self.BTN_MIN_W)
        self.speak_btn.setFont(QFont("Segoe UI", self.BTN_FONT, QFont.Bold))
        self.speak_btn.setCursor(Qt.PointingHandCursor)
        self.speak_btn.setStyleSheet(self._btn_style(
            bg="#4CAF50", hover="#45a049", pressed="#3d8b40"
        ))
        self.speak_btn.clicked.connect(self.speak_requested.emit)
        bottom_row.addWidget(self.speak_btn)

        self.download_btn = QPushButton("💾  Скачать")
        self.download_btn.setMinimumHeight(self.BTN_H)
        self.download_btn.setMinimumWidth(self.BTN_MIN_W)
        self.download_btn.setFont(QFont("Segoe UI", self.BTN_FONT, QFont.Bold))
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setStyleSheet(self._btn_style(
            bg="#2196F3", hover="#1976D2", pressed="#1565C0"
        ))
        self.download_btn.clicked.connect(self.download_requested.emit)
        bottom_row.addWidget(self.download_btn)

        bottom_row.addStretch()
        group_layout.addLayout(bottom_row)

        layout.addWidget(group)

    # ---------- Стили ----------

    def _btn_style(self, bg, hover, pressed):
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
            }}
            QPushButton:hover  {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """

    def _combo_style(self):
        return """
            QComboBox {
                background: white;
                border: 2px solid #bdbdbd;
                border-radius: 8px;
                padding: 8px 12px;
                color: #333;
            }
            QComboBox:hover { border-color: #9e9e9e; }
            QComboBox:focus { border-color: #4CAF50; }
            QComboBox::drop-down { border: none; width: 32px; }
            QComboBox QAbstractItemView {
                font-size: 18px;
                padding: 6px;
                selection-background-color: #bbdefb;
                selection-color: #000;
            }
        """

    def _slider_style(self):
        return """
            QSlider::groove:horizontal {
                height: 14px;
                background: #e0e0e0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 7px;
            }
            QSlider::add-page:horizontal {
                background: #e0e0e0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 3px solid white;
                width: 32px;
                height: 32px;
                margin: -12px 0;
                border-radius: 18px;
            }
            QSlider::handle:horizontal:hover  { background: #1976D2; }
            QSlider::handle:horizontal:pressed { background: #1565C0; }
        """

    def _groupbox_style(self):
        return """
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 14px;
                background: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                color: #333;
            }
        """

    # ---------- Логика ----------

    def on_voice_selected(self, voice: str):
        self.current_voice = voice
        if self.on_voice_changed:
            self.on_voice_changed(voice)

    def on_speed_changed(self, value: int):
        self.current_speed = value / 100.0
        self.speed_label.setText(f"{self.current_speed:.1f}x")

    def get_speed(self) -> float:
        return self.current_speed

    def get_current_voice(self) -> str:
        return self.current_voice

    def set_current_voice(self, voice: str):
        if voice in self.config.available_voices:
            self.current_voice = voice
            idx = self.voice_combo.findText(voice)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)

    def enable_buttons(self):
        self.speak_btn.setEnabled(True)
        self.download_btn.setEnabled(True)

    def disable_buttons(self):
        self.speak_btn.setEnabled(False)
        self.download_btn.setEnabled(False)