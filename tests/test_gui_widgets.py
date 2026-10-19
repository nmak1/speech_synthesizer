# tests/test_gui_widgets.py
"""GUI-тесты виджетов FreeTalk через pytest-qt (offscreen-режим).

Проверяются: форматирование TextEditor, синхронизация FormatBar,
пунктуация/предсказания T9Widget, корректность хоткеев MainWindow.
Тяжёлые зависимости (torch/sounddevice) мокаются на уровне импорта,
поэтому тесты быстрые и не требуют GPU/аудио.
"""
import os
import sys
import types
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor


def _install_tts_mocks():
    """Мок src.tts_engine.silero_tts / audio_player до импорта main_window.

   MainWindow.__init__ запускает ModelReadyWorker, который вызывает
    tts_engine.initialize(); мок делает это мгновенно и без torch.
    """
    for name in ("src.tts_engine.silero_tts", "src.tts_engine.audio_player"):
        if name in sys.modules and getattr(sys.modules[name], "_is_test_mock", False):
            continue
        mod = types.ModuleType(name)
        mod._is_test_mock = True

        class _MockSileroTTS:
            def __init__(self, *a, **k):
                pass

            def initialize(self):
                return True

            def is_ready(self):
                return True

            def synthesize(self, *a, **k):
                return b""

            def cleanup(self):
                pass

        class _MockAudioPlayer:
            def __init__(self, *a, **k):
                pass

            def play(self, *a, **k):
                pass

            def stop(self, *a, **k):
                pass

            def cleanup(self):
                pass

        mod.SileroTTS = _MockSileroTTS
        mod.AudioPlayer = _MockAudioPlayer
        sys.modules[name] = mod
        pkg_name = name.rsplit(".", 1)[0]
        if pkg_name in sys.modules:
            setattr(sys.modules[pkg_name], name.rsplit(".", 1)[1], mod)


_install_tts_mocks()


@pytest.fixture()
def config(tmp_config):
    return tmp_config


