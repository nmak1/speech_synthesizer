# src/gui/styles.py
MAIN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
}

QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #d0d0d0;
    border-color: #9e9e9e;
}

QPushButton:pressed {
    background-color: #c0c0c0;
}

QPushButton:checked {
    background-color: #4caf50;
    color: white;
    border-color: #388e3c;
}

QComboBox {
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 5px;
    min-width: 100px;
    background-color: white;
}

QComboBox:hover {
    border-color: #9e9e9e;
}

QComboBox::drop-down {
    border: none;
}

QTextEdit {
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    background-color: white;
    selection-background-color: #b3d4fc;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QTextEdit:focus {
    border-color: #4caf50;
    outline: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #4caf50;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #388e3c;
}

QSlider::sub-page:horizontal {
    background: #4caf50;
    border-radius: 3px;
}

QStatusBar {
    background-color: #e0e0e0;
    color: #666;
    padding: 2px;
}

QMenuBar {
    background-color: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
}

QMenuBar::item {
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: white;
    border: 1px solid #bdbdbd;
}

QMenu::item:selected {
    background-color: #b3d4fc;
}

QScrollBar:vertical {
    border: none;
    background: #f5f5f5;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #c1c1c1;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #f5f5f5;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #c1c1c1;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

QToolTip {
    background-color: #333;
    color: white;
    border: none;
    padding: 5px;
    border-radius: 3px;
}
"""