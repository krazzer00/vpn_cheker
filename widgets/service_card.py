import customtkinter as ctk

class ServiceCard(ctk.CTkFrame):
    def __init__(self, master, service: dict, **kwargs):
        super().__init__(master, **kwargs)
    def set_checking(self): pass
    def update_result(self, result): pass
