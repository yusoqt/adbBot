import tkinter as tk
from tkinter import ttk
import pygetwindow as gw
import pyautogui
import threading
import time


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Position Detector")

        self.selected_window = None
        self.running = False

        # Dropdown
        ttk.Label(root, text="เลือกหน้าต่างแอป:").pack(pady=5)
        self.combo = ttk.Combobox(root, width=50, state="readonly")
        self.combo.pack(pady=5)

        # Refresh button
        ttk.Button(root, text="Refresh รายการแอป", command=self.refresh_windows).pack(pady=5)

        # Start button
        ttk.Button(root, text="Start Tracking", command=self.start_tracking).pack(pady=10)

        # Display result
        self.label = ttk.Label(root, text="ตำแหน่ง: - , -", font=("Arial", 14))
        self.label.pack(pady=20)

        # Load windows on startup
        self.refresh_windows()

    def refresh_windows(self):
        windows = gw.getAllWindows()

        titles = [w.title for w in windows if w.title.strip()]
        self.windows_map = {w.title: w for w in windows if w.title.strip()}

        self.combo["values"] = titles
        if titles:
            self.combo.current(0)

    def start_tracking(self):
        title = self.combo.get()
        if title not in self.windows_map:
            self.label.config(text="ไม่พบหน้าต่าง!")
            return

        self.selected_window = self.windows_map[title]
        self.running = True

        threading.Thread(target=self.track_mouse, daemon=True).start()

    def track_mouse(self):
        while self.running:
            win = self.selected_window

            # ตำแหน่ง global
            mx, my = pyautogui.position()

            # ตำแหน่งหน้าต่าง
            local_x = mx - win.left
            local_y = my - win.top

            self.label.config(text=f"ตำแหน่งในแอป: x={local_x}  y={local_y}")

            time.sleep(0.02)


root = tk.Tk()
App(root)
root.mainloop()
