# src/gui/t9_widget.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal


class T9Widget(QWidget):
    word_selected = pyqtSignal(str)
    punctuation_selected = pyqtSignal(str)  # Новый сигнал для знаков препинания

    def __init__(self, config, on_word_selected=None):
        super().__init__()
        self.config = config
        self.enabled = config.t9_enabled
        self.suggestions = []

        if on_word_selected:
            self.word_selected.connect(on_word_selected)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Верхняя панель с T9 и знаками препинания
        top_layout = QHBoxLayout()

        # Кнопка Toggle для включения/выключения T9
        self.toggle_btn = QPushButton("T9")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self.enabled)
        self.toggle_btn.setFixedSize(60, 40)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 5px;
                font-size: 14px;
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
        top_layout.addWidget(self.toggle_btn)

        # Кнопки знаков препинания
        punctuation_btns = [",", ".", "!", "?", "...", ";", ":", "(", ")"]
        for punc in punctuation_btns:
            btn = QPushButton(punc)
            btn.setFixedSize(45, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #bdbdbd;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(lambda checked, p=punc: self.on_punctuation_clicked(p))
            top_layout.addWidget(btn)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Контейнер для кнопок предсказаний
        self.suggestions_container = QWidget()
        self.suggestions_layout = QHBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(10)

        # Создаем 5 кнопок для предсказаний
        self.suggestion_buttons = []
        for i in range(5):
            btn = QPushButton("")
            btn.setFixedSize(130, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 2px solid #2196F3;
                    border-radius: 5px;
                    font-size: 12px;
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
        main_layout.addWidget(self.suggestions_container)

    def on_punctuation_clicked(self, punctuation: str):
        """Обработчик нажатия на знак препинания - просто вставляем символ"""
        self.word_selected.emit(punctuation)

    def toggle_t9(self, checked):
        self.enabled = checked
        self.suggestions_container.setVisible(checked)

        if not checked:
            self.update_suggestions([])

    def update_suggestions(self, suggestions):
        self.suggestions = suggestions[:5]

        for i, btn in enumerate(self.suggestion_buttons):
            if i < len(self.suggestions):
                word = self.suggestions[i]
                if len(word) > 15:
                    word = word[:12] + "..."
                btn.setText(word)
                btn.setEnabled(True)
                btn.setVisible(True)
                btn.setToolTip(self.suggestions[i])
            else:
                btn.setText("")
                btn.setEnabled(False)
                btn.setVisible(False)

    def on_button_clicked(self, index):
        if index < len(self.suggestions):
            self.word_selected.emit(self.suggestions[index])

    def is_enabled(self):
        return self.enabled

    def enable(self):
        self.toggle_btn.setChecked(True)
        self.toggle_t9(True)

    def disable(self):
        self.toggle_btn.setChecked(False)
        self.toggle_t9(False)