# test_tts.py - исправленная версия
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import torch
import sounddevice as sd
import numpy as np

print("=" * 60)
print("Тест Silero TTS")
print("=" * 60)

# Путь к модели
model_path = os.path.join("../data", "models", "v3_1_ru.pt")
print(f"\nПуть к модели: {model_path}")

# Проверяем существование модели
if not os.path.exists(model_path):
    print("Модель не найдена, скачивание...")
    import requests

    model_url = "https://models.silero.ai/models/tts/ru/v3_1_ru.pt"
    print(f"Скачивание с: {model_url}")

    try:
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open(model_path, 'wb') as f:
            downloaded = 0
            for data in response.iter_content(chunk_size=8192):
                downloaded += len(data)
                f.write(data)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    if int(percent) % 10 == 0:
                        print(f"Прогресс: {percent:.1f}%")

        print("✓ Модель скачана успешно")
    except Exception as e:
        print(f"✗ Ошибка скачивания: {e}")
        sys.exit(1)
else:
    print("✓ Модель найдена")

# Загрузка модели - правильный способ
print("\nЗагрузка модели...")
try:
    # Используем правильный метод загрузки для Silero TTS
    device = torch.device('cpu')

    # Загружаем модель через torch.hub
    print("Загрузка через torch.hub...")
    model, example_text = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker='v3_1_ru'
    )

    model.to(device)
    print("✓ Модель загружена успешно")
    print(f"Используется устройство: {device}")

except Exception as e:
    print(f"✗ Ошибка загрузки через hub: {e}")

    # Альтернативный способ - загрузка из файла
    try:
        print("Пробуем альтернативный способ загрузки...")
        model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
        print("✓ Модель загружена из файла")
    except Exception as e2:
        print(f"✗ Ошибка загрузки из файла: {e2}")
        sys.exit(1)

# Тестируем синтез
print("\n" + "=" * 60)
print("Тестирование синтеза речи")
print("=" * 60)

test_texts = [
    "Привет мир",
    "Здравствуйте, как дела?",
    "Это тест голосового синтезатора"
]

voices = ["aidar", "baya", "kseniya", "xenia", "eugene"]
sample_rate = 48000

for voice in voices:
    for text in test_texts[:1]:
        print(f"\nГолос: {voice}")
        print(f"Текст: '{text}'")

        try:
            # Синтез
            print("Синтез аудио...")
            audio = model.apply_tts(text=text, speaker=voice, sample_rate=sample_rate)

            # Конвертируем в numpy
            if torch.is_tensor(audio):
                audio = audio.cpu().numpy()

            print(f"✓ Аудио синтезировано, длина: {len(audio)} samples")

            # Проверяем, что аудио не пустое
            if len(audio) == 0:
                print("✗ Аудио пустое")
                continue

            # Проверяем амплитуду
            max_val = np.max(np.abs(audio))
            print(f"Максимальная амплитуда: {max_val:.4f}")

            # Нормализация если нужно
            if max_val > 1.0:
                audio = audio / max_val
                print("Аудио нормализовано")

            # Воспроизведение
            print("Воспроизведение...")
            sd.play(audio, sample_rate)
            sd.wait()
            print("✓ Воспроизведение завершено")

            # Небольшая пауза
            import time

            time.sleep(0.5)

        except Exception as e:
            print(f"✗ Ошибка: {e}")
            import traceback

            traceback.print_exc()

print("\n" + "=" * 60)
print("Тест завершен")
print("=" * 60)