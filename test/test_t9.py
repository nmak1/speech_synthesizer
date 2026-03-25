# test_t9.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.text_processor.t9_predictor import T9Predictor
from src.config import AppConfig

config = AppConfig()
t9 = T9Predictor(config)

# Тестируем предсказания
test_prefixes = ['п', 'пр', 'при', 'прив', 'з', 'зд', 'здр', 'сп', 'спа', 'спас']

print("=" * 60)
print("Тест T9 предсказаний")
print("=" * 60)

for prefix in test_prefixes:
    predictions = t9.predict(prefix)
    print(f"\nПрефикс '{prefix}':")
    if predictions:
        for i, word in enumerate(predictions[:5], 1):
            print(f"  {i}. {word}")
    else:
        print("  Нет предсказаний")

print("\n" + "=" * 60)