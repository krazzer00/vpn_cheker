# engine/config.py
import json
import sys
from pathlib import Path
from typing import Optional


def get_services_path() -> Path:
    """
    Resolve services.json path.
    - Frozen exe: next to the .exe (writable), updated from MEIPASS when _version bumps.
    - Dev: project root.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        user_path = exe_dir / "services.json"
        bundled_path = Path(sys._MEIPASS) / "services.json"

        if user_path.exists():
            _sync_if_updated(user_path, bundled_path)
            return user_path

        # First run: copy default from MEIPASS to exe directory
        import shutil
        shutil.copy(bundled_path, user_path)
        return user_path
    return Path(__file__).parent.parent / "services.json"


def _sync_if_updated(user_path: Path, bundled_path: Path) -> None:
    """
    When the bundled _version is higher than the user's copy, merge structural
    fields (url, check_url, check_type, icon, category) from the bundle while
    preserving user preferences (enabled flag, new custom services).
    """
    try:
        with open(user_path, encoding="utf-8") as f:
            user_data = json.load(f)
        with open(bundled_path, encoding="utf-8") as f:
            bundled_data = json.load(f)
    except Exception:
        return

    if bundled_data.get("_version", 1) <= user_data.get("_version", 1):
        return

    # Build lookup of user-enabled states by service id
    user_enabled = {s["id"]: s.get("enabled", True)
                    for s in user_data.get("services", [])}

    # Use bundled list as authoritative source, restore user's enabled flags
    merged = []
    for svc in bundled_data.get("services", []):
        svc = dict(svc)
        if svc["id"] in user_enabled:
            svc["enabled"] = user_enabled[svc["id"]]
        merged.append(svc)

    user_data["_version"] = bundled_data["_version"]
    user_data["services"] = merged
    with open(user_path, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)


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
    """Persist services list to disk, preserving _version if present."""
    p = path or get_services_path()
    version = 1
    try:
        with open(p, encoding="utf-8") as f:
            version = json.load(f).get("_version", 1)
    except Exception:
        pass
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"_version": version, "services": services}, f,
                  ensure_ascii=False, indent=2)
