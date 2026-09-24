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
    padding: 6px 12px;
    font-size: 14px;              /* было 12px */
}

QPushButton:hover   { background-color: #d0d0d0; border-color: #9e9e9e; }
QPushButton:pressed { background-color: #c0c0c0; }
QPushButton:checked { background-color: #4caf50; color: white; border-color: #388e3c; }

QComboBox {
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 6px 10px;            /* было 5px */
    min-width: 100px;
    background-color: white;
    font-size: 16px;              /* добавили */
}
QComboBox:hover { border-color: #9e9e9e; }
QComboBox::drop-down { border: none; }

QGroupBox {
    font-size: 16px;              /* добавили */
    font-weight: bold;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #333;
}

QTextEdit {
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    background-color: white;
    selection-background-color: #b3d4fc;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QTextEdit:focus { border-color: #4caf50; outline: none; }

QSlider::groove:horizontal { height: 8px; background: #e0e0e0; border-radius: 4px; }
QSlider::handle:horizontal {
    background: #4caf50;
    width: 20px; height: 20px;    /* было 14×14 */
    margin: -6px 0;
    border-radius: 10px;
}
QSlider::handle:horizontal:hover { background: #388e3c; }
QSlider::sub-page:horizontal { background: #4caf50; border-radius: 4px; }

QStatusBar { background-color: #e0e0e0; color: #666; padding: 2px; }

QMenuBar { background-color: #f5f5f5; border-bottom: 1px solid #e0e0e0; }
QMenuBar::item { padding: 5px 10px; }
QMenuBar::item:selected { background-color: #e0e0e0; }

QMenu { background-color: white; border: 1px solid #bdbdbd; }
QMenu::item:selected { background-color: #b3d4fc; }

QScrollBar:vertical   { border: none; background: #f5f5f5; width: 14px; margin: 0; }
QScrollBar::handle:vertical {
    background: #c1c1c1; border-radius: 7px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #a8a8a8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }

QScrollBar:horizontal   { border: none; background: #f5f5f5; height: 14px; margin: 0; }
QScrollBar::handle:horizontal {
    background: #c1c1c1; border-radius: 7px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #a8a8a8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background: none; }

QToolTip {
    background-color: #333; color: white;
    border: none; padding: 5px; border-radius: 3px;
    font-size: 14px;
}
"""