import os
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from tkinter import ttk
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageTk
from ttkthemes import ThemedTk
import random
import base64

# Корректные данные иконки
icon_base64 = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAC3FBMVEUAAAAAAAMFBQ0SERsSEhwSExwTEhwLDRgTEx0SEhwFBQ4AAAMHDD0AAAQiIiojIyoAAAEBAQsCAgsMDBcPDxgNDRgQEBoLDBcODhkMDRgODxkMDRgNDhkGBxMGCBQLDBcNDRgODxoKCxYLDBcAAAoAAAkAAAYVFiEXGCEAAAQAAAgAAAcCAg4BAg4CAg4CAg4BAQ0BAQ0CAg0DAgwCAQoCAgwAAAcAAAaPj5ShqrC0ur6osLaxt7x+kJt+kZuosba1ur6hqrGRkpaLjJH//v23pKnjubfIo6TYsK/Io6XHoqTXsK/HpKTkuLW6oqaQkZSqsLTIsbj3VFX9S0r+S0vbREN1Li90Li/ZQ0L+S0r9S0n3U1LIrbKvtbips7fOqLD6Mz7/Lzr6LThnFyF6foOAhIlkGCL4Ljj9Mzr4ND3NoqquuLywub3+y87+MDz/KTbIHilNO0Pl5+jp6utRQUnDHin/LTX8Mjz9x8q1vsGrtbncr7f8JjX+IDBzERyPkpaUlZmVmJxuER39IS/8JTXdq7Ouub2UoqmigJDiEyfHDyBKLTbGyctBMjo9LTXHystMMjvEDR/iECWjfIyXpq1MYnFqd4ZlQk0xFiGAfoShoqUMAwwLAgucnaCHhoowFSBkQEtpdYVNY3Slr7Pr+frO291GSVDR0dO7u76Cg4iCg4m4uLvU1NZER07M19rs+fuosrelrrPK3eSTmp9vb3TS09SWmZ2Wmp6WmZzS0tRwcXaRl5vL3OSosbiirLS6zNdQU1q6u71nXWRdAA55ABJ4ABJcAA1jWmBPUVe6ytSmsLinsbnC0NcmKTNRVFtAPErZgpTFYnXGYnXagpJAOkZSVFomKDDBzNSstb1yeILX6vVfd4pkgJV2l6zC2OGatMCas8DE1t17lKdpgJRidYjb6/V2fIRlbHd+ipeGkp+BjJiGkJxdaXheaXeJkJqFjZeKk52BipVrcHr///+xkUZOAAAAOHRSTlMAOKHDwsLCwsLDojoBNNXYPJekucC6wbnBucG6wbrBurnBt8CPminHzS8phqWlpqimpaelpqiJLUocXkgAAAABYktHRPOssb7uAAAAB3RJTUUH6AYHFTQvLkJRYwAAARtJREFUGNMBEAHv/gAAAQIDBAUGBwcECAQJCgsMAA0OODk6Ozw9Pjw/QEFCDxAAEUNERUZHSElKS0xNTkRPEgATUFFSU1RVVldYWVpbXF0UABVeX2BhYmNkZWZnaGlqaxYAF2xtbm9wcXJzdHV2d3h5GAAZent8fX5/gDiBgoOEhYYaABuHiImKi4yNjo+QkZKTlBwAHZWWl5iZmpucnZ6foKGiHgAfo6SlpqeoqaqrrK2ur7AcACCxsrO0tba3tri5uru8vSEAG76/wMHCw8TFxseoyMnKHAAiy8zNzs/Q0dLT1NXW19gjACTZ2tvc3d7f4OHi4+Tl5iUAJifn6Onq6+zt7u/w8fIoKQAAKissLS4vMDEyMzQ1NjcANGd1VIO/atgAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjQtMDYtMDdUMTg6NTI6NDcrMDM6MDDR7tdqAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI0LTA2LTA3VDE4OjUyOjQ3KzAzOjAwoLNv1gAAAABJRU5ErkJggg=='