class TestTextEditor:
    def test_set_get_text(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_text("привет мир")
        assert ed.get_text() == "привет мир"

    def test_font_size_change(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_font_size(24)
        assert ed.get_font_size() == 24
        assert int(ed.text_edit.font().pointSize()) == 24

    def test_font_size_clamped(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_font_size(1000)
        assert ed.get_font_size() == ed.MAX_FONT
        ed.set_font_size(1)
        assert ed.get_font_size() == ed.MIN_FONT

    def test_font_family_applied(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_text("текст")
        ed.set_font_family("Courier New")
        cursor_fmt = ed.current_format()
        assert cursor_fmt["family"] == "Courier New"

    def test_text_color_applied(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_text("окрашенный текст")
        ed.set_text_color("#d32f2f")
        assert ed.current_format()["color"].lower() == "#d32f2f"

    def test_bold_italic_flags(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_text("стиль")
        ed.set_bold(True)
        ed.set_italic(True)
        fmt = ed.current_format()
        assert fmt["bold"] is True
        assert fmt["italic"] is True

    def test_selection_only_formatted(self, qtbot, config):
        """Форматирование по выделению не трогает остальной текст."""
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        ed.set_text("абвгдеж")
        cursor = ed.text_edit.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.KeepAnchor)
        ed.text_edit.setTextCursor(cursor)
        assert ed.has_selection()
        ed.set_text_color("#0000ff")
        # первая часть — синяя, хвост — нет
        assert ed.current_format()["color"].lower() == "#0000ff"

    def test_learn_requested_signal(self, qtbot, config):
        from src.gui.text_editor import TextEditor

        ed = TextEditor(config)
        qtbot.addWidget(ed)
        with qtbot.waitSignal(ed.learn_requested, timeout=1000) as blocker:
            ed.text_edit.setPlainText("новое слово для обучения")
        assert "слово" in blocker.args[0]


class TestFormatBar:
    def test_font_changed_signal(self, qtbot, config):
        from src.gui.format_bar import FormatBar

        bar = FormatBar(config)
        qtbot.addWidget(bar)
        idx = bar.font_combo.findData("Arial")
        with qtbot.waitSignal(bar.font_changed, timeout=1000) as blocker:
            bar.font_combo.setCurrentIndex(idx)
        assert blocker.args == ["Arial"]

    def test_size_changed_signal(self, qtbot, config):
        from src.gui.format_bar import FormatBar

        bar = FormatBar(config)
        qtbot.addWidget(bar)
        idx = bar.size_combo.findData(20)
        with qtbot.waitSignal(bar.size_changed, timeout=1000) as blocker:
            bar.size_combo.setCurrentIndex(idx)
        assert blocker.args == [20]

    def test_preset_color_click(self, qtbot, config):
        from src.gui.format_bar import FormatBar, PRESET_COLORS

        bar = FormatBar(config)
        qtbot.addWidget(bar)
        # пресеты цветов — простые QPushButton (ColorButton — отдельный класс)
        from PyQt5.QtWidgets import QPushButton
        preset_btns = [b for b in bar.findChildren(QPushButton)
                       if b is not bar.color_btn and b.isCheckable() is False]
        expected = PRESET_COLORS[-1][1]
        with qtbot.waitSignal(bar.color_changed, timeout=1000) as blocker:
            preset_btns[-1].click()
        assert blocker.args == [expected]

    def test_sync_from_editor_no_signals(self, qtbot, config):
        """sync_from_editor обновляет виджеты, но не генерирует сигналы."""
        from src.gui.format_bar import FormatBar

        bar = FormatBar(config)
        qtbot.addWidget(bar)
        spy_fired = []
        bar.font_changed.connect(lambda *_: spy_fired.append(1))
        bar.size_changed.connect(lambda *_: spy_fired.append(1))
        bar.sync_from_editor(family="Georgia", size=18, color="#ff0000",
                             bold=True, italic=False)
        assert not spy_fired
        assert bar.font_combo.currentData() == "Georgia"
        assert bar.size_combo.currentData() == 18
        assert bar.bold_btn.isChecked() is True
        assert bar.italic_btn.isChecked() is False
        assert bar.color_btn.get_color() == "#ff0000"


class TestT9Widget:
    def test_button_hidden_by_default(self, qtbot, config):
        """Кнопка T9 убрана из интерфейса (t9_show_button=False)."""
        from src.gui.t9_widget import T9Widget

        w = T9Widget(config)
        qtbot.addWidget(w)
        assert not w.toggle_btn.isVisibleTo(w)
        assert w.is_enabled() is False

    def test_punctuation_emits_word_selected(self, qtbot, config):
        from src.gui.t9_widget import T9Widget
        from PyQt5.QtWidgets import QPushButton

        w = T9Widget(config)
        qtbot.addWidget(w)
        punct_btns = [b for b in w.findChildren(QPushButton)
                      if b.text() in {",", ".", "!", "?", "...", ";", ":", "(", ")"}]
        assert len(punct_btns) == 9
        btn = next(b for b in punct_btns if b.text() == "!")
        with qtbot.waitSignal(w.word_selected, timeout=1000) as blocker:
            qtbot.mouseClick(btn, Qt.LeftButton)
        assert blocker.args == ["!"]

    def test_suggestions_hidden_when_empty(self, qtbot, config):
        from src.gui.t9_widget import T9Widget

        w = T9Widget(config)
        qtbot.addWidget(w)
        w.update_suggestions([])
        assert not w.suggestions_container.isVisibleTo(w)

    def test_suggestions_shown_when_enabled(self, qtbot, config):
        from src.gui.t9_widget import T9Widget

        w = T9Widget(config)
        qtbot.addWidget(w)
        w.enable()
        w.update_suggestions(["привет", "природа"])
        assert w.suggestions_container.isVisibleTo(w)
        assert w.suggestion_buttons[0].text() == "привет"
        assert w.suggestion_buttons[1].text() == "природа"
        assert not w.suggestion_buttons[2].isVisibleTo(w)

    def test_suggestion_click_emits_word(self, qtbot, config):
        from src.gui.t9_widget import T9Widget

        w = T9Widget(config)
        qtbot.addWidget(w)
        w.enable()
        w.update_suggestions(["привет", "природа"])
        with qtbot.waitSignal(w.word_selected, timeout=1000) as blocker:
            w.on_button_clicked(1)
        assert blocker.args == ["природа"]

    def test_programmatic_toggle_no_recurse(self, qtbot, config):
        """setChecked() из enable()/disable() не должен ломать состояние."""
        from src.gui.t9_widget import T9Widget

        w = T9Widget(config)
        qtbot.addWidget(w)
        w.disable()
        assert w.is_enabled() is False
        w.enable()
        assert w.is_enabled() is True


class TestMainWindowShortcuts:
    def test_shortcuts_registered(self, qtbot, config):
        from src.gui.main_window import MainWindow

        win = MainWindow(config, config)
        qtbot.addWidget(win)
        shortcuts = {a.shortcut().toString(): a.objectName() or a.text()
                     for a in win.actions()}
        assert "Ctrl+Return" in shortcuts   # Озвучить
        assert "Ctrl+S" in shortcuts         # Скачать
        assert "Esc" in shortcuts            # Стоп
        assert "Ctrl+Q" in shortcuts         # Выход

    def test_clear_shortcut_clears_text(self, qtbot, config):
        from src.gui.main_window import MainWindow

        win = MainWindow(config, config)
        qtbot.addWidget(win)
        win.text_editor.set_text("что-то набрано")
        assert win.act_clear.shortcut().matches("Ctrl+Del")
        win.act_clear.trigger()
        assert win.text_editor.get_text() == ""
