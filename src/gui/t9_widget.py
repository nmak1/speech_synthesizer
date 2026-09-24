# src/gui/t9_widget.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal


class T9Widget(QWidget):
    word_selected = pyqtSignal(str)
    punctuation_selected = pyqtSignal(str)

    # Размеры (Пункт 4)
    TOGGLE_W, TOGGLE_H = 70, 50
    PUNCT_W, PUNCT_H = 55, 50
    SUGG_W, SUGG_H = 160, 50
    SPACING = 8

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
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(self.SPACING)

        # --- Верхняя строка: T9 + пунктуация ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(self.SPACING)

        # Кнопка T9
        self.toggle_btn = QPushButton("T9")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self.enabled)
        self.toggle_btn.setFixedSize(self.TOGGLE_W, self.TOGGLE_H)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                color: #333;
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

        # Кнопки пунктуации
        punctuation_btns = [",", ".", "!", "?", "...", ";", ":", "(", ")"]
        for punc in punctuation_btns:
            btn = QPushButton(punc)
            btn.setFixedSize(self.PUNCT_W, self.PUNCT_H)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #bdbdbd;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
            """)
            btn.clicked.connect(lambda checked, p=punc: self.on_punctuation_clicked(p))
            top_layout.addWidget(btn)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # --- Контейнер предсказаний ---
        self.suggestions_container = QWidget()
        self.suggestions_layout = QHBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(self.SPACING)

        self.suggestion_buttons = []
        for i in range(5):
            btn = QPushButton("")
            btn.setFixedSize(self.SUGG_W, self.SUGG_H)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 2px solid #2196F3;
                    border-radius: 6px;
                    font-size: 16px;
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

        # Скрываем, пока нет предсказаний
        self.suggestions_container.setVisible(False)
        main_layout.addWidget(self.suggestions_container)

    # ---------- Логика ----------

    def on_punctuation_clicked(self, punctuation: str):
        """Вставляем знак препинания."""
        self.word_selected.emit(punctuation)

    def toggle_t9(self, checked):
        self.enabled = checked
        if not checked:
            self.update_suggestions([])
        else:
            # Если включили и есть сохранённые — показать снова
            self.suggestions_container.setVisible(len(self.suggestions) > 0)

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

        # Показываем контейнер, только если есть что показать и T9 включён
        has_any = self.enabled and len(self.suggestions) > 0
        self.suggestions_container.setVisible(has_any)

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