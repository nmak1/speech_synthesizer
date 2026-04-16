# setup_logo.py
"""
Скрипт для настройки логотипа Free Talk
"""
import os
import shutil
from PIL import Image


def setup_logo():
    """Настройка логотипа программы"""
    print("=" * 60)
    print("Настройка логотипа Free Talk")
    print("=" * 60)

    # Проверяем наличие Pillow
    try:
        from PIL import Image
    except ImportError:
        print("\n⚠ Библиотека Pillow не установлена!")
        print("Установите её командой: pip install Pillow")
        return False

    # Ищем PNG файлы в текущей папке
    png_files = [f for f in os.listdir('.') if f.lower().endswith('.png') and f.lower() != 'logo.png']

    # Проверяем наличие logo.png
    if os.path.exists("logo.png"):
        print("\n✓ Логотип уже существует: logo.png")
        use_existing = input("Использовать существующий логотип? (y/n): ")
        if use_existing.lower() == 'y':
            logo_png = "logo.png"
        else:
            if not png_files:
                print("\n⚠ Нет других PNG файлов для логотипа!")
                return False
            logo_png = None
    else:
        logo_png = None

    if not logo_png:
        if not png_files:
            print("\n⚠ PNG файлы не найдены в текущей папке!")
            print("\nПожалуйста, скопируйте ваш логотип (logo.png) в папку проекта")
            print(f"Текущая папка: {os.getcwd()}")
            return False

        print("\nНайденные PNG файлы:")
        for i, f in enumerate(png_files, 1):
            file_size = os.path.getsize(f) / 1024
            print(f"  {i}. {f} ({file_size:.1f} KB)")

        # Выбираем файл для логотипа
        while True:
            try:
                choice = input(f"\nВыберите номер файла для логотипа (1-{len(png_files)}): ")
                logo_png = png_files[int(choice) - 1]
                break
            except (ValueError, IndexError):
                print("Неверный выбор! Попробуйте снова.")

    print(f"\n✓ Выбран файл: {logo_png}")

    # Копируем в logo.png
    if logo_png != "logo.png":
        shutil.copy(logo_png, "logo.png")
        print("✓ Файл скопирован в logo.png")

    # Создаем уменьшенные версии для интерфейса
    try:
        img = Image.open("logo.png")

        # Создаем маленькую иконку для панели задач (32x32)
        img_small = img.resize((32, 32), Image.Resampling.LANCZOS)
        img_small.save("logo_small.png")
        print("✓ Создана маленькая иконка: logo_small.png")

        # Конвертируем в ICO для установщика Windows
        img_ico = img.resize((256, 256), Image.Resampling.LANCZOS)
        img_ico.save("logo.ico", format='ICO', sizes=[(256, 256)])
        print("✓ Создан файл logo.ico для установщика Windows")

        # Создаем версию для окна (64x64)
        img_medium = img.resize((64, 64), Image.Resampling.LANCZOS)
        img_medium.save("logo_medium.png")
        print("✓ Создана средняя иконка: logo_medium.png")

    except Exception as e:
        print(f"⚠ Ошибка при создании иконок: {e}")

    print("\n" + "=" * 60)
    print("Логотип успешно настроен!")
    print("Созданные файлы:")
    print("  - logo.png (основной логотип)")
    print("  - logo_small.png (иконка 32x32)")
    print("  - logo_medium.png (иконка 64x64)")
    print("  - logo.ico (иконка для установщика)")
    print("=" * 60)
    return True


if __name__ == "__main__":
    setup_logo()