# release.py
import os
import sys
import shutil
import subprocess

VERSION = "1.2.0"


def clean():
    """Очистка перед сборкой"""
    print("[1/5] Очистка...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists('FreeTalk.spec'):
        os.remove('FreeTalk.spec')
    print("  OK")


def create_ico():
    """Создание иконки"""
    print("[2/5] Создание иконки...")
    try:
        from PIL import Image
        src = "imeg/logo_highres.png"
        if not os.path.exists(src):
            src = "logo_big.png"

        img = Image.open(src)
        img = img.convert('RGBA')

        sizes = [256, 128, 96, 64, 48, 32, 24, 16]
        icons = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
        icons[0].save('logo.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=icons[1:])
        print("  ICO создан")
    except Exception as e:
        print(f"  Ошибка: {e}")


def build_exe():
    """Сборка EXE"""
    print("[3/5] Сборка EXE...")

    # Создаем version файл
    version_content = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 2, 0, 0),
    prodvers=(1, 2, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'FileDescription', u'FreeTalk Speech Synthesizer'),
           StringStruct(u'FileVersion', u'1.2.0.0'),
           StringStruct(u'InternalName', u'FreeTalk'),
           StringStruct(u'LegalCopyright', u'FreeTalk'),
           StringStruct(u'OriginalFilename', u'FreeTalk.exe'),
           StringStruct(u'ProductName', u'FreeTalk'),
           StringStruct(u'ProductVersion', u'1.2.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    with open('version.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=FreeTalk',
        '--windowed',
        '--onefile',
        '--icon=logo.ico',
        '--version-file=version.txt',
        '--add-data=src;src',
        '--add-data=data/models/v3_1_ru.pt;data/models',
        '--add-data=data/dictionaries/t9_dictionary.json;data/dictionaries',
        '--add-data=imeg;imeg',
        '--add-data=logo.ico;.',
        '--add-data=logo.png;.',
        '--add-data=logo_big.png;.',
        '--hidden-import=torch',
        '--hidden-import=torchaudio',
        '--hidden-import=soundfile',
        '--collect-all=torch',
        '--collect-all=soundfile',
        '--noconfirm',
        'main.py'
    ]

    subprocess.run(cmd)

    # Удаляем временный файл
    if os.path.exists('version.txt'):
        os.remove('version.txt')

    if os.path.exists('dist/FreeTalk.exe'):
        size = os.path.getsize('dist/FreeTalk.exe') / (1024 * 1024)
        print(f"  EXE создан: {size:.1f} MB")
        return True
    return False


def prepare_installer():
    """Подготовка установщика"""
    print("[4/5] Подготовка установщика...")

    os.makedirs('installers', exist_ok=True)

    # Копируем EXE
    shutil.copy('dist/FreeTalk.exe', 'installers/FreeTalk.exe')

    # Копируем иконки
    for icon in ['logo.ico', 'logo.png', 'logo_big.png']:
        if os.path.exists(icon):
            shutil.copy(icon, f'installers/{icon}')

    # Копируем setup.iss
    if os.path.exists('installers/setup.iss'):
        print("  setup.iss уже существует")

    print("  OK")


def build_installer():
    """Сборка установщика"""
    print("[5/5] Сборка установщика...")

    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]

    iscc = None
    for path in iscc_paths:
        if os.path.exists(path):
            iscc = path
            break

    if not iscc:
        print("  Inno Setup не найден")
        return False

    result = subprocess.run([iscc, 'installers/setup.iss'], capture_output=True, text=True)

    if os.path.exists('installers/FreeTalk_Setup_v1.2.0.exe'):
        size = os.path.getsize('installers/FreeTalk_Setup_v1.2.0.exe') / (1024 * 1024)
        print(f"  Установщик создан: {size:.1f} MB")
        return True
    return False


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
    build_installer()

    print("\n" + "=" * 50)
    print(f"    Релиз v{VERSION} готов!")
    print("=" * 50)
    print("\nФайлы:")
    print("  • installers/FreeTalk.exe")
    print("  • installers/FreeTalk_Setup_v1.2.0.exe")


if __name__ == "__main__":
    main()