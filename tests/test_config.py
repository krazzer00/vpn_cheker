# tests/test_config.py
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from engine.config import load_services, save_services, get_services_path

def test_load_services_returns_list():
    services = load_services()
    assert isinstance(services, list)
    assert len(services) > 0
    assert "id" in services[0]
    assert "enabled" in services[0]

def test_save_and_reload(tmp_path):
    path = tmp_path / "services.json"
    services = [{"id": "test", "name": "Test", "icon": "🔥",
                 "category": "Other", "url": "https://test.com",
                 "check_url": "https://test.com", "check_type": "http",
                 "port": 443, "enabled": True}]
    save_services(services, path=path)
    loaded = load_services(path=path)
    assert loaded[0]["id"] == "test"
    assert loaded[0]["enabled"] is True

def test_disabled_services_have_enabled_false(tmp_path):
    path = tmp_path / "services.json"
    services = [{"id": "x", "name": "X", "icon": "X", "category": "Other",
                 "url": "https://x.com", "check_url": "https://x.com",
                 "check_type": "http", "port": 443, "enabled": False}]
    save_services(services, path=path)
    loaded = load_services(path=path)
    assert loaded[0]["enabled"] is False
