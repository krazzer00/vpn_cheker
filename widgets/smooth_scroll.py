# widgets/smooth_scroll.py
"""Smooth mousewheel scrolling for CTkScrollableFrame."""
import customtkinter as ctk


def apply_smooth_scroll(frame: ctk.CTkScrollableFrame,
                        speed: float = 0.25,
                        friction: float = 0.82) -> callable:
    """
    Apply velocity-based smooth mousewheel scrolling to a CTkScrollableFrame.
    Replaces the default 3-unit jump with ease-out animation.

    Returns the wheel handler so callers can bind it to dynamically added children.
    """
    canvas = frame._parent_canvas
    vel = [0.0]
    timer = [None]

    def _tick():
        if abs(vel[0]) < 0.000005:
            vel[0] = 0.0
            timer[0] = None
            return
        pos = canvas.yview()[0]
        canvas.yview_moveto(max(0.0, min(1.0, pos + vel[0])))
        vel[0] *= friction
        timer[0] = canvas.after(14, _tick)  # ~70 fps

    def _on_wheel(event):
        if not event.delta:
            return
        bbox = canvas.bbox("all")
        if not bbox:
            return
        canvas_h = canvas.winfo_height()
        content_h = bbox[3] - bbox[1]
        if content_h <= canvas_h:
            return
        notches = event.delta / 120
        frac_per_notch = speed * canvas_h / content_h
        vel[0] -= notches * frac_per_notch
        if timer[0] is None:
            timer[0] = canvas.after(0, _tick)

    def _bind_recursive(widget):
        widget.bind("<MouseWheel>", _on_wheel, add="+")
        for child in widget.winfo_children():
            _bind_recursive(child)

    _bind_recursive(frame)
    canvas.bind("<MouseWheel>", _on_wheel, add="+")
    return _on_wheel
