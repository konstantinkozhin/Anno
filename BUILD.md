# Сборка OCR Tool в один .exe

## Требования

- Python 3.11 (в `.venv`)
- PyQt6 (уже установлен)
- PyInstaller

## Быстрый способ

Просто запустите:

```
build.bat
```

Он сам:
1. Активирует `.venv`
2. Установит PyInstaller (если нет)
3. Соберёт `dist/OCR_Tool.exe`

---

## Ручная сборка

### 1. Установите PyInstaller

```bash
pip install pyinstaller
```

### 2. Соберите

```bash
pyinstaller --noconfirm --onefile --windowed ^
    --name "OCR_Tool" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "sqlite3" ^
    --collect-submodules "ocr_tool" ^
    run.py
```

### 3. Результат

```
dist/
  OCR_Tool.exe     ← единый исполняемый файл
```

---

## Структура проекта (для PyInstaller)

```
run.py                   ← точка входа (PyInstaller entry point)
ocr_tool/
  __init__.py
  __main__.py
  app.py                 ← главное окно
  theme.py               ← дизайн-система (тёмная/светлая тема)
  models/
    __init__.py
    data.py              ← Box, Line, Block
    database.py           ← SQLite (unified hierarchy)
  widgets/
    __init__.py
    base.py
    chips.py
    containers.py
    dialogs.py
    flow_layout.py
    panels.py
    viewer.py
  services/
    __init__.py
    export.py            ← JSON экспорт/импорт
```

PyInstaller находит все модули через `--collect-submodules "ocr_tool"`, поэтому
дополнительные `--hidden-import` для внутренних модулей **не нужны**.

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError: PyQt6` | `pip install PyQt6` в `.venv` |
| Антивирус блокирует `.exe` | Добавьте `dist/` в исключения |
| Большой размер `.exe` (~50 МБ) | Это нормально — PyQt6 включает все Qt-библиотеки |
| `.exe` долго запускается | Нормально для `--onefile` — идёт распаковка во временную папку |
| Нет шрифта Segoe UI | Приложение использует системный fallback |

## Альтернатива: --onedir (быстрее запуск)

```bash
pyinstaller --noconfirm --onedir --windowed ^
    --name "OCR_Tool" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "sqlite3" ^
    --collect-submodules "ocr_tool" ^
    run.py
```

Создаст `dist/OCR_Tool/OCR_Tool.exe` + папку с зависимостями.
Запуск быстрее, но нужно распространять всю папку.
