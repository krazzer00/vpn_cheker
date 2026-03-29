import queue
from unittest.mock import patch, MagicMock
from engine.checker import run_checks, run_single_check

def _fake_ping(host, count=4):
    return {"ping_ms": 30.0, "loss_pct": 0.0, "method": "icmp"}

def _fake_http(url):
    return {"accessible": True, "status_code": 200, "response_ms": 50.0, "error": None}

def _fake_ai(url):
    return {"region_accessible": True, "status_code": 401, "error": None}

def _fake_speed():
    return {"download_mbps": 90.0, "upload_mbps": 45.0, "ping_ms": 15.0, "error": None}

def test_run_checks_puts_results_in_queue():
    q = queue.Queue()
    services = [
        {"id": "github", "name": "GitHub", "icon": "🐙", "category": "Other",
         "url": "https://github.com", "check_url": "https://github.com",
         "check_type": "http", "port": 443}
    ]
    with patch("engine.checker.ping_host", side_effect=_fake_ping), \
         patch("engine.checker.http_check", side_effect=_fake_http), \
         patch("engine.checker.run_speedtest", side_effect=_fake_speed):
        run_checks(services, q)

    results = []
    while not q.empty():
        results.append(q.get())

    service_results = [r for r in results if r["type"] == "service"]
    assert len(service_results) == 1
    assert service_results[0]["id"] == "github"
    assert service_results[0]["accessible"] is True

def test_run_checks_sends_verdict():
    q = queue.Queue()
    services = [
        {"id": "github", "name": "GitHub", "icon": "🐙", "category": "Other",
         "url": "https://github.com", "check_url": "https://github.com",
         "check_type": "http", "port": 443}
    ]
    with patch("engine.checker.ping_host", side_effect=_fake_ping), \
         patch("engine.checker.http_check", side_effect=_fake_http), \
         patch("engine.checker.run_speedtest", side_effect=_fake_speed):
        run_checks(services, q)

    all_msgs = []
    while not q.empty():
        all_msgs.append(q.get())

    verdict_msgs = [m for m in all_msgs if m["type"] == "verdict"]
    assert len(verdict_msgs) == 1
    assert "score" in verdict_msgs[0]

def test_run_single_check_returns_result():
    service = {
        "id": "github", "name": "GitHub", "icon": "🐙", "category": "Other",
        "url": "https://github.com", "check_url": "https://github.com",
        "check_type": "http", "port": 443
    }
    with patch("engine.checker.ping_host", side_effect=_fake_ping), \
         patch("engine.checker.http_check", side_effect=_fake_http):
        result = run_single_check(service)
    assert result["accessible"] is True
    assert result["ping_ms"] == 30.0
