# src/gui/text_editor.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QToolBar,
    QFontComboBox, QComboBox, QPushButton, QColorDialog,
    QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor


class TextEditor(QWidget):
    text_changed = pyqtSignal()

    def __init__(self, config, on_text_changed=None):
        super().__init__()
        self.config = config
        if on_text_changed:
            self.text_changed.connect(on_text_changed)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Панель инструментов форматирования
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(5)

        # Выбор шрифта
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.change_font)
        toolbar_layout.addWidget(self.font_combo)

        # Выбор размера
        self.font_size_combo = QComboBox()
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 48, 72]:
            self.font_size_combo.addItem(str(size))
        self.font_size_combo.setCurrentText(str(self.config.default_font_size))
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        toolbar_layout.addWidget(self.font_size_combo)

        # Кнопка жирного начертания
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(30, 30)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.bold_btn.clicked.connect(self.toggle_bold)
        toolbar_layout.addWidget(self.bold_btn)

        # Кнопка выбора цвета
        self.color_btn = QPushButton("🎨")
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.clicked.connect(self.choose_color)
        toolbar_layout.addWidget(self.color_btn)

        # Предустановленные цвета
        colors = ["#000000", "#FF0000", "#FFFF00", "#00FF00", "#0000FF", "#FF00FF"]
        for color in colors:
            color_btn = QPushButton()
            color_btn.setFixedSize(25, 25)
            color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
            color_btn.clicked.connect(lambda checked, c=color: self.set_text_color(c))
            toolbar_layout.addWidget(color_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        # Текстовое поле
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)

        # Установка начальных параметров
        self.set_font(self.config.default_font, self.config.default_font_size)

    def get_current_format(self):
        """Получение текущего формата текста"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            return cursor.charFormat()
        else:
            return self.text_edit.currentCharFormat()

    def change_font(self, font):
        """Изменение шрифта для выделенного текста или текущей позиции"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Применяем к выделенному тексту
            format = QTextCharFormat()
            format.setFont(font)
            cursor.mergeCharFormat(format)
        else:
            # Применяем для будущего текста
            self.text_edit.setCurrentFont(font)
        self.text_edit.setFocus()

    def change_font_size(self, size_str):
        """Изменение размера шрифта для выделенного текста"""
        try:
            size = int(size_str)
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                # Применяем к выделенному тексту
                format = QTextCharFormat()
                format.setFontPointSize(size)
                cursor.mergeCharFormat(format)
            else:
                # Применяем для будущего текста
                self.text_edit.setFontPointSize(size)
            self.text_edit.setFocus()
        except:
            pass

    def set_font(self, font_name, font_size):
        """Установка шрифта для всего текста"""
        self.text_edit.selectAll()
        font = QFont(font_name, font_size)
        self.text_edit.setCurrentFont(font)
        self.text_edit.setFontPointSize(font_size)
        cursor = self.text_edit.textCursor()
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)

    def toggle_bold(self):
        """Переключение жирного начертания для выделенного текста"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Применяем к выделенному тексту
            format = QTextCharFormat()
            format.setFontWeight(QFont.Bold if self.bold_btn.isChecked() else QFont.Normal)
            cursor.mergeCharFormat(format)
        else:
            # Применяем для будущего текста
            fmt = self.text_edit.currentCharFormat()
            fmt.setFontWeight(QFont.Bold if self.bold_btn.isChecked() else QFont.Normal)
            self.text_edit.setCurrentCharFormat(fmt)
        self.text_edit.setFocus()

    def choose_color(self):
        """Выбор цвета текста"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_text_color(color.name())

    def set_text_color(self, color_hex):
        """Установка цвета текста для выделенного фрагмента"""
        cursor = self.text_edit.textCursor()
        format = QTextCharFormat()
        format.setForeground(QColor(color_hex))

        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            self.text_edit.setCurrentCharFormat(format)
        self.text_edit.setFocus()

    def on_text_changed(self):
        self.text_changed.emit()

    def get_text(self):
        return self.text_edit.toPlainText()

    def set_text(self, text):
        self.text_edit.setPlainText(text)

    def set_zoom(self, zoom_value):
        """Установка масштаба текста"""
        base_size = self.config.default_font_size
        new_size = max(6, min(72, base_size * zoom_value / 100))
        self.text_edit.setFontPointSize(new_size)