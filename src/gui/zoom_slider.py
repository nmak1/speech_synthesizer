# src/gui/zoom_slider.py
"""
Виджет для масштабирования интерфейса
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSlider, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal


class ZoomSlider(QWidget):
    """Слайдер для изменения масштаба интерфейса"""

    zoom_changed = pyqtSignal(int)

    def __init__(self, default_zoom: int, min_zoom: int, max_zoom: int, on_zoom_changed=None):
        super().__init__()
        self.default_zoom = default_zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.current_zoom = default_zoom

        if on_zoom_changed:
            self.zoom_changed.connect(on_zoom_changed)

        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Кнопка "Сбросить"
        self.reset_btn = QPushButton("100%")
        self.reset_btn.setFixedSize(60, 30)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_zoom)
        layout.addWidget(self.reset_btn)

        # Слайдер
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.min_zoom)
        self.slider.setMaximum(self.max_zoom)
        self.slider.setValue(self.current_zoom)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.setFixedWidth(200)
        self.slider.valueChanged.connect(self.on_slider_changed)

        # Стилизация слайдера
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: black;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
                border: 1px solid #666;
            }
            QSlider::handle:horizontal:hover {
                background: #f0f0f0;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.slider)

        # Метка с текущим значением
        self.value_label = QLabel(f"{self.current_zoom}%")
        self.value_label.setFixedWidth(50)
        self.value_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #333;
            }
        """)
        layout.addWidget(self.value_label)

        # Кнопки увеличения/уменьшения
        self.minus_btn = QPushButton("-")
        self.minus_btn.setFixedSize(30, 30)
        self.minus_btn.clicked.connect(self.zoom_out)
        layout.addWidget(self.minus_btn)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(30, 30)
        self.plus_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.plus_btn)

    def on_slider_changed(self, value: int):
        """Обработчик изменения значения слайдера"""
        self.current_zoom = value
        self.value_label.setText(f"{value}%")
        self.zoom_changed.emit(value)

    def reset_zoom(self):
        """Сброс масштаба к значению по умолчанию"""
        self.slider.setValue(self.default_zoom)

    def zoom_in(self):
        """Увеличить масштаб"""
        new_value = min(self.current_zoom + 10, self.max_zoom)
        self.slider.setValue(new_value)

    def zoom_out(self):
        """Уменьшить масштаб"""
        new_value = max(self.current_zoom - 10, self.min_zoom)
        self.slider.setValue(new_value)

    def set_value(self, value: int):
        """Установить значение масштаба"""
        self.slider.setValue(value)

    def get_value(self) -> int:
        """Получить текущее значение масштаба"""
        return self.current_zoom