# src/gui/t9_widget.py
"""
Виджет для отображения предсказаний T9
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFrame,
    QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QColor


class T9Widget(QWidget):
    """Виджет для отображения предсказаний T9"""

    word_selected = pyqtSignal(str)

    def __init__(self, config, on_word_selected=None):
        super().__init__()
        self.config = config
        self.enabled = config.t9_enabled
        self.suggestions = []

        if on_word_selected:
            self.word_selected.connect(on_word_selected)

        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Кнопка Toggle для включения/выключения T9
        self.toggle_btn = QPushButton("T9")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self.enabled)
        self.toggle_btn.setFixedSize(60, 50)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                border-color: #45a049;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_t9)
        layout.addWidget(self.toggle_btn)

        # Контейнер для кнопок предсказаний
        self.suggestions_container = QWidget()
        self.suggestions_layout = QHBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(10)

        # Создаем 5 кнопок для предсказаний
        self.suggestion_buttons = []
        for i in range(5):
            btn = QPushButton("")
            btn.setFixedSize(120, 50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 2px solid #2196F3;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #bbdef5;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.on_button_clicked(idx))
            self.suggestion_buttons.append(btn)
            self.suggestions_layout.addWidget(btn)

        self.suggestions_layout.addStretch()

        self.suggestions_container.setVisible(self.enabled)
        layout.addWidget(self.suggestions_container)
        layout.addStretch()

    def toggle_t9(self, checked: bool):
        """Включение/выключение T9"""
        self.enabled = checked
        self.suggestions_container.setVisible(checked)

        if not checked:
            self.update_suggestions([])

    def update_suggestions(self, suggestions: list):
        """Обновление списка предсказаний"""
        self.suggestions = suggestions[:5]

        # Логируем для отладки
        from src.utils.logger import get_logger
        logger = get_logger()
        logger.debug(f"T9 Widget обновлен: {self.suggestions}")

        for i, btn in enumerate(self.suggestion_buttons):
            if i < len(self.suggestions):
                btn.setText(self.suggestions[i])
                btn.setEnabled(True)
                btn.setVisible(True)
            else:
                btn.setText("")
                btn.setEnabled(False)
                btn.setVisible(False)

    def on_button_clicked(self, index: int):
        """Обработчик нажатия на кнопку предсказания"""
        if index < len(self.suggestions):
            selected_word = self.suggestions[index]
            self.word_selected.emit(selected_word)
            # Очищаем предсказания после выбора
            self.update_suggestions([])

    def is_enabled(self) -> bool:
        """Возвращает состояние T9"""
        return self.enabled

    def enable(self):
        """Включить T9"""
        self.toggle_btn.setChecked(True)
        self.toggle_t9(True)

    def disable(self):
        """Выключить T9"""
        self.toggle_btn.setChecked(False)
        self.toggle_t9(False)