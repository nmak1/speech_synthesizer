# main.py - исправленная версия с поддержкой иконок
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

    # Устанавливаем имя приложения
    app.setApplicationName("FreeTalk")
    app.setOrganizationName("FreeTalk")

    # Создаем иконку с несколькими размерами для лучшего отображения
    icon = QIcon()

    # Пути к иконкам (поиск в разных местах)
    icon_paths = [
        # Основные пути
        "logo.ico",
        "logo.png",
        "logo_big.png",
        # Пути из папки imeg
        "imeg/logo.ico",
        "imeg/logo.png",
        "imeg/logo_big.png",
        "imeg/logo_highres.png",
        # Пути из installers (для скомпилированной версии)
        os.path.join(os.path.dirname(sys.executable), "logo.ico"),
        os.path.join(os.path.dirname(sys.executable), "logo.png"),
    ]

    icon_found = False
    for path in icon_paths:
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Добавляем разные размеры иконки
                for size in [16, 32, 48, 64, 128, 256]:
                    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon.addPixmap(scaled)
                icon_found = True
                print(f"[OK] Иконка загружена: {path}")
                break

    if icon_found:
        app.setWindowIcon(icon)
    else:
        print("[WARN] Иконка не найдена, используется стандартная")

    # Создаем временный QWidget для установки иконки через стиль (Windows)
    try:
        import ctypes
        # Устанавливаем иконку для окна через Windows API (более надежно)
        myappid = 'freetalk.synthesizer.version1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    from src.utils.logger import setup_logger
    from src.utils.config_manager import ConfigManager
    from src.gui.main_window import MainWindow

    logger = setup_logger()
    logger.info("Запуск приложения 'Free Talk'")

    config_manager = ConfigManager()
    config = config_manager.load_config()
    config.app_name = "Free Talk"

    window = MainWindow(config_manager, config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()