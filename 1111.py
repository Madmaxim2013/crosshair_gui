import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import ctypes
import winsound
import time
import colorsys
import uuid

# === Глобальные переменные ===
crosshair_window = None
canvas = None
current_color = "#00FF00"
current_size = 30
current_style = "Крестик"
crosshair_visible = False
rainbow_crosshair = False
rainbow_phase = 0
rainbow_loop_id = None

# === Звук с антиспамом ===
last_click_time = 0
click_delay = 0.3

def play_click():
    global last_click_time
    now = time.time()
    if now - last_click_time >= click_delay:
        last_click_time = now
        try:
            winsound.PlaySound("click.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            pass

def with_click(func):
    def wrapper(*args, **kwargs):
        play_click()
        return func(*args, **kwargs)
    return wrapper

# === Кликабельность окна ===
def make_window_clickthrough(hwnd):
    extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    new_style = extended_style | 0x80000 | 0x20
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)

# === Цвет прицела с эффектом радуги ===
def get_crosshair_color():
    global rainbow_phase
    if rainbow_crosshair:
        rainbow_phase += 0.005
        if rainbow_phase >= 1:
            rainbow_phase = 0
        r, g, b = colorsys.hsv_to_rgb(rainbow_phase, 1, 1)
        return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    return current_color

# === Отрисовка прицела ===
def draw_crosshair():
    global rainbow_phase, rainbow_loop_id
    if canvas is None:
        return

    size = current_size
    canvas.config(width=size, height=size)
    canvas.delete("all")
    cx, cy = size // 2, size // 2
    color = get_crosshair_color()

    if current_style == "Крестик":
        canvas.create_line(cx, 0, cx, size, fill=color, width=2)
        canvas.create_line(0, cy, size, cy, fill=color, width=2)
    elif current_style == "Точка":
        r = size // 10
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
    elif current_style == "Круг":
        r = size // 3
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2)

    if rainbow_crosshair:
        if rainbow_loop_id:
            canvas.after_cancel(rainbow_loop_id)
        rainbow_loop_id = canvas.after(30, draw_crosshair)

# === Показать прицел ===
@with_click
def show_crosshair():
    global crosshair_window, canvas, crosshair_visible
    if crosshair_visible:
        return
    crosshair_visible = True
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = screen_width // 2
    center_y = screen_height // 2

    crosshair_window = tk.Toplevel()
    crosshair_window.overrideredirect(True)
    crosshair_window.attributes("-topmost", True)
    crosshair_window.attributes("-transparentcolor", "black")
    crosshair_window.config(bg="black")

    size = current_size
    crosshair_window.geometry(f"{size}x{size}+{center_x - size//2}+{center_y - size//2}")
    crosshair_window.update_idletasks()

    hwnd = ctypes.windll.user32.FindWindowW(None, crosshair_window.title())
    if hwnd:
        make_window_clickthrough(hwnd)

    canvas = tk.Canvas(crosshair_window, width=size, height=size, bg="black", highlightthickness=0)
    canvas.pack()
    draw_crosshair()

# === Скрыть прицел ===
@with_click
def hide_crosshair():
    global crosshair_window, canvas, crosshair_visible, rainbow_loop_id
    if not crosshair_visible:
        return
    if crosshair_window:
        if rainbow_loop_id:
            canvas.after_cancel(rainbow_loop_id)
            rainbow_loop_id = None
        crosshair_window.destroy()
        crosshair_window = None
        canvas = None
        crosshair_visible = False

# === Изменение размера ===
def update_size(val):
    global current_size
    current_size = int(float(val))
    if crosshair_window:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = screen_width // 2
        center_y = screen_height // 2
        crosshair_window.geometry(f"{current_size}x{current_size}+{center_x - current_size//2}+{center_y - current_size//2}")
    draw_crosshair()

# === Цвет прицела ===
@with_click
def choose_color():
    global current_color
    color = colorchooser.askcolor(title="Выбери цвет прицела")
    if color[1]:
        current_color = color[1]
        draw_crosshair()

# === Стиль прицела ===
@with_click
def change_style(event=None):
    global current_style
    current_style = style_var.get()
    draw_crosshair()

