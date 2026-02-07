@echo off
chcp 65001 >nul 2>&1
title OCR Tool — PyInstaller Build
echo ══════════════════════════════════════════════
echo   OCR Tool — сборка в один .exe
echo ══════════════════════════════════════════════

:: ── Activate venv if it exists ──
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo [OK] Виртуальное окружение активировано
) else (
    echo [!]  .venv не найден — используется системный Python
)

:: ── Check / install PyInstaller ──
python -m PyInstaller --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*]  Установка PyInstaller ...
    pip install pyinstaller
)
echo [OK] PyInstaller найден

:: ── Build ──
echo.
echo [*]  Запуск сборки ...
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "OCR_Tool" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "sqlite3" ^
    --collect-submodules "ocr_tool" ^
    run.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ОШИБКА] Сборка завершилась с ошибкой!
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════
echo   ГОТОВО!
echo   Файл: dist\OCR_Tool.exe
echo ══════════════════════════════════════════════
echo.
pause
