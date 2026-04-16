# test_model.py
import os
import torch

print("=" * 60)
print("Проверка модели Silero TTS для Free Talk")
print("=" * 60)

# Проверяем пути
model_path = "data/models/v3_1_ru.pt"
print(f"\nПуть к модели: {model_path}")

if os.path.exists(model_path):
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"✓ Модель найдена! Размер: {file_size:.2f} MB")

    # Пробуем загрузить
    print("\nПопытка загрузки модели...")
    try:
        model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
        print("✓ Модель успешно загружена!")

        # Пробуем синтез
        print("\nПопытка синтеза...")
        audio = model.apply_tts(text="Привет мир", speaker="aidar", sample_rate=48000)
        print(f"✓ Синтез успешен! Длина аудио: {len(audio)} samples")

        # Проверяем аудио
        import numpy as np

        audio_array = audio.cpu().numpy() if torch.is_tensor(audio) else audio
        print(f"  Максимальная амплитуда: {np.max(np.abs(audio_array)):.4f}")

    except Exception as e:
        print(f"✗ Ошибка загрузки: {e}")
        print("\nВозможные решения:")
        print("1. Запустите: python download_model.py и выберите 'y' для перезагрузки")
        print("2. Проверьте свободное место на диске")
        print("3. Проверьте интернет-соединение")
else:
    print("✗ Модель не найдена!")
    print("\nЗапустите скачивание модели:")
    print("  python download_model.py")
    print("  При вопросе 'Скачать заново?' введите 'y'")

print("\n" + "=" * 60)