# === Главное окно ===
root = tk.Tk()
root.title("🎯 CS2 Crosshair Config")
root.geometry("600x400")
root.configure(bg="black")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")
style.configure(".", background="#0f1117", foreground="#ffffff", font=('Segoe UI', 10))
style.configure("TButton", background="#1c1f26", foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
style.map("TButton", background=[("active", "#292d36")])
style.configure("TLabel", background="#0f1117", foreground="#bbbbbb")
style.configure("TCheckbutton", background="#0f1117", foreground="#ffffff")
style.configure("TScale", background="#0f1117")
style.configure("TCombobox", fieldbackground="#1c1f26", background="#1c1f26", foreground="#ffffff", arrowcolor="#ffffff")

# === Анимация текста ===
def animate_text(label, text, index=0):
    if index <= len(text):
        label.config(text=text[:index])
        root.after(80, lambda: animate_text(label, text, index + 1))

# === Заставка ===
def show_intro_and_launch():
    for widget in root.winfo_children():
        widget.destroy()

    title_label = tk.Label(root, text="", font=("Segoe UI", 24, "bold"), fg="white", bg="black")
    title_label.place(relx=0.5, rely=0.4, anchor="center")
    animate_text(title_label, "🔫 MAX AIM LAUNCHER")

    dot_label = tk.Label(root, text="", font=("Segoe UI", 18), fg="white", bg="black")
    dot_label.place(relx=0.5, rely=0.55, anchor="center")

    dots = ["", ".", "..", "..."]
    index = [0]

    def animate_dots():
        try:
            index[0] = (index[0] + 1) % len(dots)
            dot_label.config(text="Загрузка" + dots[index[0]])
            root.after(300, animate_dots)
        except tk.TclError:
            pass

    def launch_main_ui():
        for widget in root.winfo_children():
            widget.destroy()
        launch_main_interface()

    root.after(1000, animate_dots)
    root.after(4000, launch_main_ui)

# === Основной интерфейс ===
def launch_main_interface():
    root.geometry("400x480")
    root.configure(bg="#0f1117")

    ttk.Label(root, text="🎮 CROSSHAIR MANAGER", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))

    delay = 0
    def delay_pack(widget, delay_ms, **kwargs):
        root.after(delay_ms, lambda: widget.pack(**kwargs))

    global style_var
    style_var = tk.StringVar(value=current_style)

    delay_pack(ttk.Button(root, text="Показать прицел", command=with_click(show_crosshair)), delay := delay + 100, pady=6, fill="x", padx=40)
    delay_pack(ttk.Button(root, text="Скрыть прицел", command=with_click(hide_crosshair)), delay := delay + 100, pady=6, fill="x", padx=40)
    delay_pack(ttk.Button(root, text="Цвет прицела", command=with_click(choose_color)), delay := delay + 100, pady=6, fill="x", padx=40)

    delay_pack(ttk.Label(root, text="📏 Размер прицела"), delay := delay + 100, pady=(12, 0))
    delay_pack(ttk.Scale(root, from_=10, to=200, orient="horizontal", command=update_size), delay := delay + 100, padx=30, fill="x")

    delay_pack(ttk.Label(root, text="🧬 Стиль прицела"), delay := delay + 100, pady=(12, 0))
    style_box = ttk.Combobox(root, textvariable=style_var, values=["Крестик", "Точка", "Круг"], state="readonly")
    style_box.bind("<<ComboboxSelected>>", change_style)
    delay_pack(style_box, delay := delay + 100, padx=30, fill="x")

    def toggle_rainbow():
        global rainbow_crosshair
        rainbow_crosshair = rainbow_var.get()
        draw_crosshair()

    rainbow_var = tk.BooleanVar(value=rainbow_crosshair)
    rainbow_chk = ttk.Checkbutton(root, text="🌈 Разноцветный прицел", variable=rainbow_var, command=toggle_rainbow)
    delay_pack(rainbow_chk, delay := delay + 100, pady=(30, 10))

# === Проверка лицензионного ключа ===
def check_license_and_continue():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="🔑 Введите лицензионный ключ", font=("Segoe UI", 14, "bold"), fg="white", bg="black").pack(pady=(30, 10))
    key_entry = tk.Entry(root, font=("Segoe UI", 12), width=30)
    key_entry.pack(pady=10)

    info_label = tk.Label(root, text="Ключ можно получить у @yourbot", font=("Segoe UI", 10), fg="#bbbbbb", bg="black")
    info_label.pack(pady=(5, 20))

    def validate_key():
        user_key = key_entry.get().strip()
        machine_id = str(uuid.getnode())
        try:
            import requests
            response = requests.post("http://localhost:8000/check", json={"key": user_key, "machine_id": machine_id}, timeout=5)
            result = response.json()
            if result.get("valid", False):
                show_intro_and_launch()
            else:
                messagebox.showerror("Ошибка", result.get("message", "Неверный ключ"))
        except Exception:
            messagebox.showerror("Ошибка", "Нет подключения к серверу. Проверьте интернет.")

    ttk.Button(root, text="Активировать", command=validate_key).pack(pady=10)

check_license_and_continue()
root.mainloop()
