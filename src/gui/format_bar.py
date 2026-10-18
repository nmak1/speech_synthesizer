# src/gui/format_bar.py
"""Панель форматирования текста: шрифты, размер, цвет, начертание.

Элементы крупные (интерфейс рассчитан на айтрекер):
кнопки >= 50 px по высоте, увеличенные шрифты.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, QColorDialog, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QGuiApplication

# Системные шрифты, гарантированно присутствующие в Windows / Linux / macOS
AVAILABLE_FONTS = [
    ("Segoe UI", "Segoe UI"),
    ("Arial", "Arial"),
    ("Tahoma", "Tahoma"),
    ("Verdana", "Verdana"),
    ("Trebuchet MS", "Trebuchet MS"),
    ("Times New Roman", "Times New Roman"),
    ("Georgia", "Georgia"),
    ("Comic Sans MS", "Comic Sans MS"),
    ("Courier New", "Courier New"),
    ("Calibri", "Calibri"),
]

PRESET_COLORS = [
    ("Чёрный", "#000000"),
    ("Красный", "#d32f2f"),
    ("Зелёный", "#2e7d32"),
    ("Синий", "#1565c0"),
    ("Оранжевый", "#ef6c00"),
    ("Фиолетовый", "#6a1b9a"),
    ("Бирюзовый", "#00838f"),
    ("Тёмно-серый", "#424242"),
]


class ColorButton(QPushButton):
    """Кнопка с превью текущего цвета; клик открывает диалог выбора."""

    color_picked = pyqtSignal(str)

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 50)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Выбрать цвет текста")
        self.clicked.connect(self.pick_color)
        self.set_color(color)

    def set_color(self, color: str):
        self._color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 3px solid #bdbdbd;
                border-radius: 8px;
            }}
            QPushButton:hover {{ border-color: #2196F3; }}
            QPushButton:pressed {{ border-color: #1976D2; }}
        """)

    def get_color(self) -> str:
        return self._color

    def pick_color(self):
        dlg = QColorDialog(QColor(self._color), self)
        dlg.setOption(QColorDialog.ShowAlphaChannel, False)
        dlg.setWindowTitle("Цвет текста")
        if dlg.exec_():
            self._color = dlg.currentColor().name()
            self.set_color(self._color)
            self.color_picked.emit(self._color)


class FormatBar(QWidget):
    """Панель формата текста."""

    font_changed = pyqtSignal(str)          # семейство шрифта
    size_changed = pyqtSignal(int)          # кегль
    color_changed = pyqtSignal(str)         # hex-цвет
    bold_toggled = pyqtSignal(bool)
    italic_toggled = pyqtSignal(bool)

    BTN_H = 50
    SPACING = 8

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._updating = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(self.SPACING)

        lbl_font = QLabel("Шрифт:")
        lbl_font.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_font)

        # --- Выбор семейства шрифта ---
        self.font_combo = QComboBox()
        for name, family in AVAILABLE_FONTS:
            self.font_combo.addItem(name, family)
        default_family = getattr(self.config, "default_font_family", "Segoe UI")
        idx = self.font_combo.findData(default_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        self.font_combo.setMinimumHeight(self.BTN_H)
        self.font_combo.setMinimumWidth(190)
        self.font_combo.setCursor(Qt.PointingHandCursor)
        self.font_combo.currentIndexChanged.connect(self._on_font_selected)
        layout.addWidget(self.font_combo)

        # --- Размер шрифта ---
        lbl_size = QLabel("Размер:")
        lbl_size.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_size)

        self.size_combo = QComboBox()
        base_sizes = [10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72]
        for s in base_sizes:
            self.size_combo.addItem(f"{s} px", s)
        self.size_combo.setMinimumHeight(self.BTN_H)
        self.size_combo.setMinimumWidth(90)
        self.size_combo.setCursor(Qt.PointingHandCursor)
        self.size_combo.currentIndexChanged.connect(self._on_size_selected)
        layout.addWidget(self.size_combo)

        # --- Жирный / Курсив ---
        self.bold_btn = QPushButton("Ж")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(self.BTN_H, self.BTN_H)
        self._style_toggle(self.bold_btn, underline=False)
        self.bold_btn.setToolTip("Полужирный")
        self.bold_btn.setCursor(Qt.PointingHandCursor)
        self.bold_btn.toggled.connect(lambda v: self._emit(self.bold_toggled, v))
        layout.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("К")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(self.BTN_H, self.BTN_H)
        self._style_toggle(self.italic_btn, underline=True)
        self.italic_btn.setToolTip("Курсив")
        self.italic_btn.setCursor(Qt.PointingHandCursor)
        self.italic_btn.toggled.connect(lambda v: self._emit(self.italic_toggled, v))
        layout.addWidget(self.italic_btn)

        # --- Цвет текста ---
        lbl_color = QLabel("Цвет:")
        lbl_color.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_color)

        default_color = getattr(self.config, "default_text_color", "#000000")
        self.color_btn = ColorButton(default_color)
        self.color_btn.color_picked.connect(lambda c: self._emit(self.color_changed, c))
        layout.addWidget(self.color_btn)

        # --- Быстрые цвета ---
        for name, hexc in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(36, self.BTN_H)
            btn.setToolTip(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hexc};
                    border: 2px solid #bdbdbd;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ border-color: #2196F3; }}
            """)
            btn.clicked.connect(lambda checked, c=hexc: self.set_color(c))
            layout.addWidget(btn)

        layout.addStretch()

    def _style_toggle(self, btn, underline=False):
        dec = " text-decoration: underline;" if underline else ""
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                {'font-style: italic;' if underline else ''}
                color: #333;{dec}
            }}
            QPushButton:checked {{
                background-color: #2196F3;
                color: white;
                border-color: #1976D2;
            }}
            QPushButton:hover {{ background-color: #e0e0e0; }}
        """)

    def _emit(self, signal, value):
        if self._updating:
            return
        signal.emit(value)

    # ---------- Слоты ----------

    def _on_font_selected(self, index):
        if not self._updating and index >= 0:
            self.font_changed.emit(self.font_combo.itemData(index))

    def _on_size_selected(self, index):
        if not self._updating and index >= 0:
            self.size_changed.emit(self.size_combo.itemData(index))

    # ---------- Публичный API ----------

    def set_color(self, color: str):
        self.color_btn.set_color(color)
        self.color_changed.emit(color)

    def sync_from_editor(self, family: str = None, size: int = None,
                        color: str = None, bold: bool = None, italic: bool = None):
        """Обновить виджеты панели без генерации сигналов (изменение выделением)."""
        self._updating = True
        try:
            if family:
                idx = self.font_combo.findData(family)
                if idx < 0:  # неизвестный системный шрифт — добавим
                    self.font_combo.addItem(family, family)
                    idx = self.font_combo.count() - 1
                self.font_combo.setCurrentIndex(idx)
            if size:
                idx = self.size_combo.findData(size)
                if idx < 0:
                    self.size_combo.addItem(f"{size} px", size)
                    self.size_combo.model().sort(0, Qt.AscendingOrder)
                    idx = self.size_combo.findData(size)
                self.size_combo.setCurrentIndex(idx)
            if color:
                self.color_btn.set_color(color)
            if bold is not None:
                self.bold_btn.setChecked(bold)
            if italic is not None:
                self.italic_btn.setChecked(italic)
        finally:
            self._updating = False
