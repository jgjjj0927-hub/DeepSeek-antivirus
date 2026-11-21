import customtkinter as ctk
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class Splash(ctk.CTkToplevel):
    def __init__(self, master, on_done, duration_ms=2500):
        super().__init__(master)
        self.overrideredirect(True)
        self.geometry("420x260+{}+{}".format(
            (self.winfo_screenwidth() - 420) // 2,
            (self.winfo_screenheight() - 260) // 2))
        self.configure(fg_color="#0b1f12")

        self._img = None
        png = ASSETS / "kiwi.png"
        if png.exists():
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(png), size=(96, 96))
                self._img = img
                ctk.CTkLabel(self, image=img, text="").pack(pady=(28, 8))
            except Exception:
                pass

        ctk.CTkLabel(self, text="KiwiLab X00Team",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color="#3ddc84").pack(pady=4)
        ctk.CTkLabel(self, text="Инициализация защиты...",
                     font=ctk.CTkFont(size=12), text_color="#8fbf9f").pack(pady=2)

        self.progress = ctk.CTkProgressBar(self, width=320)
        self.progress.pack(pady=14)
        self.progress.set(0)
        self._duration = duration_ms
        self._step = 0
        self._on_done = on_done
        self.after(50, self._tick)

    def _tick(self):
        self._step += 50
        self.progress.set(min(1.0, self._step / self._duration))
        if self._step >= self._duration:
            self.destroy()
            self._on_done()
        else:
            self.after(50, self._tick)
