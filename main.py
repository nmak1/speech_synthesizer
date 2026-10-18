# main.py
import sys
import os

# Корень проекта в sys.path (для импорта пакета src как в dev, так и в frozen)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from src.paths import find_resource
from src.version import __version__, APP_USER_MODEL_ID


def main():
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("FreeTalk")
    app.setOrganizationName("FreeTalk")

    # Иконка — через единый резолвер ресурсов (src/paths.py)
    icon = QIcon()
    icon_path = find_resource("imeg/logo.ico", "logo.ico", "imeg/logo.png", "logo.png")
    if icon_path:
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            for size in [16, 32, 48, 64, 128, 256]:
                icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    if not icon.isNull():
        app.setWindowIcon(icon)

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass

    from src.utils.logger import setup_logger
    from src.utils.config_manager import ConfigManager
    from src.gui.main_window import MainWindow

    logger = setup_logger()
    logger.info(f"Запуск приложения 'Free Talk' v{__version__}")

    config_manager = ConfigManager()
    config = config_manager.load_config()
    config.app_name = "Free Talk"

    window = MainWindow(config_manager, config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
