@echo off
setlocal

echo ============================================
echo   KiwiLab X00Team - Build (Nuitka)
echo ============================================

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден в PATH.
    pause
    exit /b 1
)

:: Установка зависимостей
echo.
echo [1/3] Установка зависимостей...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Не удалось установить зависимости.
    pause
    exit /b 1
)

:: Очистка старой сборки
echo.
echo [2/3] Очистка старой сборки...
if exist build rmdir /s /q build
if exist main.build rmdir /s /q main.build
if exist main.dist rmdir /s /q main.dist
if exist main.onefile-build rmdir /s /q main.onefile-build

:: Сборка
echo.
echo [3/3] Сборка через Nuitka...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=tk-inter ^
    --include-package=customtkinter ^
    --include-data-dir=assets=assets ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=assets/logo.ico ^
    --output-filename=KiwiLabX00Team.exe ^
    --output-dir=build ^
    --company-name=X00Team ^
    --product-name="KiwiLab X00Team" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0.0 ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Сборка не удалась. Смотри лог выше.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Готово: build\KiwiLabX00Team.exe
echo ============================================
pause
