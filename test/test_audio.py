# test_audio.py
import sounddevice as sd
import numpy as np

print("=" * 60)
print("Проверка аудио устройств")
print("=" * 60)

# Список устройств
print("\nДоступные аудио устройства:")
devices = sd.query_devices()
for i, device in enumerate(devices):
    print(f"{i}: {device['name']} (max inputs: {device['max_input_channels']}, max outputs: {device['max_output_channels']})")

print("\n" + "=" * 60)
print("Тест воспроизведения звука...")

# Генерируем тестовый звук (1000 Гц, 1 секунда)
sample_rate = 44100
duration = 1.0
frequency = 1000

t = np.linspace(0, duration, int(sample_rate * duration))
test_audio = 0.5 * np.sin(2 * np.pi * frequency * t)

try:
    print("Воспроизведение тестового звука...")
    sd.play(test_audio, sample_rate)
    sd.wait()
    print("✓ Тестовый звук воспроизведен успешно!")
except Exception as e:
    print(f"✗ Ошибка воспроизведения: {e}")

print("=" * 60)