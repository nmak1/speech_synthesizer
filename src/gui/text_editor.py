# src/gui/text_editor.py
from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor


class TextEditor(QWidget):
    text_changed = pyqtSignal()
    format_changed = pyqtSignal()   # курсор/выделение сменили формат — обновить панель
    learn_requested = pyqtSignal(str)  # текст изменился — пакетное обучение T9-словаря

    MIN_FONT = 8
    MAX_FONT = 96

    def __init__(self, config, on_text_changed=None):
        super().__init__()
        self.config = config
        self._predictor = None
        self._font_size = getattr(config, "default_font_size", 14)
        self._font_family = getattr(config, "default_font_family", "Segoe UI")
        self._text_color = getattr(config, "default_text_color", "#000000")
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
        self.text_edit.setAcceptRichText(False)   # вводимый текст остаётся plain-text
        self.text_edit.textChanged.connect(self.on_text_changed)
        # отслеживаем смену выделения/курсора для синхронизации панели формата
        self.text_edit.cursorPositionChanged.connect(self.format_changed.emit)

        font = QFont(self._font_family, self._font_size)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                color: {self._text_color};
            }}
            QTextEdit:focus {{ border-color: #4CAF50; }}
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

    # ---------- Форматирование ----------

    def set_font_family(self, family: str):
        """Сменить семейство шрифта (для выделения, если оно есть)."""
        self._font_family = family
        fmt = QTextCharFormat()
        fmt.setFont(QFont(family))
        self._apply_to_selection_or_all(fmt)
        self._schedule_save()

    def set_font_size(self, size: int):
        """Сменить размер шрифта (для выделения, если оно есть)."""
        size = max(self.MIN_FONT, min(self.MAX_FONT, size))
        if size == self._font_size and not self.has_selection():
            return
        self._font_size = size
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._apply_to_selection_or_all(fmt)
        # базовый шрифт редактора тоже меняем — новый ввод идёт в этом кегле
        font = self.text_edit.font()
        font.setPointSize(size)
        self.text_edit.setFont(font)
        self._schedule_save()

    def get_font_size(self) -> int:
        return self._font_size

    def set_text_color(self, color: str):
        """Сменить цвет текста (для выделения, если оно есть)."""
        self._text_color = color
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        self._apply_to_selection_or_all(fmt)
        self._refresh_base_color()
        self._schedule_save()

    def set_bold(self, bold: bool):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if bold else QFont.Normal)
        self._apply_to_selection_or_all(fmt)
        self._schedule_save()

    def set_italic(self, italic: bool):
        fmt = QTextCharFormat()
        fmt.setFontItalic(italic)
        self._apply_to_selection_or_all(fmt)
        self._schedule_save()

    def has_selection(self) -> bool:
        return self.text_edit.textCursor().hasSelection()

    def current_format(self) -> dict:
        """Текущий формат в точке курсора/выделения — для панели."""
        f = self.text_edit.currentCharFormat()
        fam = f.fontFamily() or self._font_family
        sz = f.fontPointSize()
        if sz <= 0:
            sz = float(self._font_size)
        brush = f.foreground()
        color = brush.color().name() if brush.color().isValid() else self._text_color
        return {
            "family": fam,
            "size": int(round(sz)),
            "color": color,
            "bold": f.fontWeight() >= QFont.Bold,
            "italic": f.fontItalic(),
        }

    def _apply_to_selection_or_all(self, fmt: QTextCharFormat):
        """Применить формат к выделению; если его нет — ко всему тексту."""
        cursor = self.text_edit.textCursor()
        had_selection = cursor.hasSelection()
        self._is_updating = True
        try:
            if had_selection:
                cursor.mergeCharFormat(fmt)
            else:
                self.text_edit.selectAll()
                self.text_edit.textCursor().mergeCharFormat(fmt)
                self.text_edit.moveCursor(QTextCursor.Start)
        finally:
            self._is_updating = False

    def _refresh_base_color(self):
        """Обновить базовый цвет редактора (для нового ввода / placeholder)."""
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                color: {self._text_color};
            }}
            QTextEdit:focus {{ border-color: #4CAF50; }}
        """)

    # ---------- Зум ----------

    def set_zoom(self, value: int):
        self._zoom_level = value
        base_size = getattr(self.config, "default_font_size", 14)
        new_size = max(self.MIN_FONT, int(round(base_size * (value / 100.0))))
        self.set_font_size(new_size)
        self._schedule_save()

    # ---------- Служебное ----------

    def on_text_changed(self):
        if not self._is_updating:
            self.text_changed.emit()
            self._schedule_save()
            self.learn_requested.emit(self.get_text())

    def set_predictor(self, predictor):
        """Подключить T9-предиктор для динамического обучения."""
        self._predictor = predictor

    def _schedule_save(self):
        """Отложенное сохранение — не чаще раза в 400 мс."""
        self._save_timer.start(400)

    def _flush_settings(self):
        settings = QSettings("FreeTalk", "App")
        settings.setValue("editor_text", self.get_text())
        settings.setValue("editor_font_size", self._font_size)
        settings.setValue("editor_zoom", self._zoom_level)
        settings.setValue("editor_font_family", self._font_family)
        settings.setValue("editor_text_color", self._text_color)

    MAX_RESTORE_LEN = 5000

    def load_settings(self):
        """Загрузка настроек. Огромный текст не восстанавливаем."""
        settings = QSettings("FreeTalk", "App")

        # Семейство шрифта и цвет (до загрузки текста)
        family = settings.value("editor_font_family", self._font_family)
        if family:
            self._font_family = family
            self.text_edit.setFont(QFont(self._font_family, self._font_size))
        color = settings.value("editor_text_color", self._text_color)
        if color:
            self._text_color = color
            self._refresh_base_color()

        # Загружаем текст, только если он не слишком большой
        text = settings.value("editor_text", "")
        if text and len(text) <= self.MAX_RESTORE_LEN:
            self._is_updating = True
            self.text_edit.clear()
            self.text_edit.insertPlainText(text)
            self._is_updating = False
        elif text and len(text) > self.MAX_RESTORE_LEN:
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
