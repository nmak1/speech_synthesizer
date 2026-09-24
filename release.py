# release.py
import os
import sys
import glob
import shutil
import subprocess

VERSION = "2.0.0"


def clean():
    """Очистка перед сборкой. FreeTalk.spec НЕ удаляем — он в git."""
    print("[1/6] Очистка...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    print("  OK")


def create_ico():
    """Создание квадратной иконки из logo.png."""
    print("[2/6] Создание иконки...")
    try:
        from PIL import Image

        candidates = [
            "imeg/logo.png",
            "logo.png",
            "imeg/logo_highres.png",
            "imeg/logo_big.png",
        ]
        src = next((c for c in candidates if os.path.exists(c)), None)
        if not src:
            print("  [WARN] Логотип не найден, logo.ico не создан")
            return

        img = Image.open(src).convert("RGBA")

        # Обрезаем до квадрата по центру
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))

        sizes = [256, 128, 96, 64, 48, 32, 24, 16]
        icons = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
        icons[0].save(
            "logo.ico",
            format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=icons[1:],
        )
        print(f"  ICO создан из {src}")
    except Exception as e:
        print(f"  Ошибка: {e}")


def build_exe():
    """Сборка EXE через FreeTalk.spec."""
    print("[3/6] Сборка EXE...")

    if not os.path.exists("data/models/v3_1_ru.pt"):
        print("  [ERROR] Модель не найдена: data/models/v3_1_ru.pt")
        return False

    if not os.path.exists("FreeTalk.spec"):
        print("  [ERROR] FreeTalk.spec не найден")
        return False

    cmd = [sys.executable, "-m", "PyInstaller", "FreeTalk.spec", "--clean", "--noconfirm"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists("dist/FreeTalk.exe"):
        size = os.path.getsize("dist/FreeTalk.exe") / (1024 * 1024)
        print(f"  [OK] EXE создан: {size:.1f} MB")
        return True

    print("  [ERROR] Ошибка сборки EXE")
    if result.stderr:
        print(result.stderr[-1000:])
    return False


def prepare_installer():
    """Копирование EXE и ресурсов в installers/."""
    print("[4/6] Подготовка установщика...")
    os.makedirs("installers", exist_ok=True)

    shutil.copy("dist/FreeTalk.exe", "installers/FreeTalk.exe")

    # Логотипы
    if os.path.exists("logo.ico"):
        shutil.copy("logo.ico", "installers/logo.ico")

    # imeg копируется через setup.iss из ..\imeg — здесь не нужно

    print("  OK")


def build_installer():
    """Сборка установщика через Inno Setup."""
    print("[5/6] Сборка установщика...")

    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc = next((p for p in iscc_paths if os.path.exists(p)), None)

    if not iscc:
        print("  [ERROR] Inno Setup не найден")
        return False

    result = subprocess.run([iscc, "installers/setup.iss"], capture_output=True, text=True)

    expected = f"installers/FreeTalk_Setup_v{VERSION}.exe"
    if os.path.exists(expected):
        size = os.path.getsize(expected) / (1024 * 1024)
        print(f"  [OK] Установщик создан: {size:.1f} MB")
        return True

    found = glob.glob("installers/FreeTalk_Setup_*.exe")
    if found:
        print(f"  [OK] Найден: {found[0]}")
        return True

    print("  [ERROR] Установщик не создан")
    if result.stderr:
        print(result.stderr[-1000:])
    return False


def git_commit():
    """Git: add + commit + tag."""
    print("[6/6] Git...")
    try:
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(
            ["git", "commit", "-m",
             f"Release v{VERSION}: оптимизация синтеза, крупные элементы UI, улучшенный T9"],
            check=False,
        )
        subprocess.run(
            ["git", "tag", "-a", f"v{VERSION}", "-m", f"Release v{VERSION}"],
            check=False,
        )
        print(f"  OK. Не забудьте: git push origin main && git push origin v{VERSION}")
    except Exception as e:
        print(f"  [WARN] {e}")


def main():
    print("=" * 50)
    print(f"    FreeTalk v{VERSION} - Релиз")
    print("=" * 50)

    clean()
    create_ico()

    if not build_exe():
        print("Ошибка сборки EXE!")
        sys.exit(1)

    prepare_installer()

    if not build_installer():
        print("Установщик не собран, но EXE готов")

    git_commit()

    print("\n" + "=" * 50)
    print(f"    Релиз v{VERSION} готов!")
    print("=" * 50)
    print("\nФайлы для GitHub Release:")
    print(f"  • installers/FreeTalk_Setup_v{VERSION}.exe")
    print(f"  • dist/FreeTalk.exe (portable)")
    print(f"\nТег: v{VERSION}")
    print(f"Репозиторий: https://github.com/nmak1/speech_synthesizer")


if __name__ == "__main__":
    main()