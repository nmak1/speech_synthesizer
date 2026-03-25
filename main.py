# main.py
"""
Точка входа в приложение "Голосовой синтезатор"
"""
import sys
import os

# Добавляем путь к src в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.utils.config_manager import ConfigManager


def main():
    """Главная функция запуска приложения"""
    # Инициализируем логгер
    logger = setup_logger()
    logger.info("Запуск приложения 'Голосовой синтезатор'")

    # Настройки High DPI должны быть установлены ДО создания QApplication
    # Для PyQt5 используем这种方式
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Создаем приложение PyQt
    app = QApplication(sys.argv)

    # Загружаем конфигурацию
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Создаем и показываем главное окно
    window = MainWindow(config_manager, config)
    window.show()

    # Запускаем цикл событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()