# build_complete.ps1
# Скрипт сборки для PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Сборка Free Talk - Голосовой синтезатор" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Активация виртуального окружения
Write-Host "[1/5] Активация виртуального окружения..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 2. Установка PyInstaller
Write-Host ""
Write-Host "[2/5] Установка PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller

# 3. Сборка EXE
Write-Host ""
Write-Host "[3/5] Сборка EXE файла FreeTalk.exe..." -ForegroundColor Yellow
Write-Host "Это может занять 2-3 минуты..." -ForegroundColor Gray
pyinstaller --onefile --windowed --name FreeTalk --add-data "data;data" --icon=logo.ico main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при сборке EXE файла!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# 4. Проверка файлов
Write-Host ""
Write-Host "[4/5] Проверка файлов..." -ForegroundColor Yellow
if (Test-Path "dist\FreeTalk.exe") {
    Write-Host "OK - EXE файл создан" -ForegroundColor Green
} else {
    Write-Host "ОШИБКА: dist\FreeTalk.exe не создан!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# 5. Сборка установщика
Write-Host ""
Write-Host "[5/5] Сборка установщика Inno Setup..." -ForegroundColor Yellow
Write-Host ""

# Переходим в папку installers
Set-Location installers

# Проверяем наличие Inno Setup
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    Write-Host "Запуск Inno Setup Compiler..." -ForegroundColor Green
    & $innoPath "setup_fixed.iss"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Ошибка при сборке установщика!" -ForegroundColor Red
        Set-Location ..
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
} else {
    Write-Host "Inno Setup не найден!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Пожалуйста, установите Inno Setup:" -ForegroundColor Yellow
    Write-Host "1. Скачайте с https://jrsoftware.org/isdl.php" -ForegroundColor Gray
    Write-Host "2. Установите в C:\Program Files (x86)\Inno Setup 6" -ForegroundColor Gray
    Write-Host ""
    Set-Location ..
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Set-Location ..

# 6. Результат
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "СБОРКА УСПЕШНО ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Портативная версия: dist\FreeTalk.exe" -ForegroundColor Cyan
if (Test-Path "installers\FreeTalk_Setup.exe") {
    $size = (Get-Item "installers\FreeTalk_Setup.exe").Length
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "Установщик: installers\FreeTalk_Setup.exe ($sizeMB MB)" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Для тестирования:" -ForegroundColor Yellow
Write-Host "  - Портативная версия: .\dist\FreeTalk.exe" -ForegroundColor Gray
Write-Host "  - Установщик: .\installers\FreeTalk_Setup.exe" -ForegroundColor Gray
Write-Host ""
Read-Host "Нажмите Enter для выхода"