# Глобальные переменные для хранения состояния
dataset = []
index = 0
total_images = 0
image_dir = ''
label_dir = ''
current_annotations = []
start_x = 0
start_y = 0
selected_boxes = set()  # Множество для хранения индексов выделенных боксов
classes = [""]  # Список классов по умолчанию с пустым классом
class_colors = {0: "red"}  # Цвет по умолчанию для класса 0
current_class_id = 0
shapes = []
scale = 1
new_width = 0
new_height = 0
contrast_levels = [1, 2, 4]  # Уровни контрастности
contrast_index = 0  # Начальный уровень контрастности (1.0)
current_shape = None  # Переменная для хранения текущей формы
class_info_window = None  # Окно настройки классов
class_selection_window = None  # Окно выбора класса
low_quality = False  # Переменная для переключения качества изображения
theme = "light"  # Текущая тема

# Объявляем глобальные переменные для frame и annotation_canvas
frame = None
annotation_canvas = None

def reset_state():
    global dataset, index, total_images, image_dir, label_dir, current_annotations, start_x, start_y, selected_boxes, classes, class_colors, current_class_id, contrast_index, current_shape, class_info_window, class_selection_window, low_quality, theme
    dataset = []
    index = 0
    total_images = 0
    image_dir = ''
    label_dir = ''
    current_annotations = []
    start_x = 0
    start_y = 0
    selected_boxes = set()
    classes = [""]
    class_colors = {0: "red"}
    current_class_id = 0
    contrast_index = 0
    current_shape = None
    class_info_window = None
    class_selection_window = None
    low_quality = False
    theme = "light"
    if 'image_info_label' in globals() and image_info_label.winfo_exists():
        image_info_label.config(text="Позиция: 0/0, Текущее изображение: N/A")

def load_dataset():
    global dataset, index, total_images, image_dir, label_dir, current_annotations
    
    directory = filedialog.askdirectory()
    if not directory:
        return
    
    reset_state()
    
    image_dir = directory
    label_dir = os.path.join(os.path.dirname(directory), "labels")
    os.makedirs(label_dir, exist_ok=True)
    
    dataset = [os.path.join(image_dir, f)
               for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    total_images = len(dataset)
    index = 0
    current_annotations = []
    
    if dataset:
        show_image()
        update_image_info()
        annotation_canvas.config(state=tk.NORMAL)  # Разблокировать поле после загрузки датасета
    else:
        messagebox.showerror("Ошибка", "No images found in the specified directory.")
        image_info_label.config(text="Позиция: 0/0, Текущее изображение: N/A")
        annotation_canvas.config(state=tk.DISABLED)  # Оставить поле заблокированным

def draw_boxes(image, annotation_list, selected_boxes):
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial", 15)
    except IOError:
        font = ImageFont.load_default()
    
    for i, annotation in enumerate(annotation_list):
        if len(annotation) != 5:
            continue
        class_id, x_center, y_center, width, height = map(float, annotation)
        img_width, img_height = image.size
        x_center *= img_width
        y_center *= img_height
        width *= img_width
        height *= img_height
        x1 = x_center - width / 2
        y1 = y_center - height / 2
        x2 = x_center + width / 2
        y2 = y_center + height / 2
        outline_color = class_colors.get(int(class_id), "red")
        if i in selected_boxes:
            outline_color = "blue"
        draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)
        if int(class_id) < len(classes):
            draw.text((x1, y1), f"{int(class_id)}: {classes[int(class_id)]}", fill=outline_color, font=font)
    
    return image

