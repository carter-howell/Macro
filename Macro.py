import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog
import keyboard
import json
from PIL import Image, ImageDraw
import pystray

QUEUE_FILE = 'hotkey_queue.json'


class FolderHotkeyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Hotkey Opener")

        self.root.withdraw()

        self.hotkey_queue = self.load_queue()

        self.folder_label = tk.Label(root, text="Folder Path:")
        self.folder_label.grid(row=0, column=0, padx=10, pady=10)

        self.folder_path = tk.Entry(root, width=50)
        self.folder_path.grid(row=0, column=1, padx=10, pady=10)

        self.browse_button = tk.Button(root, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        self.hotkey_label = tk.Label(root, text="Enter Hotkey:")
        self.hotkey_label.grid(row=1, column=0, padx=10, pady=10)

        self.hotkey_entry = tk.Entry(root, width=50)
        self.hotkey_entry.grid(row=1, column=1, padx=10, pady=10)
        self.hotkey_entry.insert(0, "ctrl+shift+a")

        self.add_button = tk.Button(root, text="Add to Queue", command=self.add_to_queue)
        self.add_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.queue_label = tk.Label(root, text="Hotkey Queue:")
        self.queue_label.grid(row=3, column=0, padx=10, pady=10)

        self.queue_listbox = tk.Listbox(root, width=50, height=10)
        self.queue_listbox.grid(row=3, column=1, padx=10, pady=10, columnspan=2)

        self.edit_button = tk.Button(root, text="Edit Selected", command=self.edit_selected)
        self.edit_button.grid(row=4, column=0, padx=10, pady=10)

        self.delete_button = tk.Button(root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.grid(row=4, column=1, padx=10, pady=10)

        self.start_button = tk.Button(root, text="Start All Hotkeys", command=self.set_all_hotkeys)
        self.start_button.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        self.status_label = tk.Label(root, text="Waiting for hotkey setup...", fg="blue")
        self.status_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

        self.update_queue_display()

        self.root.after(1000, self.minimize_on_startup)

        self.set_all_hotkeys()

        self.create_system_tray()

    def minimize_on_startup(self):
        self.root.withdraw()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.delete(0, tk.END)
            self.folder_path.insert(0, folder_selected)

    def add_to_queue(self):
        folder = self.folder_path.get()
        hotkey = self.hotkey_entry.get()

        if not self.validate_hotkey(hotkey):
            self.status_label.config(text="Invalid hotkey format. Use modifiers and a key (e.g., ctrl+shift+a).", fg="red")
            return

        if not folder:
            self.status_label.config(text="Please enter or select a folder path.", fg="red")
            return

        if not os.path.exists(folder):
            self.status_label.config(text="Folder path does not exist.", fg="red")
            return

        self.hotkey_queue.append((hotkey, folder))
        self.update_queue_display()
        self.save_queue()
        self.status_label.config(text=f"Added hotkey '{hotkey}' for folder.", fg="green")

    def validate_hotkey(self, hotkey):
        valid_modifiers = {'ctrl', 'alt', 'shift'}
        keys = [key.strip().lower() for key in hotkey.split('+')]

        if len(keys) < 2:
            return False

        if not any(key in valid_modifiers for key in keys[:-1]):
            return False

        if not keys[-1].isalnum() or len(keys[-1]) != 1:
            return False

        return True

    def edit_selected(self):
        selected_index = self.queue_listbox.curselection()
        if not selected_index:
            self.status_label.config(text="Please select a hotkey-folder pair from the queue to edit.", fg="red")
            return

        selected_index = selected_index[0]
        hotkey, folder = self.hotkey_queue[selected_index]

        self.folder_path.delete(0, tk.END)
        self.folder_path.insert(0, folder)
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, hotkey)

        self.delete_selected()
        self.status_label.config(text=f"Editing hotkey '{hotkey}' for folder.", fg="blue")

    def delete_selected(self):
        selected_index = self.queue_listbox.curselection()
        if not selected_index:
            self.status_label.config(text="Please select a hotkey-folder pair from the queue to delete.", fg="red")
            return

        selected_index = selected_index[0]

        self.hotkey_queue.pop(selected_index)
        self.queue_listbox.delete(selected_index)

        self.save_queue()
        self.status_label.config(text="Deleted selected hotkey-folder pair.", fg="green")

    def set_all_hotkeys(self):
        keyboard.clear_all_hotkeys()
        for hotkey, folder in self.hotkey_queue:
            keyboard.add_hotkey(hotkey, self.open_folder, args=[folder])
        self.status_label.config(text="All hotkeys are now active.", fg="green")

    def open_folder(self, folder):
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", folder])

    def update_queue_display(self):
        self.queue_listbox.delete(0, tk.END)
        for hotkey, folder in self.hotkey_queue:
            self.queue_listbox.insert(tk.END, f"Hotkey: {hotkey} -> Folder: {folder}")

    def save_queue(self):
        with open(QUEUE_FILE, 'w') as f:
            json.dump(self.hotkey_queue, f)

    def load_queue(self):
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f:
                return json.load(f)
        return []

    def load_icon(self):
        try:
            return Image.open("icon.png")
        except FileNotFoundError:
            icon_image = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(icon_image)
            draw.rectangle([12, 18, 52, 48], outline='black', fill='#2f81f7')
            draw.rectangle([12, 14, 32, 24], outline='black', fill='#79c0ff')
            return icon_image

    def create_system_tray(self):
        def on_quit(icon, item):
            self.root.quit()

        def show_window(icon, item):
            self.root.deiconify()
            self.root.after(100, self.root.lift)

        icon_image = self.load_icon()
        menu = (pystray.MenuItem('Show', show_window), pystray.MenuItem('Quit', on_quit))
        icon = pystray.Icon("FolderHotkeyApp", icon_image, menu=menu)
        icon.run_detached()

    def on_closing(self):
        if pystray:
            self.root.withdraw()
        else:
            self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderHotkeyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
