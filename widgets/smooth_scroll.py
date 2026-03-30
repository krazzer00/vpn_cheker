# widgets/smooth_scroll.py
"""
Smooth mousewheel scrolling for CTkScrollableFrame.

Replaces (not adds to) existing bindings so CTk's default 3-unit jump
never fires alongside our animation.  Returns `rebind` so callers can
re-apply after dynamically adding child widgets.
"""
import customtkinter as ctk


def apply_smooth_scroll(frame: ctk.CTkScrollableFrame,
                        speed: float = 0.28,
                        friction: float = 0.80) -> callable:
    canvas = frame._parent_canvas
    vel = [0.0]
    timer = [None]

    def _tick():
        if abs(vel[0]) < 0.000005:
            vel[0] = 0.0
            timer[0] = None
            return
        canvas.yview_moveto(max(0.0, min(1.0, canvas.yview()[0] + vel[0])))
        vel[0] *= friction
        timer[0] = canvas.after(14, _tick)  # ~70 fps

    def _on_wheel(event):
        if not event.delta:
            return "break"
        bbox = canvas.bbox("all")
        if not bbox:
            return "break"
        ch = canvas.winfo_height()
        th = bbox[3] - bbox[1]
        if th <= ch:
            return "break"
        vel[0] -= (event.delta / 120) * speed * (ch / th) * 3
        if timer[0] is None:
            timer[0] = canvas.after(0, _tick)
        return "break"  # stop CTk's default 3-unit handler from also firing

    def rebind(widget):
        """
        Bind (replacing any existing binding) to widget and all descendants.
        Call this after dynamically adding children to keep smooth scroll working.
        """
        widget.bind("<MouseWheel>", _on_wheel)   # no add="+" → replaces CTk binding
        for child in widget.winfo_children():
            rebind(child)

    rebind(frame)
    canvas.bind("<MouseWheel>", _on_wheel)  # replace canvas binding too
    return rebind
