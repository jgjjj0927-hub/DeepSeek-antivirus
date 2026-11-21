import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.scanner import scan_paths, scan_system, quarantine_file, list_quarantine
from core.keys import validate_key_format, bind_key, deactivate, generate_key
from core.config import save_config
from core.crypto import decrypt_str
from ui.widgets import KeyEntry


class ScanTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._running = False
        self._stop = False
        self._build()

    def _build(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=6)
        ctk.CTkLabel(row, text="Путь:").pack(side="left", padx=(0, 6))
        self.path_entry = ctk.CTkEntry(row, placeholder_text="Файл или папка...")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="Обзор", width=70, command=self._browse).pack(side="left", padx=2)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", pady=4)
        self.scan_btn = ctk.CTkButton(btns, text="▶ Сканировать", command=self._start)
        self.scan_btn.pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🖥 Система", command=self._start_system).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="⏹ Стоп", width=70, fg_color="#8B0000",
                      hover_color="#5a0000", command=self._stop_scan).pack(side="left", padx=2)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(fill="x", pady=(8, 4))
        self.progress.set(0)
        self.log = ctk.CTkTextbox(self, height=280)
        self.log.pack(fill="both", expand=True, pady=4)

    def _browse(self):
        p = filedialog.askopenfilename() or filedialog.askdirectory()
        if p:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, p)

    def _start(self):
        p = self.path_entry.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("Путь", "Укажи существующий файл или папку.")
            return
        self._run(lambda: scan_paths([p], self._prog, lambda: self._stop))

    def _start_system(self):
        self._run(lambda: scan_system(self._prog, lambda: self._stop))

    def _prog(self, v):
        self.after(0, lambda: self.progress.set(v))

    def _run(self, fn):
        if self._running:
            return
        self._running = True
        self._stop = False
        self.scan_btn.configure(state="disabled")
        self.log.delete("1.0", "end")
        self.progress.set(0)

        def worker():
            try:
                threats = fn()
            except Exception as e:
                self.after(0, lambda: self.log.insert("end", f"Ошибка: {e}\n"))
                threats = []
            self.after(0, lambda: self._done(threats))

        threading.Thread(target=worker, daemon=True).start()

    def _stop_scan(self):
        self._stop = True
        self.log.insert("end", "\n[!] Остановка...\n")

    def _done(self, threats):
        self._running = False
        self.scan_btn.configure(state="normal")
        self.progress.set(1)
        real = [t for t in threats if t.get("severity") != "info"]
        if not real:
            self.log.insert("end", "✅ Угроз не обнаружено.\n")
        else:
            self.log.insert("end", f"⚠️ Подозрительных: {len(real)}\n\n")
            for t in real:
                self.log.insert("end", f"[{t['severity'].upper()}] {t['path']}\n  → {t['reason']}\n")
            if messagebox.askyesno("Карантин", f"Переместить {len(real)} в карантин?"):
                ok = sum(1 for t in real if quarantine_file(t["path"]))
                self.log.insert("end", f"\n📦 В карантине: {ok}\n")
        if len(threats) > len(real):
            self.log.insert("end", f"\nℹ️ Просканировано файлов с хешем: {len(threats) - len(real)}\n")


class QuarantineTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.box = ctk.CTkTextbox(self, height=300)
        self.box.pack(fill="both", expand=True, padx=4, pady=4)
        ctk.CTkButton(self, text="🔄 Обновить", command=self.refresh).pack(pady=4)
        self.refresh()

    def refresh(self):
        self.box.delete("1.0", "end")
        items = list_quarantine()
        if not items:
            self.box.insert("end", "Карантин пуст.\n")
            return
        for it in items:
            self.box.insert("end", f"{it['name']}\n  ← {it['original']}\n\n")


class KeysTab(ctk.CTkFrame):
    def __init__(self, master, cfg):
        super().__init__(master, fg_color="transparent")
        self.cfg = cfg
        self._build()
        self._refresh()

    def _build(self):
        ctk.CTkLabel(self, text="🔐 Статус ключа",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(8, 2))
        self.status = ctk.CTkLabel(self, text="...", justify="left")
        self.status.pack(anchor="w", padx=8, pady=2)
        self.hwid_lbl = ctk.CTkLabel(self, text="", text_color="gray", justify="left")
        self.hwid_lbl.pack(anchor="w", padx=8, pady=2)

        ctk.CTkButton(self, text="🎲 Сгенерировать ключ", command=self._gen).pack(anchor="w", padx=8, pady=6)

        ctk.CTkLabel(self, text="Ввод ключа",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(8, 2))
        self.entry = KeyEntry(self, width=280)
        self.entry.pack(anchor="w", padx=8, pady=4)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(anchor="w", padx=8, pady=4)
        ctk.CTkButton(btns, text="💾 Сохранить", command=self._save).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑 Деактивировать", fg_color="#8B0000",
                      hover_color="#5a0000", command=self._deact).pack(side="left", padx=2)

        ctk.CTkLabel(self, text="Developer: t.me/aqDiamondS",
                     text_color="#4a9eff").pack(anchor="w", padx=8, pady=12)

    def _gen(self):
        k = generate_key()
        self.entry.delete(0, "end")
        self.entry.insert(0, k)

    def _save(self):
        k = self.entry.get().strip().upper()
        ok, msg = validate_key_format(k)
        if not ok:
            messagebox.showerror("Ключ", msg)
            return
        try:
            is_new = bind_key(k, self.cfg)
            messagebox.showinfo("Ключ", "Сохранён." if is_new else "Уже привязан.")
            self._refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _deact(self):
        if messagebox.askyesno("Деактивация", "Удалить ключ?"):
            deactivate(self.cfg)
            self._refresh()

    def _refresh(self):
        if not self.cfg.get("key"):
            self.status.configure(text="❌ Ключ не активирован", text_color="#ff6b6b")
            self.hwid_lbl.configure(text="")
            return
        try:
            self.status.configure(text=f"✅ {decrypt_str(self.cfg['key'])}", text_color="#6bff6b")
            self.hwid_lbl.configure(text=f"HWID: {self.cfg.get('hwid', '?')[:32]}...")
        except Exception:
            self.status.configure(text="⚠️ Ошибка чтения ключа", text_color="#ffaa00")


class AboutTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="KiwiLab X00Team",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#3ddc84").pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Молодёжный антивирус нового поколения",
                     text_color="#8fbf9f").pack(pady=2)
        ctk.CTkLabel(self, text="Версия 1.0.0", text_color="gray").pack(pady=2)
        ctk.CTkLabel(self, text="Developer: t.me/aqDiamondS",
                     text_color="#4a9eff").pack(pady=20)
