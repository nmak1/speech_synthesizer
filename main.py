# main.py - обновленная версия для работы с PNG
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap


def main():
    # Настройки High DPI
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Установка иконки приложения (поддерживает PNG)
    if os.path.exists("logo.png"):
        icon = QIcon()
        icon.addPixmap(QPixmap("logo.png"))
        app.setWindowIcon(icon)
        print("✓ Логотип загружен: logo.png")
    elif os.path.exists("logo.ico"):
        app.setWindowIcon(QIcon("logo.ico"))
        print("✓ Логотип загружен: logo.ico")
    else:
        print("⚠ Логотип не найден, используется стандартная иконка")

    from src.utils.logger import setup_logger
    from src.utils.config_manager import ConfigManager
    from src.gui.main_window import MainWindow

    logger = setup_logger()
    logger.info("Запуск приложения 'Free Talk'")

    config_manager = ConfigManager()
    config = config_manager.load_config()
    config.app_name = "Free Talk"

    window = MainWindow(config_manager, config)
    window.setWindowTitle("Free Talk - Голосовой синтезатор")
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()