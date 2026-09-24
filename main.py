# main.py
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap


def main():
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("FreeTalk")
    app.setOrganizationName("FreeTalk")

    icon = QIcon()
    icon_paths = [
        "imeg/logo.ico",
        "logo.ico",
        "imeg/logo.png",
        "logo.png",
        os.path.join(os.path.dirname(sys.executable), "imeg", "logo.ico"),
        os.path.join(os.path.dirname(sys.executable), "logo.ico"),
    ]
    for path in icon_paths:
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                for size in [16, 32, 48, 64, 128, 256]:
                    icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                break
    if not icon.isNull():
        app.setWindowIcon(icon)

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "freetalk.synthesizer.version2.0"
        )
    except Exception:
        pass

    from src.utils.logger import setup_logger
    from src.utils.config_manager import ConfigManager
    from src.gui.main_window import MainWindow

    logger = setup_logger()
    logger.info("Запуск приложения 'Free Talk' v2.0.0")

    config_manager = ConfigManager()
    config = config_manager.load_config()
    config.app_name = "Free Talk"

    window = MainWindow(config_manager, config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()