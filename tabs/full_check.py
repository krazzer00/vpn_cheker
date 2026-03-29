import customtkinter as ctk
import queue

class FullCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, **kwargs)
    def handle_result(self, msg): pass
