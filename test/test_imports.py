# test_imports.py
import sys
import os

print("=" * 60)
print("Voice Synthesizer - Проверка импортов")
print("=" * 60)

# Проверка основных импортов
try:
    from PyQt5.QtWidgets import QApplication
    print("✓ PyQt6.QtWidgets")
except Exception as e:
    print(f"✗ PyQt6.QtWidgets: {e}")

try:
    import torch
    print(f"✓ torch {torch.__version__}")
except Exception as e:
    print(f"✗ torch: {e}")

try:
    import torchaudio
    print(f"✓ torchaudio {torchaudio.__version__}")
except Exception as e:
    print(f"✗ torchaudio: {e}")

try:
    import numpy as np
    print(f"✓ numpy {np.__version__}")
except Exception as e:
    print(f"✗ numpy: {e}")

try:
    import sounddevice as sd
    print("✓ sounddevice")
    # Проверка аудио устройств
    devices = sd.query_devices()
    print(f"  Найдено аудио устройств: {len(devices)}")
except Exception as e:
    print(f"✗ sounddevice: {e}")

try:
    import soundfile as sf
    print("✓ soundfile")
except Exception as e:
    print(f"✗ soundfile: {e}")

try:
    import nltk
    print(f"✓ nltk {nltk.__version__}")
except Exception as e:
    print(f"✗ nltk: {e}")

try:
    import pyphen
    print("✓ pyphen")
except Exception as e:
    print(f"✗ pyphen: {e}")

# Проверка импорта модулей проекта
print("\n" + "=" * 60)
print("Проверка импорта модулей проекта")
print("=" * 60)

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

modules_to_check = [
    "src.config",
    "src.constants",
    "src.gui.main_window",
    "src.gui.text_editor",
    "src.gui.tts_controls",
    "src.gui.t9_widget",
    "src.gui.zoom_slider",
    "src.tts_engine.silero_tts",
    "src.tts_engine.audio_player",
    "src.tts_engine.audio_saver",
    "src.text_processor.preprocessor",
    "src.text_processor.t9_predictor",
    "src.utils.logger",
    "src.utils.config_manager",
    "src.utils.file_manager"
]

for module_name in modules_to_check:
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        print(f"✗ {module_name}: {e}")

print("\n" + "=" * 60)
print("Проверка завершена")
print("=" * 60)