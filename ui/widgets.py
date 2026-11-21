import customtkinter as ctk
from core.keys import format_key_input


class KeyEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, placeholder_text="XXXX-XXXX-XXXX-XXXX", **kwargs)
        self.bind("<KeyRelease>", self._on_key)

    def _on_key(self, _e=None):
        f = format_key_input(self.get())
        if f != self.get():
            self.delete(0, "end")
            self.insert(0, f)
