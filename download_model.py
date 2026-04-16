# download_model.py
"""
Скачивание модели Silero TTS для Free Talk
"""
import os
import torch
import requests


def download_model():
    """Скачивание модели Silero TTS"""
    print("=" * 60)
    print("Скачивание модели Silero TTS для Free Talk")
    print("=" * 60)

    # Путь для сохранения модели
    model_dir = "data/models"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "v3_1_ru.pt")

    # Проверяем, существует ли уже модель
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"\nМодель уже существует: {model_path}")
        print(f"Размер: {file_size:.2f} MB")

        choice = input("Скачать заново? (y/n): ")
        if choice.lower() != 'y':
            print("Используем существующую модель")
            return True

    # Скачиваем модель
    print("\nСкачивание модели...")
    model_url = "https://models.silero.ai/models/tts/ru/v3_1_ru.pt"

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

        print(f"\n✓ Модель успешно скачана: {model_path}")
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"Размер: {file_size:.2f} MB")
        return True

    except Exception as e:
        print(f"\n✗ Ошибка скачивания: {e}")
        return False


if __name__ == "__main__":
    download_model()