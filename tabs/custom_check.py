import customtkinter as ctk
import queue

class CustomCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, **kwargs)
        self.result_queue = result_queue
    def handle_result(self, msg): pass
