# src/gui/zoom_slider.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSlider, QLabel, QPushButton, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer


class ZoomSlider(QWidget):
    zoom_changed = pyqtSignal(int)

    # Добавляем сигнал для отслеживания завершения изменения масштаба
    zoom_finished = pyqtSignal()

    def __init__(self, default_zoom, min_zoom, max_zoom, on_zoom_changed=None):
        super().__init__()
        self.default_zoom = default_zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.current_zoom = default_zoom
        self._update_timer = None  # Таймер для debounce
        self._is_updating = False  # Флаг для предотвращения рекурсии

        if on_zoom_changed:
            self.zoom_changed.connect(on_zoom_changed)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Кнопка "Сбросить"
        self.reset_btn = QPushButton("100%")
        self.reset_btn.setFixedSize(60, 30)
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
        # Используем sliderMoved вместо valueChanged для лучшей производительности
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)
        layout.addWidget(self.slider)

        # Метка с текущим значением
        self.value_label = QLabel(f"{self.current_zoom}%")
        self.value_label.setFixedWidth(50)
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

    def on_slider_moved(self, value):
        """При перемещении слайдера - обновляем только интерфейс, без сигнала"""
        self.current_zoom = value
        self.value_label.setText(f"{value}%")

        # Используем debounce для отложенной отправки сигнала
        if self._update_timer:
            self._update_timer.stop()

        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(lambda: self._emit_zoom_changed(value))
        self._update_timer.start(50)  # Задержка 50мс

    def on_slider_released(self):
        """Когда пользователь отпустил слайдер - финальное обновление"""
        if self._update_timer:
            self._update_timer.stop()
        self._emit_zoom_changed(self.current_zoom)
        # Отправляем сигнал о завершении изменения масштаба
        self.zoom_finished.emit()

        # Принудительно обрабатываем события для восстановления интерфейса
        QApplication.processEvents()

    def _emit_zoom_changed(self, value):
        """Безопасная отправка сигнала изменения масштаба"""
        if not self._is_updating:
            self._is_updating = True
            try:
                self.zoom_changed.emit(value)
                # Принудительно обновляем интерфейс после изменения масштаба
                QApplication.processEvents()
            finally:
                self._is_updating = False

    def reset_zoom(self):
        self._is_updating = True
        self.slider.setValue(self.default_zoom)
        self.current_zoom = self.default_zoom
        self.value_label.setText(f"{self.default_zoom}%")
        self._emit_zoom_changed(self.default_zoom)
        self._is_updating = False
        self.zoom_finished.emit()
        QApplication.processEvents()

    def zoom_in(self):
        new_value = min(self.current_zoom + 10, self.max_zoom)
        self.slider.setValue(new_value)
        self.on_slider_released()

    def zoom_out(self):
        new_value = max(self.current_zoom - 10, self.min_zoom)
        self.slider.setValue(new_value)
        self.on_slider_released()

    def set_value(self, value):
        if not self._is_updating:
            self._is_updating = True
            self.slider.setValue(value)
            self.current_zoom = value
            self.value_label.setText(f"{value}%")
            self._is_updating = False

    def get_value(self):
        return self.current_zoom