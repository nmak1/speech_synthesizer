# src/gui/zoom_slider.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSlider, QLabel, QPushButton, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


class ZoomSlider(QWidget):
    """
    Виджет управления масштабом.
    - Крупные кнопки +/- (для айтрекера)
    - Широкий слайдер с увеличенным ползунком
    - Debounce: zoom_changed шлётся не чаще, чем раз в 50 мс
    - zoom_finished: шлётся при отпускании слайдера / клике по кнопке
    """

    zoom_changed = pyqtSignal(int)
    zoom_finished = pyqtSignal()

    # Размеры — увеличены под требования (Пункт 3)
    BTN_SIZE = 60          # было 30
    RESET_BTN_W = 90       # было 60
    RESET_BTN_H = 60       # было 30
    SLIDER_W = 320         # было 200
    SLIDER_H = 48          # высота слайдера
    SPACING = 16           # было 10

    def __init__(self, default_zoom, min_zoom, max_zoom, on_zoom_changed=None):
        super().__init__()
        self.default_zoom = default_zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.current_zoom = default_zoom
        self._update_timer: QTimer = None
        self._is_updating = False

        if on_zoom_changed:
            self.zoom_changed.connect(on_zoom_changed)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(self.SPACING)

        # Кнопка "Сбросить 100%"
        self.reset_btn = QPushButton("100%")
        self.reset_btn.setFixedSize(self.RESET_BTN_W, self.RESET_BTN_H)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(self._btn_style("#607D8B", "#455A64", "#37474F"))
        self.reset_btn.clicked.connect(self.reset_zoom)
        layout.addWidget(self.reset_btn)

        # Кнопка "-"
        self.minus_btn = QPushButton("−")  # U+2212, визуально ровнее
        self.minus_btn.setFixedSize(self.BTN_SIZE, self.BTN_SIZE)
        self.minus_btn.setCursor(Qt.PointingHandCursor)
        self.minus_btn.setStyleSheet(self._btn_style("#2196F3", "#1976D2", "#1565C0"))
        self.minus_btn.clicked.connect(self.zoom_out)
        layout.addWidget(self.minus_btn)

        # Слайдер — крупный
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.min_zoom)
        self.slider.setMaximum(self.max_zoom)
        self.slider.setValue(self.current_zoom)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.setFixedSize(self.SLIDER_W, self.SLIDER_H)
        self.slider.setStyleSheet(self._slider_style())
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)
        layout.addWidget(self.slider)

        # Кнопка "+"
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(self.BTN_SIZE, self.BTN_SIZE)
        self.plus_btn.setCursor(Qt.PointingHandCursor)
        self.plus_btn.setStyleSheet(self._btn_style("#2196F3", "#1976D2", "#1565C0"))
        self.plus_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.plus_btn)

        # Метка значения — крупная
        self.value_label = QLabel(f"{self.current_zoom}%")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(80, self.BTN_SIZE)
        f = QFont("Segoe UI", 14, QFont.Bold)
        self.value_label.setFont(f)
        self.value_label.setStyleSheet(
            "QLabel { color: #333; background: #f5f5f5; "
            "border: 1px solid #ddd; border-radius: 6px; }"
        )
        layout.addWidget(self.value_label)

    # ---------- Стили ----------

    def _btn_style(self, bg, hover, pressed):
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 22px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
            QPushButton:disabled {{ background-color: #cccccc; }}
        """

    def _slider_style(self):
        # Увеличенный ползунок — важно для айтрекера
        return """
            QSlider::groove:horizontal {
                height: 12px;
                background: #e0e0e0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 6px;
            }
            QSlider::add-page:horizontal {
                background: #e0e0e0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 3px solid white;
                width: 32px;
                height: 32px;
                margin: -14px 0;
                border-radius: 18px;
            }
            QSlider::handle:horizontal:hover {
                background: #1976D2;
            }
            QSlider::handle:horizontal:pressed {
                background: #1565C0;
            }
        """

    # ---------- Обработчики ----------

    def on_slider_moved(self, value):
        self.current_zoom = value
        self.value_label.setText(f"{value}%")

        if self._update_timer:
            self._update_timer.stop()
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(lambda: self._emit_zoom_changed(value))
        self._update_timer.start(60)

    def on_slider_released(self):
        if self._update_timer:
            self._update_timer.stop()
        self._emit_zoom_changed(self.current_zoom)
        self.zoom_finished.emit()

    def _emit_zoom_changed(self, value):
        if not self._is_updating:
            self._is_updating = True
            try:
                self.zoom_changed.emit(value)
            finally:
                self._is_updating = False

    def reset_zoom(self):
        self._is_updating = True
        try:
            self.slider.setValue(self.default_zoom)
            self.current_zoom = self.default_zoom
            self.value_label.setText(f"{self.default_zoom}%")
        finally:
            self._is_updating = False
        self._emit_zoom_changed(self.default_zoom)
        self.zoom_finished.emit()

    def zoom_in(self):
        new_value = min(self.current_zoom + 10, self.max_zoom)
        self.slider.setValue(new_value)
        self.current_zoom = new_value
        self.value_label.setText(f"{new_value}%")
        self._emit_zoom_changed(new_value)
        self.zoom_finished.emit()

    def zoom_out(self):
        new_value = max(self.current_zoom - 10, self.min_zoom)
        self.slider.setValue(new_value)
        self.current_zoom = new_value
        self.value_label.setText(f"{new_value}%")
        self._emit_zoom_changed(new_value)
        self.zoom_finished.emit()

    def set_value(self, value):
        if not self._is_updating:
            self._is_updating = True
            try:
                self.slider.setValue(value)
                self.current_zoom = value
                self.value_label.setText(f"{value}%")
            finally:
                self._is_updating = False

    def get_value(self):
        return self.current_zoom