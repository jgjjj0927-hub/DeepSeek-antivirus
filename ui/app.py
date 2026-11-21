import customtkinter as ctk
from ui.splash import Splash
from ui.tabs import ScanTab, QuarantineTab, KeysTab, AboutTab
from core.config import load_config, save_config
from core.scanner import scan_system


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.withdraw()  # скрыть главное окно до сплэша
        ctk.set_appearance_mode(self.cfg.get("theme", "dark"))
        ctk.set_default_color_theme("green")
        self.title("KiwiLab X00Team")
        self.geometry("920x640")
        self.minsize(820, 580)
        self._build()
        self.after(100, self._show_splash)

    def _build(self):
        top = ctk.CTkFrame(self, height=48, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(top, text="🥝 KiwiLab X00Team🕊️",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.theme_btn = ctk.CTkButton(top, text="🌙", width=40, height=32, command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=4)

        self.tabs = ctk.CTkTabview(self, corner_radius=12)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
        t_scan = self.tabs.add("Сканер")
        t_quar = self.tabs.add("Карантин")
        t_keys = self.tabs.add("Ключи")
        t_about = self.tabs.add("О программе")

        ScanTab(t_scan).pack(fill="both", expand=True)
        QuarantineTab(t_quar).pack(fill="both", expand=True)
        KeysTab(t_keys, self.cfg).pack(fill="both", expand=True)
        AboutTab(t_about).pack(fill="both", expand=True)

    def _show_splash(self):
        Splash(self, on_done=self._after_splash, duration_ms=2200)

    def _after_splash(self):
        self.deiconify()
        if self.cfg.get("autostart", True):
            self.after(400, self._autoscan)

    def _autoscan(self):
        # простой фоновый скан системы при старте
        import threading
        def worker():
            try:
                scan_system()
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _toggle_theme(self):
        new = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new)
        self.cfg["theme"] = new.lower()
        save_config(self.cfg)
        self.theme_btn.configure(text="☀️" if new == "Dark" else "🌙")
