# engine/config.py
import json
import sys
from pathlib import Path
from typing import Optional


def get_services_path() -> Path:
    """
    Resolve services.json path.
    - Frozen exe: next to the .exe (writable), falling back to MEIPASS default.
    - Dev: project root.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        user_path = exe_dir / "services.json"
        if user_path.exists():
            return user_path
        # First run: copy default from MEIPASS to exe directory
        default_path = Path(sys._MEIPASS) / "services.json"
        import shutil
        shutil.copy(default_path, user_path)
        return user_path
    return Path(__file__).parent.parent / "services.json"


def load_services(path: Optional[Path] = None) -> list[dict]:
    """Load services list. Missing `enabled` field defaults to True."""
    p = path or get_services_path()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    services = data["services"]
    for svc in services:
        svc.setdefault("enabled", True)
    return services


def save_services(services: list[dict], path: Optional[Path] = None) -> None:
    """Persist services list to disk."""
    p = path or get_services_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"services": services}, f, ensure_ascii=False, indent=2)
