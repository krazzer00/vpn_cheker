# engine/history.py
import json
from datetime import datetime
from pathlib import Path

_HISTORY_DIR = Path.home() / ".vpn_checker"
_HISTORY_PATH = _HISTORY_DIR / "history.json"
_MAX_RECORDS = 100


def _ensure_dir():
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    """Load check history. Returns list newest-first."""
    if not _HISTORY_PATH.exists():
        return []
    try:
        with open(_HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_result(verdict: dict, service_results: list[dict],
                ip_info: str = "") -> None:
    """Prepend a new check record. Truncates to _MAX_RECORDS."""
    _ensure_dir()
    records = load_history()
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "ip_info": ip_info,
        "score": verdict["score"],
        "tier": verdict["tier"],
        "message": verdict["message"],
        "accessible_count": verdict["accessible_count"],
        "total_count": verdict["total_count"],
        "services": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "accessible": r.get("accessible", False),
                "ping_ms": r.get("ping_ms"),
                "loss_pct": r.get("loss_pct"),
            }
            for r in service_results
        ],
    }
    records.insert(0, record)
    records = records[:_MAX_RECORDS]
    with open(_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def clear_history() -> None:
    """Delete all history records."""
    if _HISTORY_PATH.exists():
        _HISTORY_PATH.unlink()
