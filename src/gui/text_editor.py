# src/gui/text_editor.py
from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont


class TextEditor(QWidget):
    text_changed = pyqtSignal()

    MIN_FONT = 8
    MAX_FONT = 96

    def __init__(self, config, on_text_changed=None):
        super().__init__()
        self.config = config
        self._font_size = getattr(config, "default_font_size", 14)
        self._zoom_level = 100
        self._is_updating = False
        self._on_text_changed_cb = on_text_changed   # ← запоминаем, не подключаем
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_settings)

        self.init_ui()
        self.load_settings()                          # ← загрузка без сигнала

        # Подключаем сигнал ТОЛЬКО ПОСЛЕ полной инициализации
        if on_text_changed:
            self.text_changed.connect(on_text_changed)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите текст для озвучивания...")
        self.text_edit.textChanged.connect(self.on_text_changed)

        font = QFont("Segoe UI", self._font_size)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-family: 'Segoe UI';
            }
            QTextEdit:focus { border-color: #4CAF50; }
        """)
        layout.addWidget(self.text_edit)

    # ---------- API ----------

    def set_text(self, text: str):
        self._is_updating = True
        self.text_edit.setText(text)
        self._is_updating = False
        self._schedule_save()

    def get_text(self) -> str:
        return self.text_edit.toPlainText()

    def set_font_size(self, size: int):
        size = max(self.MIN_FONT, min(self.MAX_FONT, size))
        if size == self._font_size:
            return
        self._font_size = size
        font = self.text_edit.font()
        font.setPointSize(size)
        self.text_edit.setFont(font)
        self._schedule_save()

    def get_font_size(self) -> int:
        return self._font_size

    def set_zoom(self, value: int):
        self._zoom_level = value
        base_size = getattr(self.config, "default_font_size", 14)
        # Не клиппим жёстко — позволим MIN/MAX в set_font_size
        new_size = max(self.MIN_FONT, int(round(base_size * (value / 100.0))))
        self.set_font_size(new_size)
        self._schedule_save()

    # ---------- Служебное ----------

    def on_text_changed(self):
        if not self._is_updating:
            self.text_changed.emit()
            self._schedule_save()

    def _schedule_save(self):
        """Отложенное сохранение — не чаще раза в 400 мс."""
        self._save_timer.start(400)

    def _flush_settings(self):
        settings = QSettings("FreeTalk", "App")
        settings.setValue("editor_text", self.get_text())
        settings.setValue("editor_font_size", self._font_size)
        settings.setValue("editor_zoom", self._zoom_level)

    MAX_RESTORE_LEN = 5000

    def load_settings(self):
        """Загрузка настроек. Огромный текст не восстанавливаем."""
        settings = QSettings("FreeTalk", "App")

        # Загружаем текст, только если он не слишком большой
        text = settings.value("editor_text", "")
        if text and len(text) <= self.MAX_RESTORE_LEN:
            self._is_updating = True
            self.text_edit.setText(text)
            self._is_updating = False
        elif text and len(text) > self.MAX_RESTORE_LEN:
            # Показываем заглушку и пишем в лог
            try:
                from src.utils.logger import get_logger
                get_logger().info(
                    f"Сохранённый текст ({len(text)} симв.) превышает лимит "
                    f"{self.MAX_RESTORE_LEN} — не восстанавливаем"
                )
            except Exception:
                pass

        # Размер шрифта
        font_size = settings.value("editor_font_size", self._font_size, type=int)
        if font_size:
            self.set_font_size(font_size)

        # Зум
        zoom = settings.value("editor_zoom", 100, type=int)
        if zoom:
            self._zoom_level = zoom

    def save_settings(self):
        """Оставлено для совместимости — форсирует сохранение."""
        self._save_timer.stop()
        self._flush_settings()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.text_edit.toPlainText():
            self.text_edit.selectAll()