# quick_diagnose.py
import os
import sys

print("=" * 60)
print("Диагностика Free Talk")
print("=" * 60)

# Проверяем пути
print("\n1. Проверка структуры папок:")
print(f"   Текущая папка: {os.getcwd()}")

data_dir = "data"
models_dir = os.path.join(data_dir, "models")
model_path = os.path.join(models_dir, "v3_1_ru.pt")

print(f"   Папка data существует: {os.path.exists(data_dir)}")
print(f"   Папка models существует: {os.path.exists(models_dir)}")
print(f"   Файл модели существует: {os.path.exists(model_path)}")

if os.path.exists(model_path):
    size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"   Размер модели: {size:.2f} MB")

# Проверяем импорты
print("\n2. Проверка импортов:")
try:
    import torch

    print(f"   ✓ torch: {torch.__version__}")
except ImportError as e:
    print(f"   ✗ torch: {e}")

try:
    import sounddevice

    print(f"   ✓ sounddevice: {sounddevice.__version__}")
except ImportError as e:
    print(f"   ✗ sounddevice: {e}")

try:
    import numpy

    print(f"   ✓ numpy: {numpy.__version__}")
except ImportError as e:
    print(f"   ✗ numpy: {e}")

# Пробуем загрузить модель
if os.path.exists(model_path):
    print("\n3. Попытка загрузки модели:")
    try:
        import torch

        model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
        print("   ✓ Модель загружена успешно!")

        # Пробуем синтез
        print("\n4. Попытка синтеза речи:")
        audio = model.apply_tts(text="Тест", speaker="aidar", sample_rate=48000)
        print(f"   ✓ Синтез успешен! Длина: {len(audio)} samples")

        import numpy as np

        audio_array = audio.cpu().numpy() if torch.is_tensor(audio) else audio
        print(f"   Максимальная амплитуда: {np.max(np.abs(audio_array)):.4f}")

        print("\n✅ Все проверки пройдены! Программа должна работать.")

    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        print("\n   Рекомендация: Модель повреждена.")
        print("   Запустите: python download_model.py и выберите 'y'")
else:
    print("\n❌ Модель не найдена!")
    print("Запустите: python download_model.py")

print("\n" + "=" * 60)
input("Нажмите Enter для выхода...")