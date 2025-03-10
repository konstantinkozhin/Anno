# Anno OCR

**Anno OCR** – это программа для разметки изображений с последующей расшифровкой. Программа позволяет быстро создавать, редактировать и удалять bounding box’ы (области интереса) на изображениях, а также задавать для них расшифровки. Все аннотации сохраняются в базе данных SQLite и могут быть экспортированы в CSV.

https://github.com/user-attachments/assets/f53cf13e-c37e-4e42-9d15-2f5c82b385e7

<details>
  <summary>Основные возможности</summary>

  - **Загрузка изображений:**
    - Выбор папки с изображениями (файлы с расширением `.jpg`).
    - Автоматическая работа с базой данных (`annotations.db`) в выбранной папке.

  - **Создание и редактирование bounding box’ов:**
    - Рисование нового бокса при помощи ЛКМ (если не включён режим редактирования).
    - Режим редактирования (включается кнопкой *Edit Boxes* или сочетанием `Ctrl+E`):
      - Ручки (синие квадратики) позволяют изменять размеры бокса.
      - При клике по пустому месту (без бокса) режим редактирования автоматически выключается.
      - После изменения размера данные обновляются и отражаются в панели расшифровок.

  - **Панель расшифровок и обрезков:**
    - Панель, отображающая вырезанные фрагменты (cropped images) из боксов и соответствующие поля ввода для расшифровки.
    - Панель по умолчанию скрыта и открывается по кнопке *Toggle Decoding Panel* или сочетанием `Ctrl+D`.
    - Панель открывается с соотношением 75% для изображения и 25% для панели, а после любых изменений обновляется автоматически.
    - Размер шрифта полей ввода можно задавать в настройках.

  - **Масштабирование:**
    - Масштабирование изображения с помощью колёсика мыши при зажатом `Ctrl`.
    - Стандартные кнопки зума (➕ и ➖).

  - **Навигация:**
    - Перелистывание изображений с помощью кнопок или горячих клавиш:
      - `Ctrl+Left` и `Ctrl+Right` переключают изображения (однократное нажатие).

  - **Горячие клавиши для быстрого ввода:**
    - Сочетания `Ctrl+1` .. `Ctrl+5` позволяют вставлять заданные строки или символы в поля ввода расшифровок.
    - Тексты для горячих клавиш настраиваются через окно настроек.

  - **Настройки:**
    - В настройках можно изменить:
      - Толщину и цвет линий боксов.
      - Размер и цвет уголков (ручек) для редактирования.
      - Размер шрифта в полях ввода расшифровок.
      - Тексты для горячих клавиш `Ctrl+1` … `Ctrl+5`.
    - Все настройки сохраняются в файле `config.json`, который создаётся рядом с exe.

  - **Экспорт аннотаций:**
    - Экспорт всех аннотаций в CSV файл с колонками:
      - `image_name, x_center, y_center, width, height, class_id, decoding`.
</details>

<details>
  <summary>Как использовать</summary>

1. **Запустите Anno OCR** (например, запустив скомпилированный exe-файл).
2. **Выберите папку** с изображениями через меню *File → Select Folder*.
3. **Навигация:**  
   - Используйте кнопки (🡰 / 🡲) или поле **Select Page** для перехода между изображениями.
   - Горячие клавиши `Ctrl+Left` и `Ctrl+Right` также переключают изображения.
4. **Создание бокса:**  
   - Если режим редактирования выключен, нажмите ЛКМ на изображении и тяните для создания нового бокса.
5. **Редактирование боксов:**  
   - Включите режим редактирования (кнопка *Edit Boxes* или `Ctrl+E`).
   - Изменяйте размеры бокса, перетаскивая синие ручки.  
   - Для выхода из режима редактирования нажмите ЛКМ по пустому месту на изображении.
6. **Панель расшифровок:**  
   - Включите панель с помощью кнопки *Toggle Decoding Panel* или `Ctrl+D`.
   - Панель будет отображать обрезки боксов и поля для ввода расшифровок. При изменении настроек или боксов панель обновляется автоматически.
7. **Настройки:**  
   - В меню *File → Settings* можно задать параметры:
     - Толщина и цвет линий боксов.
     - Размер и цвет уголков.
     - Размер шрифта полей ввода.
     - Горячие клавиши для вставки текста.
8. **Экспорт:**  
   - Для экспорта аннотаций в CSV выберите *File → Export to CSV*.
</details>

## Скачать

Вы можете скачать программу "Anno OCR" и "Anno MCL" по следующей ссылке:

[Скачать](https://drive.google.com/drive/folders/1K4D0LPNx1idc5h0YMJ1rPYqewmyKZC39?usp=drive_link)
