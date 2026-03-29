import customtkinter as ctk

class SpeedBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
    def update_speed(self, result): pass
    def update_ping(self, ping_ms, loss_pct): pass
