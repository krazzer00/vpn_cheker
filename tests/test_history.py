# tests/test_history.py
import json
from pathlib import Path
from unittest.mock import patch
from engine.history import save_result, load_history, clear_history


def test_save_and_load(tmp_path):
    p = tmp_path / "history.json"
    verdict = {"score": 8.5, "tier": "A", "message": "Норм",
               "accessible_count": 10, "total_count": 12}
    service_results = [{"id": "github", "name": "GitHub", "accessible": True,
                         "ping_ms": 30.0, "loss_pct": 0.0}]
    with patch("engine.history._HISTORY_PATH", p):
        save_result(verdict, service_results)

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) == 1
    assert records[0]["score"] == 8.5
    assert records[0]["tier"] == "A"
    assert len(records[0]["services"]) == 1


def test_newest_first(tmp_path):
    p = tmp_path / "history.json"
    with patch("engine.history._HISTORY_PATH", p):
        for i in range(3):
            save_result({"score": float(i), "tier": "F", "message": "x",
                         "accessible_count": 0, "total_count": 1}, [])

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert records[0]["score"] == 2.0  # newest first


def test_max_100_records(tmp_path):
    p = tmp_path / "history.json"
    with patch("engine.history._HISTORY_PATH", p):
        for i in range(110):
            save_result({"score": 0.0, "tier": "F", "message": "x",
                         "accessible_count": 0, "total_count": 1}, [])

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) <= 100


def test_clear_history(tmp_path):
    p = tmp_path / "history.json"
    with patch("engine.history._HISTORY_PATH", p):
        save_result({"score": 5.0, "tier": "B", "message": "x",
                     "accessible_count": 5, "total_count": 10}, [])
        clear_history()

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) == 0