def show_image():
    global index, dataset, label_dir, img_path, selected_boxes, tk_img, annotation_canvas, shapes, scale, new_width, new_height, low_quality
    
    img_path = dataset[index]
    image = Image.open(img_path)

    # Применение контрастности
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast_levels[contrast_index])

    annotation_path = os.path.join(label_dir, os.path.basename(img_path).replace(".jpg", ".txt"))
    if os.path.exists(annotation_path):
        with open(annotation_path, 'r') as file:
            annotation_text = file.read().strip().split('\n')
        annotation_list = [line.split() for line in annotation_text]
    else:
        annotation_list = []
    
    selected_boxes.clear()
    shapes = []
    img_width, img_height = image.size
    canvas_width = annotation_canvas.winfo_width()
    canvas_height = annotation_canvas.winfo_height()
    scale = min(canvas_width/img_width, canvas_height/img_height)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    for annotation in annotation_list:
        if len(annotation) == 5:
            class_id, x_center, y_center, width, height = map(float, annotation)
            x_center *= new_width
            y_center *= new_height
            width *= new_width
            height *= new_height
            x1 = x_center - width / 2
            y1 = y_center - height / 2
            x2 = x_center + width / 2
            y2 = y_center + height / 2
            shapes.append((x1, y1, x2, y2, int(class_id)))
    
    tk_img = ImageTk.PhotoImage(image)
    annotation_canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    annotation_canvas.config(scrollregion=annotation_canvas.bbox(tk.ALL))
    refresh_canvas()
    update_image_info()

def next_image(event=None):
    global index, total_images
    if index < total_images - 1:
        save_annotations()
        index += 1
        show_image()
        update_image_info()

def previous_image(event=None):
    global index
    if index > 0:
        save_annotations()
        index -= 1
        show_image()
        update_image_info()

def update_image_info():
    global index, dataset
    if index < len(dataset):
        if 'image_info_label' in globals() and image_info_label.winfo_exists():
            image_info_label.config(text=f"Позиция: {index + 1}/{total_images}, Текущее изображение: {os.path.basename(dataset[index])}")

