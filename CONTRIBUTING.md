# Contributing to Voice Synthesizer

Мы рады, что вы хотите внести свой вклад в развитие Voice Synthesizer!

## Как помочь

1. **Сообщать об ошибках** - создавайте Issue с подробным описанием
2. **Предлагать улучшения** - создавайте Issue с меткой enhancement
3. **Писать код** - создавайте Pull Request
4. **Улучшать документацию** - исправляйте опечатки, добавляйте примеры

## Процесс разработки

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Внесите изменения
4. Зафиксируйте: `git commit -m 'Add amazing feature'`
5. Запушьте: `git push origin feature/amazing-feature`
6. Создайте Pull Request

## Стиль кода

- Используйте PEP 8
- Добавляйте docstring для функций и классов
- Комментируйте сложные участки кода
- Тестируйте изменения

## Сборка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py

# Сборка EXE
pyinstaller --onefile --windowed --name VoiceSynthesizer main.py