def load_class_file():
    global classes, class_colors
    file_path = filedialog.askopenfilename(title="Выбрать файл классов", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                classes = [line.strip() for line in file.readlines()]
            class_colors = {i: "#%06x" % random.randint(0, 0xFFFFFF) for i in range(len(classes))}
            messagebox.showinfo("Классы загружены", f"Классы: {classes}")
            refresh_display()  # Добавляем обновление отображения после загрузки классов
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить классы: {e}")
    else:
        messagebox.showwarning("Предупреждение", "Файл классов не выбран. Используются текущие классы.")

def refresh_display():
    if dataset:
        show_image()
        update_image_info()



def show_class_info():
    global classes, class_colors, class_info_window
    if class_info_window is not None and class_info_window.winfo_exists():
        return

    class_info_window = tk.Toplevel(root)
    class_info_window.title("Информация о классах")
    class_info_window.attributes('-topmost', True)  # Always on top
    class_info_window.focus_force()  # Bring to front and make active

    def close_window(event=None):
        class_info_window.destroy()

    class_info_window.bind("<Escape>", close_window)  # Bind Esc to close

    frame = ttk.Frame(class_info_window)
    frame.pack(fill=tk.BOTH, expand=True)
    
    tree = ttk.Treeview(frame, columns=("ID", "Класс"), show='headings', height=10)
    tree.column("ID", width=50, anchor='center')
    tree.column("Класс", anchor='center')
    tree.heading("ID", text="ID")
    tree.heading("Класс", text="Класс")

    for i, cls in enumerate(classes):
        tree.insert("", "end", values=(i, cls), tags=(i,))
    
    for i in range(len(classes)):
        tree.tag_configure(str(i), background=class_colors[i])
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    tree.configure(yscrollcommand=scrollbar.set)

    def change_color(event):
        item = tree.selection()[0]
        class_id = int(tree.item(item, "values")[0])
        class_info_window.attributes('-topmost', False)  # Temporarily disable always on top for class_info_window
        color = colorchooser.askcolor(title="Выберите цвет")[1]
        class_info_window.attributes('-topmost', True)  # Re-enable always on top for class_info_window
        class_info_window.focus_force()  # Bring to front and make active again
        if color:
            class_colors[class_id] = color
            tree.tag_configure(str(class_id), background=color)
            refresh_canvas()
            class_info_window.attributes('-topmost', True)  # Ensure window stays on top
            class_info_window.focus_force()  # Bring to front and make active

    tree.bind("<Double-1>", change_color)

    # Установка темы для окна class_info_window
    apply_theme_to_window(class_info_window)

    class_info_window.mainloop()
    






def clear_annotations():
    global current_annotations, label_dir, index, dataset
    current_annotations = []
    if index < len(dataset):
        annotation_path = os.path.join(label_dir, os.path.basename(dataset[index]).replace(".jpg", ".txt"))
        with open(annotation_path, 'w') as file:
            file.write("")
    show_image()
    update_image_info()

def jump_to_image(event=None):
    global index
    try:
        idx = int(image_number_entry.get()) - 1
        if 0 <= idx < total_images:
            save_annotations()
            index = idx
            show_image()
            update_image_info()
        else:
            messagebox.showerror("Ошибка", "Номер изображения вне диапазона.")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный номер изображения.")

def validate_number(P):
    if P.isdigit() or P == "":
        return True
    return False

def on_mouse_down(event):
    global start_x, start_y, current_shape
    if event.state & 0x0004 or event.num == 3:  # Проверяем, что Ctrl нажат или это ПКМ
        select_box(event.x, event.y)
    else:
        start_x = min(max(event.x, 0), new_width)
        start_y = min(max(event.y, 0), new_height)
        current_shape = annotation_canvas.create_rectangle(start_x, start_y, start_x, start_y, outline=class_colors.get(current_class_id, 'red'))


def on_mouse_up(event):
    global start_x, start_y, current_shape, shapes
    if not (event.state & 0x0004):  # Проверяем, что Ctrl не нажат
        end_x = min(max(event.x, 0), new_width)
        end_y = min(max(event.y, 0), new_height)
        # Проверяем размеры бокса
        if abs(end_x - start_x) > 0 and abs(end_y - start_y) > 0:
            shapes.append((start_x, start_y, end_x, end_y, current_class_id))
        else:
            annotation_canvas.delete(current_shape)
        current_shape = None
        save_annotations()
        refresh_canvas()

def on_mouse_move(event):
    global start_x, start_y, current_shape
    if current_shape is not None:
        end_x = min(max(event.x, 0), new_width)
        end_y = min(max(event.y, 0), new_height)
        annotation_canvas.coords(current_shape, start_x, start_y, end_x, end_y)

def save_annotations():
    global current_annotations, shapes, label_dir, index, dataset, annotation_canvas, scale
    
    current_annotations = []
    for shape in shapes:
        x1, y1, x2, y2, class_id = shape
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        if width == 0 or height == 0:
            continue  # Пропускаем боксы с нулевым размером
        x_center = ((x1 + x2) / 2) / new_width
        y_center = ((y1 + y2) / 2) / new_height
        width /= new_width
        height /= new_height
        x_center = min(max(x_center, 0), 1)
        y_center = min(max(y_center, 0), 1)
        width = min(max(width, 0), 1)
        height = min(max(height, 0), 1)
        current_annotations.append([int(class_id), x_center, y_center, width, height])
    
    if index < len(dataset):
        annotation_path = os.path.join(label_dir, os.path.basename(dataset[index]).replace(".jpg", ".txt"))
        with open(annotation_path, 'w') as file:
            for ann in current_annotations:
                file.write(" ".join(map(str, ann)) + "\n")
    
    update_image_info()

def select_box(x, y):
    global selected_boxes
    for i, (x1, y1, x2, y2, class_id) in enumerate(shapes):
        if x1 <= x <= x2 and y1 <= y <= y2:
            if i in selected_boxes:
                selected_boxes.remove(i)
            else:
                selected_boxes.add(i)
            refresh_canvas()  # Ensure the canvas is refreshed to show selection
            return
    refresh_canvas()


def on_delete(event):
    global selected_boxes, shapes
    shapes = [shape for i, shape in enumerate(shapes) if i not in selected_boxes]
    selected_boxes.clear()
    save_annotations()
    refresh_canvas()



def change_class(event=None):
    global class_selection_window
    if class_selection_window is not None and class_selection_window.winfo_exists():
        return

    def set_class():
        global current_class_id, selected_boxes
        new_class_id = class_combobox.current()
        if selected_boxes:
            for box_index in selected_boxes:
                x1, y1, x2, y2, _ = shapes[box_index]
                shapes[box_index] = (x1, y1, x2, y2, new_class_id)
            current_class_id = new_class_id  # Обновляем текущий класс
            selected_boxes.clear()
            save_annotations()
        else:
            current_class_id = new_class_id
        class_selection_window.destroy()
        refresh_canvas()

    class_selection_window = tk.Toplevel(root)
    class_selection_window.title("Выбор класса")
    class_selection_window.attributes('-topmost', True)  # Always on top
    class_selection_window.focus_force()  # Bring to front and make active

    def close_window(event=None):
        class_selection_window.destroy()

    class_selection_window.bind("<Escape>", close_window)  # Bind Esc to close

    class_label = ttk.Label(class_selection_window, text="Выберите класс:")
    class_label.pack(side=tk.LEFT, padx=5, pady=5)

    class_combobox = ttk.Combobox(class_selection_window, values=classes, state="readonly")
    class_combobox.pack(side=tk.LEFT, padx=5, pady=5)
    class_combobox.current(current_class_id)

    select_button = ttk.Button(class_selection_window, text="Выбрать", command=set_class)
    select_button.pack(side=tk.LEFT, padx=5, pady=5)

    class_selection_window.bind("<Return>", lambda e: set_class())

    # Установка темы для окна class_selection_window
    apply_theme_to_window(class_selection_window)



def show_other_popup():
    other_popup_window = tk.Toplevel(root)
    other_popup_window.title("Other Settings")
    other_popup_window.attributes('-topmost', True)  # Always on top
    other_popup_window.focus_force()  # Bring to front and make active

    def close_window(event=None):
        other_popup_window.destroy()

    other_popup_window.bind("<Escape>", close_window)  # Bind Esc to close

    # Add other content and widgets to this window here

    other_popup_window.mainloop()




def refresh_canvas():
    annotation_canvas.delete("all")
    annotation_canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    for i, shape in enumerate(shapes):
        outline_color = "blue" if i in selected_boxes else class_colors.get(int(shape[4]), 'red')
        annotation_canvas.create_rectangle(shape[0], shape[1], shape[2], shape[3], outline=outline_color)
        if int(shape[4]) < len(classes):
            annotation_canvas.create_text(shape[0], shape[1], anchor=tk.NW, text=f"{int(shape[4])}: {classes[int(shape[4])]}", fill=class_colors.get(int(shape[4]), 'red'))

    
def show_class_label():
    class_label = tk.Label(root, text=f"Текущий класс: {current_class_id}: {classes[current_class_id]}", bg="yellow")
    class_label.place(relx=0.5, rely=0, anchor='n')

    def hide_class_label():
        class_label.destroy()

    root.after(2000, hide_class_label)

def increase_contrast():
    global contrast_index
    if contrast_index < len(contrast_levels) - 1:
        contrast_index += 1
    refresh_display()

def decrease_contrast():
    global contrast_index
    if contrast_index > 0:
        contrast_index -= 1
    refresh_display()

def set_dark_theme_styles():
    global style
    style.theme_use("clam")
    style.configure('TButton', background='#444444', foreground='#ffffff', borderwidth=1, relief='flat')
    style.map('TButton', background=[('active', '#666666')], foreground=[('active', '#000000')])
    style.configure('TLabel', background='#333333', foreground='#ffffff')
    style.configure('TEntry', fieldbackground='#333333', foreground='#ffffff')
    style.configure('TFrame', background='#333333')
    style.configure('TCombobox', fieldbackground='#333333', foreground='#ffffff')
    style.configure('TScrollbar', background='#444444')
    # Set the background color of the main frame and canvas
    if frame and annotation_canvas:
        frame.config(style='TFrame')
        annotation_canvas.config(background='#333333')

def set_light_theme_styles():
    global style
    style.theme_use("clam")
    style.configure('TButton', background='#f0f0f0', foreground='#000000', borderwidth=1, relief='flat')
    style.map('TButton', background=[('active', '#e0e0e0')], foreground=[('active', '#000000')])
    style.configure('TLabel', background='#ffffff', foreground='#000000')
    style.configure('TEntry', fieldbackground='#ffffff', foreground='#000000')
    style.configure('TFrame', background='#ffffff')
    style.configure('TCombobox', fieldbackground='#ffffff', foreground='#000000')
    style.configure('TScrollbar', background='#f0f0f0')
    # Set the background color of the main frame and canvas
    if frame and annotation_canvas:
        frame.config(style='TFrame')
        annotation_canvas.config(background='#ffffff')

def apply_theme_to_window(window):
    if theme == "light":
        window.configure(bg='#ffffff')
        for child in window.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(background='#ffffff', foreground='#000000')
            elif isinstance(child, ttk.Button):
                child.configure(style='TButton')
            elif isinstance(child, ttk.Frame):
                child.configure(style='TFrame')
            elif isinstance(child, ttk.Combobox):
                child.configure(style='TCombobox')
            elif isinstance(child, tk.Canvas):
                child.configure(bg='#ffffff')
    else:
        window.configure(bg='#333333')
        for child in window.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(background='#333333', foreground='#ffffff')
            elif isinstance(child, ttk.Button):
                child.configure(style='TButton')
            elif isinstance(child, ttk.Frame):
                child.configure(style='TFrame')
            elif isinstance(child, ttk.Combobox):
                child.configure(style='TCombobox')
            elif isinstance(child, tk.Canvas):
                child.configure(bg='#333333')

def toggle_theme():
    global theme
    if theme == "light":
        set_dark_theme_styles()
        theme = "dark"
    else:
        set_light_theme_styles()
        theme = "light"
    refresh_display()

root = ThemedTk(theme="breeze")
root.title("Anno PE: Программа для аннотирования изображений")
root.state('normal')
root.minsize(1354, 600)

# Устанавливаем иконку
icon_data = base64.b64decode(icon_base64)
icon_image = tk.PhotoImage(data=icon_data)
root.iconphoto(True, icon_image)

# Установить современный стиль
style_options = {"padx": 10, "pady": 10}
style = ttk.Style()
frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

top_frame = ttk.Frame(frame)
top_frame.pack(fill=tk.X, **style_options)

directory_button = ttk.Button(top_frame, text="Выбрать папку", command=load_dataset)
directory_button.pack(side=tk.LEFT, padx=5)

class_label = ttk.Label(top_frame, text="  Настройки классов:")
class_label.pack(side=tk.LEFT, padx=5)
class_button = ttk.Button(top_frame, text="Загрузить файл классов", command=load_class_file)
class_button.pack(side=tk.LEFT, padx=5)

show_class_info_button = ttk.Button(top_frame, text="Показать классы", command=show_class_info)
show_class_info_button.pack(side=tk.LEFT, padx=5)

annot_label = ttk.Label(top_frame, text="  Настройки аннотирования:")
annot_label.pack(side=tk.LEFT, padx=5)

refresh_button = ttk.Button(top_frame, text="Обновить", command=refresh_display)
refresh_button.pack(side=tk.LEFT, padx=5)

clear_button = ttk.Button(top_frame, text="Очистить", command=clear_annotations)
clear_button.pack(side=tk.LEFT, padx=5)

theme_button = ttk.Button(top_frame, text="Переключить тему", command=toggle_theme)
theme_button.pack(side=tk.LEFT, padx=5)

# Добавить счетчик изображений и поле ввода номера изображения
counter_frame = ttk.Frame(top_frame)
counter_frame.pack(side=tk.LEFT, padx=5)

image_number_label = ttk.Label(counter_frame, text="Номер изображения:")
image_number_label.pack(side=tk.LEFT)

validate_command = root.register(validate_number)
image_number_entry = ttk.Entry(counter_frame, width=5, validate="key", validatecommand=(validate_command, '%P'))
image_number_entry.pack(side=tk.LEFT)
image_number_entry.bind("<Return>", jump_to_image)

jump_button = ttk.Button(counter_frame, text="Перейти", command=jump_to_image)
jump_button.pack(side=tk.LEFT, padx=5)

info_frame = ttk.Frame(frame)
info_frame.pack(fill=tk.X, **style_options)

image_info_label = ttk.Label(info_frame, text="Позиция: 0/0, Текущее изображение: N/A")
image_info_label.pack(side=tk.LEFT, padx=5)

main_frame = ttk.Frame(frame)
main_frame.pack(fill=tk.BOTH, expand=True)

# Поле для аннотирования
annotation_frame = ttk.Frame(main_frame, height=100)
annotation_frame.pack(fill=tk.BOTH, expand=True, **style_options)

annotation_canvas = tk.Canvas(annotation_frame, bg="white")
annotation_canvas.pack(fill=tk.BOTH, expand=True)

# Устанавливаем тему после создания всех элементов
set_light_theme_styles()

annotation_canvas.bind("<ButtonPress-1>", on_mouse_down)
annotation_canvas.bind("<ButtonPress-3>", on_mouse_down)  # Binding for Right Click
annotation_canvas.bind("<ButtonRelease-1>", on_mouse_up)
annotation_canvas.bind("<Motion>", on_mouse_move)

def _onKeyRelease(event):
    ctrl = (event.state & 0x4) != 0
    if ctrl and (chr(event.keycode) in ['V', 'М']):  # V key in English and Russian
        root.focus_get().event_generate("<<Paste>>")
    if ctrl and (chr(event.keycode) in ['C', 'С']):  # C key in English and Russian
        root.focus_get().event_generate("<<Copy>>")
    if ctrl and (chr(event.keycode) in ['X', 'Ч']):  # X key in English and Russian
        root.focus_get().event_generate("<<Cut>>")
    if ctrl and (chr(event.keycode) in ['A', 'Ф']):  # A key in English and Russian
        root.focus_get().event_generate("<<SelectAll>>")
    if chr(event.keycode) in ['R', 'К']:  # R key in English and Russian
        refresh_display()
    if event.keycode == 37:  # Left arrow key
        previous_image()
    if event.keycode == 39:  # Right arrow key
        next_image()
    if event.keycode in [61, 187, 171]:  # Plus key (+) in different layouts
        increase_contrast()
    if event.keycode in [45, 189, 173]:  # Minus key (-) in different layouts
        decrease_contrast()
    if event.keycode == 16:  # Tab key
        change_class(event)
    if event.keycode == 8:  # Backspace key
        on_delete(event)
    if chr(event.keycode) in ['T', 'Е']:  # T key in English and Russian
        toggle_theme()

# Bind all key press events to the _onKeyRelease function
root.bind_all("<KeyRelease>", _onKeyRelease, "+")



root.bind("<MouseWheel>", lambda event: next_image() if event.delta < 0 else previous_image())



root.mainloop()
