# VPN Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable Windows desktop app that tests VPN effectiveness across popular services and shows ping, packet loss, speed, and a meme verdict score.

**Architecture:** CustomTkinter GUI polls a thread-safe queue every 100ms for results from a ThreadPoolExecutor that runs all service checks in parallel. Services are defined in `services.json` so new ones can be added without code changes.

**Tech Stack:** Python 3.11+, customtkinter, ping3, requests, speedtest-cli, PyInstaller

---

## File Map

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point — create and start the app |
| `app.py` | Main CTk window, tab container, queue poll loop |
| `tabs/full_check.py` | Full check tab: sidebar checkboxes, speed bar, cards grid, verdict |
| `tabs/custom_check.py` | Custom check tab: single URL input, result card |
| `widgets/service_card.py` | CTk frame showing one service result (status, ping, loss, region) |
| `widgets/speed_bar.py` | Top bar showing global ping / download / upload / loss |
| `engine/checker.py` | Orchestrator: ThreadPoolExecutor, dispatches checks, puts results in queue |
| `engine/ping.py` | ICMP ping via ping3, TCP fallback, packet loss calculation |
| `engine/http_check.py` | HTTP availability + regional AI check logic |
| `engine/speedtest.py` | speedtest-cli wrapper, returns download/upload Mbps |
| `services.json` | Service definitions: name, url, icon, category, check_type |
| `requirements.txt` | Pinned dependencies |
| `tests/test_ping.py` | Unit tests for ping engine |
| `tests/test_http_check.py` | Unit tests for HTTP check engine |
| `tests/test_verdict.py` | Unit tests for verdict scoring algorithm |
| `tests/test_checker.py` | Integration tests for checker orchestrator |
| `build.bat` | One-click PyInstaller build script |

---

## Task 1: Project scaffold and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `services.json`
- Create: `main.py`
- Create: `app.py`
- Create: `tabs/__init__.py`
- Create: `widgets/__init__.py`
- Create: `engine/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Install dependencies**

```bash
cd /c/Users/krazz/Desktop/vpn_cheker
python -m venv .venv
source .venv/Scripts/activate
pip install customtkinter ping3 requests speedtest-cli pytest pyinstaller
pip freeze > requirements.txt
```

- [ ] **Step 2: Create services.json**

```json
{
  "services": [
    {
      "id": "claude",
      "name": "Claude AI",
      "icon": "🤖",
      "category": "AI",
      "url": "https://api.anthropic.com",
      "check_url": "https://api.anthropic.com/v1/messages",
      "check_type": "ai_region",
      "port": 443
    },
    {
      "id": "chatgpt",
      "name": "ChatGPT",
      "icon": "💬",
      "category": "AI",
      "url": "https://api.openai.com",
      "check_url": "https://api.openai.com/v1/models",
      "check_type": "ai_region",
      "port": 443
    },
    {
      "id": "gemini",
      "name": "Gemini",
      "icon": "✨",
      "category": "AI",
      "url": "https://generativelanguage.googleapis.com",
      "check_url": "https://generativelanguage.googleapis.com/v1/models",
      "check_type": "ai_region",
      "port": 443
    },
    {
      "id": "youtube",
      "name": "YouTube",
      "icon": "▶",
      "category": "Media",
      "url": "https://www.youtube.com",
      "check_url": "https://www.youtube.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "twitch",
      "name": "Twitch",
      "icon": "🎮",
      "category": "Media",
      "url": "https://www.twitch.tv",
      "check_url": "https://www.twitch.tv",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "instagram",
      "name": "Instagram",
      "icon": "📸",
      "category": "Social",
      "url": "https://www.instagram.com",
      "check_url": "https://www.instagram.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "vk",
      "name": "VK",
      "icon": "🔵",
      "category": "Social",
      "url": "https://vk.com",
      "check_url": "https://vk.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "telegram",
      "name": "Telegram",
      "icon": "✈",
      "category": "Social",
      "url": "https://telegram.org",
      "check_url": "https://telegram.org",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "github",
      "name": "GitHub",
      "icon": "🐙",
      "category": "Other",
      "url": "https://github.com",
      "check_url": "https://github.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "discord",
      "name": "Discord",
      "icon": "🎮",
      "category": "Other",
      "url": "https://discord.com",
      "check_url": "https://discord.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "vrchat",
      "name": "VRChat",
      "icon": "🌐",
      "category": "Other",
      "url": "https://vrchat.com",
      "check_url": "https://vrchat.com",
      "check_type": "http",
      "port": 443
    },
    {
      "id": "vrcdn",
      "name": "VRCDN",
      "icon": "📡",
      "category": "Other",
      "url": "https://vrcdn.live",
      "check_url": "https://vrcdn.live",
      "check_type": "http",
      "port": 443
    }
  ]
}
```

- [ ] **Step 3: Create package __init__ files**

```bash
mkdir -p tabs widgets engine tests
touch tabs/__init__.py widgets/__init__.py engine/__init__.py tests/__init__.py
```

- [ ] **Step 4: Create main.py**

```python
# main.py
from app import VpnCheckerApp

if __name__ == "__main__":
    app = VpnCheckerApp()
    app.mainloop()
```

- [ ] **Step 5: Create app.py skeleton**

```python
# app.py
import customtkinter as ctk
import queue

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG = "#16161f"
DARKER_BG = "#111118"
BORDER = "#2a2a3a"
ACCENT = "#5b6af5"


class VpnCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Checker")
        self.geometry("960x620")
        self.minsize(800, 560)
        self.configure(fg_color=DARK_BG)

        self.result_queue: queue.Queue = queue.Queue()

        self._build_titlebar()
        self._build_tabs()
        self._start_queue_poll()

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=DARKER_BG, height=40, corner_radius=0)
        bar.pack(fill="x", side="top")
        ctk.CTkLabel(bar, text="VPN Checker", font=("Segoe UI", 13, "bold"),
                     text_color="#aaaaaa").pack(side="left", padx=16, pady=8)
        self.ip_label = ctk.CTkLabel(bar, text="● Определение IP...",
                                      font=("Segoe UI", 11), text_color="#7c7caa")
        self.ip_label.pack(side="right", padx=16)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, fg_color=DARK_BG,
                                       segmented_button_fg_color=DARKER_BG,
                                       segmented_button_selected_color=ACCENT,
                                       segmented_button_unselected_color=DARKER_BG)
        self.tabview.pack(fill="both", expand=True, padx=0, pady=0)

        self.tabview.add("🛡  Полная проверка")
        self.tabview.add("🔍  Кастомная")

        self.full_tab = FullCheckTab(
            self.tabview.tab("🛡  Полная проверка"),
            self.result_queue
        )
        self.full_tab.pack(fill="both", expand=True)

        self.custom_tab = CustomCheckTab(
            self.tabview.tab("🔍  Кастомная"),
            self.result_queue
        )
        self.custom_tab.pack(fill="both", expand=True)

    def _start_queue_poll(self):
        self._poll_queue()

    def _poll_queue(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                self.full_tab.handle_result(msg)
                self.custom_tab.handle_result(msg)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)
```

- [ ] **Step 6: Verify app launches (empty tabs are fine)**

```bash
python main.py
```
Expected: Window opens with dark background, two tabs visible, no errors.

- [ ] **Step 7: Commit**

```bash
git add main.py app.py tabs/ widgets/ engine/ tests/ services.json requirements.txt
git commit -m "feat: project scaffold, deps, services.json"
```

---

## Task 2: Ping engine

**Files:**
- Create: `engine/ping.py`
- Create: `tests/test_ping.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ping.py
from unittest.mock import patch, MagicMock
from engine.ping import ping_host, tcp_ping

def test_ping_host_returns_dict_keys():
    with patch("engine.ping.ping3.ping", return_value=0.032):
        result = ping_host("8.8.8.8")
    assert "ping_ms" in result
    assert "loss_pct" in result
    assert "method" in result

def test_ping_host_calculates_loss():
    # 1 out of 4 packets lost
    with patch("engine.ping.ping3.ping", side_effect=[0.01, None, 0.01, 0.01]):
        result = ping_host("8.8.8.8", count=4)
    assert result["loss_pct"] == 25.0

def test_ping_host_all_lost():
    with patch("engine.ping.ping3.ping", return_value=None):
        result = ping_host("8.8.8.8", count=4)
    assert result["ping_ms"] is None
    assert result["loss_pct"] == 100.0

def test_tcp_ping_success():
    with patch("engine.ping.socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock(return_value=None)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = tcp_ping("github.com", 443)
    assert result["ping_ms"] is not None
    assert result["method"] == "tcp"

def test_tcp_ping_failure():
    with patch("engine.ping.socket.create_connection", side_effect=OSError):
        result = tcp_ping("github.com", 443)
    assert result["ping_ms"] is None
    assert result["loss_pct"] == 100.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ping.py -v
```
Expected: 5 errors — `engine.ping` module not found.

- [ ] **Step 3: Implement engine/ping.py**

```python
# engine/ping.py
import socket
import time
from typing import Optional

import ping3

PING_TIMEOUT = 2
PING_COUNT = 4


def ping_host(host: str, count: int = PING_COUNT) -> dict:
    """
    ICMP ping with packet loss. Falls back to TCP on permission error.
    Returns: {ping_ms, loss_pct, method}
    """
    try:
        results = []
        for _ in range(count):
            try:
                rtt = ping3.ping(host, timeout=PING_TIMEOUT, unit="ms")
                results.append(rtt)
            except PermissionError:
                return tcp_ping(host, 443)
        lost = sum(1 for r in results if r is None)
        valid = [r for r in results if r is not None]
        return {
            "ping_ms": round(sum(valid) / len(valid), 1) if valid else None,
            "loss_pct": round((lost / count) * 100, 1),
            "method": "icmp",
        }
    except Exception:
        return tcp_ping(host, 443)


def tcp_ping(host: str, port: int, timeout: float = 2.0) -> dict:
    """TCP connect as ping fallback."""
    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
        return {
            "ping_ms": round(elapsed, 1),
            "loss_pct": 0.0,
            "method": "tcp",
        }
    except OSError:
        return {
            "ping_ms": None,
            "loss_pct": 100.0,
            "method": "tcp",
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ping.py -v
```
Expected: 5 PASSED.

- [ ] **Step 5: Commit**

```bash
git add engine/ping.py tests/test_ping.py
git commit -m "feat: ping engine with ICMP + TCP fallback"
```

---

## Task 3: HTTP check engine

**Files:**
- Create: `engine/http_check.py`
- Create: `tests/test_http_check.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_http_check.py
from unittest.mock import patch, MagicMock
from engine.http_check import http_check, ai_region_check

def _mock_response(status_code):
    r = MagicMock()
    r.status_code = status_code
    return r

def test_http_check_accessible():
    with patch("engine.http_check.requests.head", return_value=_mock_response(200)):
        result = http_check("https://github.com")
    assert result["accessible"] is True
    assert result["status_code"] == 200
    assert result["response_ms"] is not None

def test_http_check_not_accessible():
    with patch("engine.http_check.requests.head", side_effect=Exception("timeout")):
        result = http_check("https://github.com")
    assert result["accessible"] is False
    assert result["status_code"] is None

def test_ai_region_check_accessible_on_401():
    """401 Unauthorized means the endpoint is reachable — just no API key."""
    with patch("engine.http_check.requests.get", return_value=_mock_response(401)):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is True

def test_ai_region_check_blocked_on_403():
    with patch("engine.http_check.requests.get", return_value=_mock_response(403)):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is False

def test_ai_region_check_blocked_on_timeout():
    with patch("engine.http_check.requests.get", side_effect=Exception("timeout")):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_http_check.py -v
```
Expected: 5 errors — module not found.

- [ ] **Step 3: Implement engine/http_check.py**

```python
# engine/http_check.py
import time
import requests

HTTP_TIMEOUT = 5
AI_TIMEOUT = 8

# Status codes that mean the endpoint is reachable (just no auth)
_REACHABLE_STATUSES = {200, 201, 400, 401, 405, 422}


def http_check(url: str) -> dict:
    """
    HEAD request to check HTTP availability.
    Returns: {accessible, status_code, response_ms}
    """
    try:
        start = time.perf_counter()
        r = requests.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True,
                          headers={"User-Agent": "VPNChecker/1.0"})
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "accessible": r.status_code < 500,
            "status_code": r.status_code,
            "response_ms": round(elapsed, 1),
        }
    except Exception:
        return {
            "accessible": False,
            "status_code": None,
            "response_ms": None,
        }


def ai_region_check(check_url: str) -> dict:
    """
    Check if an AI service is accessible in this region.
    401 = reachable (just no key). 403/timeout = geo-blocked.
    Returns: {region_accessible, status_code}
    """
    try:
        r = requests.get(check_url, timeout=AI_TIMEOUT,
                         headers={"User-Agent": "VPNChecker/1.0"})
        return {
            "region_accessible": r.status_code in _REACHABLE_STATUSES,
            "status_code": r.status_code,
        }
    except Exception:
        return {
            "region_accessible": False,
            "status_code": None,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_http_check.py -v
```
Expected: 5 PASSED.

- [ ] **Step 5: Commit**

```bash
git add engine/http_check.py tests/test_http_check.py
git commit -m "feat: HTTP check + AI regional check engine"
```

---

## Task 4: Speedtest engine

**Files:**
- Create: `engine/speedtest.py`

- [ ] **Step 1: Implement engine/speedtest.py**

No unit tests here — speedtest-cli makes real network calls and has no clean mock surface. Integration only.

```python
# engine/speedtest.py
import speedtest as st


def run_speedtest() -> dict:
    """
    Run a speedtest. Returns download/upload in Mbps and ping in ms.
    Returns: {download_mbps, upload_mbps, ping_ms, error}
    """
    try:
        s = st.Speedtest(secure=True)
        s.get_best_server()
        s.download()
        s.upload()
        results = s.results.dict()
        return {
            "download_mbps": round(results["download"] / 1_000_000, 1),
            "upload_mbps": round(results["upload"] / 1_000_000, 1),
            "ping_ms": round(results["ping"], 1),
            "error": None,
        }
    except Exception as e:
        return {
            "download_mbps": None,
            "upload_mbps": None,
            "ping_ms": None,
            "error": str(e),
        }
```

- [ ] **Step 2: Commit**

```bash
git add engine/speedtest.py
git commit -m "feat: speedtest engine wrapper"
```

---

## Task 5: Verdict scoring

**Files:**
- Create: `engine/verdict.py`
- Create: `tests/test_verdict.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_verdict.py
import random
from engine.verdict import score_service, compute_verdict

def test_score_perfect():
    assert score_service(accessible=True, ping_ms=50, loss_pct=0.0) == 1.0

def test_score_high_ping():
    assert score_service(accessible=True, ping_ms=150, loss_pct=0.0) == 0.7

def test_score_minor_loss():
    assert score_service(accessible=True, ping_ms=80, loss_pct=2.0) == 0.7

def test_score_very_high_ping():
    assert score_service(accessible=True, ping_ms=250, loss_pct=0.0) == 0.5

def test_score_inaccessible():
    assert score_service(accessible=False, ping_ms=None, loss_pct=100.0) == 0.0

def test_compute_verdict_perfect():
    services = [
        {"accessible": True, "ping_ms": 30, "loss_pct": 0.0},
        {"accessible": True, "ping_ms": 40, "loss_pct": 0.0},
    ]
    result = compute_verdict(services)
    assert result["score"] == 10.0
    assert result["tier"] == "S"

def test_compute_verdict_empty():
    result = compute_verdict([])
    assert result["score"] == 0.0

def test_verdict_message_in_tier(monkeypatch):
    # monkeypatch random.choice to return first element
    monkeypatch.setattr(random, "choice", lambda lst: lst[0])
    services = [{"accessible": True, "ping_ms": 30, "loss_pct": 0.0}]
    result = compute_verdict(services)
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_verdict.py -v
```
Expected: 8 errors — module not found.

- [ ] **Step 3: Implement engine/verdict.py**

```python
# engine/verdict.py
import random

_VERDICTS = {
    "S": [
        "Топчик, всё летает 🚀",
        "Пиздатый VPN, уважаю",
        "Ни одна собака не заблочила, красавчик",
    ],
    "A": [
        "Норм впн, жить можно 👍",
        "Почти идеально, но могло быть лучше",
        "Сойдёт для сельской местности",
    ],
    "B": [
        "Ну такое... 😐",
        "Работает через жопу, но работает",
        "VPN страдает, но держится",
    ],
    "C": [
        "Это провал, Карл 💀",
        "Твой VPN умирает на наших глазах",
        "Роскомнадзор победил, поздравляю",
    ],
    "F": [
        "Это не VPN, это позор семьи 🗑",
        "Братан, ты забыл включить VPN?",
        "Полный пиздец, меняй провайдера",
    ],
}


def score_service(accessible: bool, ping_ms: float | None, loss_pct: float) -> float:
    if not accessible:
        return 0.0
    if ping_ms is not None and ping_ms > 200:
        return 0.5
    if (ping_ms is not None and ping_ms > 100) or loss_pct > 0:
        return 0.7
    return 1.0


def compute_verdict(services: list[dict]) -> dict:
    """
    services: list of {accessible, ping_ms, loss_pct}
    Returns: {score, tier, message, accessible_count, total_count}
    """
    if not services:
        return {"score": 0.0, "tier": "F", "message": random.choice(_VERDICTS["F"]),
                "accessible_count": 0, "total_count": 0}

    total = len(services)
    points = sum(score_service(s["accessible"], s.get("ping_ms"), s.get("loss_pct", 0.0))
                 for s in services)
    score = round((points / total) * 10, 1)
    accessible_count = sum(1 for s in services if s["accessible"])

    if score >= 9:
        tier = "S"
    elif score >= 7:
        tier = "A"
    elif score >= 5:
        tier = "B"
    elif score >= 3:
        tier = "C"
    else:
        tier = "F"

    return {
        "score": score,
        "tier": tier,
        "message": random.choice(_VERDICTS[tier]),
        "accessible_count": accessible_count,
        "total_count": total,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_verdict.py -v
```
Expected: 8 PASSED.

- [ ] **Step 5: Commit**

```bash
git add engine/verdict.py tests/test_verdict.py
git commit -m "feat: verdict scoring with meme messages"
```

---

## Task 6: Check orchestrator

**Files:**
- Create: `engine/checker.py`
- Create: `tests/test_checker.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_checker.py
import queue
from unittest.mock import patch, MagicMock
from engine.checker import run_checks, run_single_check

def _fake_ping(host, count=4):
    return {"ping_ms": 30.0, "loss_pct": 0.0, "method": "icmp"}

def _fake_http(url):
    return {"accessible": True, "status_code": 200, "response_ms": 50.0}

def _fake_ai(url):
    return {"region_accessible": True, "status_code": 401}

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_checker.py -v
```
Expected: 3 errors — module not found.

- [ ] **Step 3: Implement engine/checker.py**

```python
# engine/checker.py
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from engine.ping import ping_host
from engine.http_check import http_check, ai_region_check
from engine.speedtest import run_speedtest
from engine.verdict import compute_verdict, score_service


def _check_one_service(service: dict) -> dict:
    """Run all checks for a single service. Called in a thread."""
    host = urlparse(service["url"]).hostname
    ping_result = ping_host(host)

    if service["check_type"] == "ai_region":
        http_result = http_check(service["url"])
        ai_result = ai_region_check(service["check_url"])
        accessible = http_result["accessible"] and ai_result["region_accessible"]
        region_accessible = ai_result["region_accessible"]
    else:
        http_result = http_check(service["check_url"])
        accessible = http_result["accessible"]
        region_accessible = None

    return {
        "type": "service",
        "id": service["id"],
        "name": service["name"],
        "icon": service["icon"],
        "category": service["category"],
        "accessible": accessible,
        "region_accessible": region_accessible,
        "ping_ms": ping_result["ping_ms"],
        "loss_pct": ping_result["loss_pct"],
        "ping_method": ping_result["method"],
        "status_code": http_result.get("status_code"),
        "response_ms": http_result.get("response_ms"),
    }


def run_checks(services: list[dict], result_queue: queue.Queue) -> None:
    """
    Run all service checks + speedtest in parallel.
    Puts {type: "service", ...} and {type: "verdict", ...} into result_queue.
    Also puts {type: "speed", ...} when speedtest completes.
    """
    service_results = []
    lock = threading.Lock()

    def speedtest_worker():
        speed = run_speedtest()
        result_queue.put({"type": "speed", **speed})

    speed_thread = threading.Thread(target=speedtest_worker, daemon=True)
    speed_thread.start()

    with ThreadPoolExecutor(max_workers=min(len(services), 8)) as pool:
        futures = {pool.submit(_check_one_service, svc): svc for svc in services}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                svc = futures[future]
                result = {
                    "type": "service",
                    "id": svc["id"],
                    "name": svc["name"],
                    "icon": svc["icon"],
                    "category": svc["category"],
                    "accessible": False,
                    "region_accessible": None,
                    "ping_ms": None,
                    "loss_pct": 100.0,
                    "ping_method": "n/a",
                    "status_code": None,
                    "response_ms": None,
                    "error": str(e),
                }
            result_queue.put(result)
            with lock:
                service_results.append(result)

    verdict = compute_verdict(service_results)
    result_queue.put({"type": "verdict", **verdict})


def run_single_check(service: dict) -> dict:
    """Single service check for the custom tab."""
    return _check_one_service(service)
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```
Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add engine/checker.py tests/test_checker.py
git commit -m "feat: check orchestrator with parallel execution"
```

---

## Task 7: ServiceCard widget

**Files:**
- Create: `widgets/service_card.py`

- [ ] **Step 1: Implement widgets/service_card.py**

```python
# widgets/service_card.py
import customtkinter as ctk

DARK_BG = "#16161f"
CARD_BG = "#1a1a26"
BORDER = "#2a2a3a"

COLOR_OK = "#4CAF50"
COLOR_WARN = "#FF9800"
COLOR_BAD = "#F44336"
COLOR_CHECKING = "#5b6af5"
COLOR_MUTED = "#555566"


def _ping_color(ping_ms):
    if ping_ms is None:
        return COLOR_BAD
    if ping_ms < 100:
        return COLOR_OK
    if ping_ms < 200:
        return COLOR_WARN
    return COLOR_BAD


class ServiceCard(ctk.CTkFrame):
    def __init__(self, master, service: dict, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self.service = service
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(top, text=self.service["icon"] + "  " + self.service["name"],
                     font=("Segoe UI", 13, "bold")).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            top, text="Ожидание...",
            font=("Segoe UI", 10, "bold"),
            text_color=COLOR_CHECKING,
            fg_color="#1e1e3a", corner_radius=10
        )
        self.status_badge.pack(side="right", padx=(4, 0))

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 10))

        self.ping_label = self._stat(stats, "ПИНГ", "—")
        self.loss_label = self._stat(stats, "ПОТЕРИ", "—")
        self.region_label = self._stat(stats, "РЕГИОН", "—")

    def _stat(self, parent, label_text, value_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(frame, text=label_text, font=("Segoe UI", 9),
                     text_color=COLOR_MUTED).pack(anchor="w")
        val = ctk.CTkLabel(frame, text=value_text, font=("Segoe UI", 13, "bold"))
        val.pack(anchor="w")
        return val

    def set_checking(self):
        self.status_badge.configure(text="Проверка...", text_color=COLOR_CHECKING,
                                    fg_color="#1e1e3a")
        self.ping_label.configure(text="—", text_color="white")
        self.loss_label.configure(text="—", text_color="white")
        self.region_label.configure(text="—", text_color="white")
        self.configure(border_color=BORDER)

    def update_result(self, result: dict):
        accessible = result["accessible"]
        ping_ms = result.get("ping_ms")
        loss_pct = result.get("loss_pct", 0.0)
        region = result.get("region_accessible")

        if accessible:
            self.status_badge.configure(text="Доступен", text_color=COLOR_OK,
                                        fg_color=_alpha_color(COLOR_OK))
            self.configure(border_color=COLOR_OK)
        else:
            self.status_badge.configure(text="Недоступен", text_color=COLOR_BAD,
                                        fg_color=_alpha_color(COLOR_BAD))
            self.configure(border_color=COLOR_BAD)

        ping_text = f"{ping_ms} ms" if ping_ms is not None else "—"
        self.ping_label.configure(text=ping_text, text_color=_ping_color(ping_ms))

        loss_color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
        self.loss_label.configure(text=f"{loss_pct}%", text_color=loss_color)

        if region is None:
            self.region_label.configure(text="н/п", text_color=COLOR_MUTED)
        elif region:
            self.region_label.configure(text="✓", text_color=COLOR_OK)
        else:
            self.region_label.configure(text="✗", text_color=COLOR_BAD)


def _alpha_color(hex_color: str) -> str:
    """Return a darkened bg color for status badges."""
    mapping = {
        COLOR_OK: "#1a2e1a",
        COLOR_WARN: "#2e1f0a",
        COLOR_BAD: "#2e0a0a",
        COLOR_CHECKING: "#1a1e3a",
    }
    return mapping.get(hex_color, "#1a1a26")
```

- [ ] **Step 2: Commit**

```bash
git add widgets/service_card.py
git commit -m "feat: ServiceCard widget with live update"
```

---

## Task 8: SpeedBar widget

**Files:**
- Create: `widgets/speed_bar.py`

- [ ] **Step 1: Implement widgets/speed_bar.py**

```python
# widgets/speed_bar.py
import customtkinter as ctk

DARKER_BG = "#1a1a26"
BORDER = "#2a2a3a"
MUTED = "#555566"
ACCENT = "#e0e0e0"


class SpeedBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=DARKER_BG, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self._build()

    def _build(self):
        self.ping_val = self._item("ПИНГ", "—")
        self._divider()
        self.dl_val = self._item("ЗАГРУЗКА", "—")
        self._divider()
        self.ul_val = self._item("ВЫГРУЗКА", "—")
        self._divider()
        self.loss_val = self._item("ПОТЕРИ", "—")

    def _item(self, label, value):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 9),
                     text_color=MUTED).pack(anchor="w")
        val = ctk.CTkLabel(frame, text=value, font=("Segoe UI", 20, "bold"),
                            text_color=ACCENT)
        val.pack(anchor="w")
        return val

    def _divider(self):
        ctk.CTkFrame(self, fg_color=BORDER, width=1).pack(
            side="left", fill="y", pady=8)

    def update_speed(self, result: dict):
        dl = result.get("download_mbps")
        ul = result.get("upload_mbps")
        ping = result.get("ping_ms")
        self.dl_val.configure(text=f"{dl} Мбит/с" if dl else "N/A")
        self.ul_val.configure(text=f"{ul} Мбит/с" if ul else "N/A")
        self.ping_val.configure(text=f"{ping} ms" if ping else "N/A")

    def update_ping(self, ping_ms, loss_pct):
        if ping_ms is not None:
            self.ping_val.configure(text=f"{ping_ms} ms")
        if loss_pct is not None:
            color = "#4CAF50" if loss_pct == 0 else ("#FF9800" if loss_pct < 10 else "#F44336")
            self.loss_val.configure(text=f"{loss_pct}%", text_color=color)
```

- [ ] **Step 2: Commit**

```bash
git add widgets/speed_bar.py
git commit -m "feat: SpeedBar widget"
```

---

## Task 9: Full Check Tab

**Files:**
- Create: `tabs/full_check.py`

- [ ] **Step 1: Implement tabs/full_check.py**

```python
# tabs/full_check.py
import json
import queue
import threading
from pathlib import Path

import customtkinter as ctk

from engine.checker import run_checks
from widgets.service_card import ServiceCard
from widgets.speed_bar import SpeedBar

DARK_BG = "#16161f"
DARKER_BG = "#111118"
BORDER = "#2a2a3a"
ACCENT = "#5b6af5"
MUTED = "#555566"

_SERVICES_PATH = Path(__file__).parent.parent / "services.json"

TIER_COLORS = {
    "S": "#4CAF50",
    "A": "#42a5f5",
    "B": "#FFC107",
    "C": "#FF9800",
    "F": "#F44336",
}


def _load_services():
    with open(_SERVICES_PATH, encoding="utf-8") as f:
        return json.load(f)["services"]


class FullCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.result_queue = result_queue
        self.all_services = _load_services()
        self.cards: dict[str, ServiceCard] = {}
        self._selected: set[str] = {s["id"] for s in self.all_services}
        self._running = False

        self._build()

    def _build(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=DARKER_BG, width=210,
                                     corner_radius=0, border_width=1,
                                     border_color=BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        right = ctk.CTkFrame(self, fg_color=DARK_BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_sidebar(self):
        scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        for cat, services in categories.items():
            ctk.CTkLabel(scroll, text=cat.upper(), font=("Segoe UI", 9, "bold"),
                         text_color=MUTED).pack(anchor="w", padx=4, pady=(10, 2))
            for svc in services:
                var = ctk.BooleanVar(value=True)
                cb = ctk.CTkCheckBox(
                    scroll, text=svc["icon"] + "  " + svc["name"],
                    variable=var, font=("Segoe UI", 12),
                    checkbox_width=16, checkbox_height=16,
                    fg_color=ACCENT, hover_color="#7b8ef5",
                    command=lambda sid=svc["id"], v=var: self._toggle(sid, v)
                )
                cb.pack(anchor="w", pady=2)
                self._checkboxes[svc["id"]] = cb

        self.run_btn = ctk.CTkButton(
            self.sidebar, text="▶  Запустить",
            font=("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            corner_radius=9, height=38,
            command=self._start_check
        )
        self.run_btn.pack(fill="x", padx=8, pady=8)

    def _build_right(self, parent):
        self.speed_bar = SpeedBar(parent)
        self.speed_bar.pack(fill="x", padx=12, pady=(12, 8))

        self.cards_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.cards_scroll.pack(fill="both", expand=True, padx=12)

        self._build_cards()

        self.verdict_frame = ctk.CTkFrame(parent, fg_color="#1a1a26",
                                           corner_radius=10, border_width=1,
                                           border_color=BORDER)
        self.verdict_frame.pack(fill="x", padx=12, pady=(8, 12))
        self.verdict_icon = ctk.CTkLabel(self.verdict_frame, text="🛡",
                                          font=("Segoe UI", 28))
        self.verdict_icon.pack(side="left", padx=16, pady=12)
        verdict_text_frame = ctk.CTkFrame(self.verdict_frame, fg_color="transparent")
        verdict_text_frame.pack(side="left", fill="both", expand=True)
        self.verdict_title = ctk.CTkLabel(verdict_text_frame,
                                           text="Нажми Запустить",
                                           font=("Segoe UI", 15, "bold"))
        self.verdict_title.pack(anchor="w")
        self.verdict_sub = ctk.CTkLabel(verdict_text_frame,
                                         text="Выбери сервисы и запусти проверку",
                                         font=("Segoe UI", 11), text_color=MUTED)
        self.verdict_sub.pack(anchor="w")
        self.verdict_score = ctk.CTkLabel(self.verdict_frame, text="",
                                           font=("Segoe UI", 32, "bold"))
        self.verdict_score.pack(side="right", padx=16)

    def _build_cards(self):
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()
        self.cards.clear()

        categories: dict[str, list] = {}
        for svc in self.all_services:
            if svc["id"] in self._selected:
                categories.setdefault(svc["category"], []).append(svc)

        for cat, services in categories.items():
            ctk.CTkLabel(self.cards_scroll, text=cat.upper(),
                         font=("Segoe UI", 10, "bold"),
                         text_color=MUTED).pack(anchor="w", pady=(8, 4))
            grid = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
            grid.pack(fill="x")
            for i, svc in enumerate(services):
                card = ServiceCard(grid, svc)
                card.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
                grid.grid_columnconfigure(i % 3, weight=1)
                self.cards[svc["id"]] = card

    def _toggle(self, service_id: str, var: ctk.BooleanVar):
        if var.get():
            self._selected.add(service_id)
        else:
            self._selected.discard(service_id)

    def _start_check(self):
        if self._running:
            return
        self._running = True
        self.run_btn.configure(state="disabled", text="Проверка...")

        self._build_cards()
        for card in self.cards.values():
            card.set_checking()

        services = [s for s in self.all_services if s["id"] in self._selected]
        thread = threading.Thread(
            target=run_checks, args=(services, self.result_queue), daemon=True
        )
        thread.start()

    def handle_result(self, msg: dict):
        if msg["type"] == "service":
            card = self.cards.get(msg["id"])
            if card:
                card.update_result(msg)
                # Update speed bar ping from first result
                if msg.get("ping_ms") is not None:
                    self.speed_bar.update_ping(msg["ping_ms"], msg.get("loss_pct"))

        elif msg["type"] == "speed":
            self.speed_bar.update_speed(msg)

        elif msg["type"] == "verdict":
            self._running = False
            self.run_btn.configure(state="normal", text="▶  Запустить снова")
            color = TIER_COLORS.get(msg["tier"], "#e0e0e0")
            self.verdict_title.configure(text=msg["message"], text_color=color)
            self.verdict_sub.configure(
                text=f"Доступно {msg['accessible_count']} из {msg['total_count']} сервисов"
            )
            self.verdict_score.configure(
                text=f"{msg['score']}/10", text_color=color
            )
```

- [ ] **Step 2: Verify app runs with full check tab**

```bash
python main.py
```
Expected: Full check tab visible with sidebar checkboxes and empty cards. Clicking "Запустить" starts checks and cards update.

- [ ] **Step 3: Commit**

```bash
git add tabs/full_check.py
git commit -m "feat: full check tab with sidebar, cards grid, verdict"
```

---

## Task 10: Custom Check Tab

**Files:**
- Create: `tabs/custom_check.py`

- [ ] **Step 1: Implement tabs/custom_check.py**

```python
# tabs/custom_check.py
import queue
import threading
from urllib.parse import urlparse

import customtkinter as ctk

from engine.ping import ping_host
from engine.http_check import http_check

DARK_BG = "#16161f"
CARD_BG = "#1a1a26"
BORDER = "#2a2a3a"
ACCENT = "#5b6af5"
MUTED = "#555566"
COLOR_OK = "#4CAF50"
COLOR_BAD = "#F44336"
COLOR_WARN = "#FF9800"


class CustomCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self._running = False
        self._build()

    def _build(self):
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="Проверить ресурс",
                     font=("Segoe UI", 18, "bold")).pack(pady=(0, 4))
        ctk.CTkLabel(center, text="Введи URL или hostname",
                     font=("Segoe UI", 12), text_color=MUTED).pack(pady=(0, 20))

        input_row = ctk.CTkFrame(center, fg_color="transparent")
        input_row.pack()

        self.url_entry = ctk.CTkEntry(
            input_row, width=380, height=40,
            placeholder_text="https://example.com или example.com",
            font=("Segoe UI", 13),
            fg_color=CARD_BG, border_color=BORDER
        )
        self.url_entry.pack(side="left", padx=(0, 8))

        self.check_btn = ctk.CTkButton(
            input_row, text="Проверить", width=110, height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            command=self._start_check
        )
        self.check_btn.pack(side="left")

        self.result_frame = ctk.CTkFrame(
            center, fg_color=CARD_BG, corner_radius=12,
            border_width=1, border_color=BORDER, width=500
        )
        self.result_frame.pack(pady=20, fill="x")
        self.result_frame.pack_propagate(False)
        self.result_frame.configure(height=0)  # hidden initially

        self._result_labels = {}

    def _show_result(self, ping_result: dict, http_result: dict, url: str):
        for w in self.result_frame.winfo_children():
            w.destroy()

        accessible = http_result["accessible"]
        ping_ms = ping_result.get("ping_ms")
        loss_pct = ping_result.get("loss_pct", 0.0)

        color = COLOR_OK if accessible else COLOR_BAD
        status_text = "Доступен ✓" if accessible else "Недоступен ✗"

        self.result_frame.configure(height=160)

        top = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(top, text=url, font=("Segoe UI", 13, "bold"),
                     text_color="#cccccc").pack(side="left")
        ctk.CTkLabel(top, text=status_text, font=("Segoe UI", 12, "bold"),
                     text_color=color).pack(side="right")

        stats = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        stats.pack(fill="x", padx=16, pady=(0, 14))

        def stat(label, value, color="#e0e0e0"):
            f = ctk.CTkFrame(stats, fg_color="transparent")
            f.pack(side="left", padx=(0, 24))
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 9),
                         text_color=MUTED).pack(anchor="w")
            ctk.CTkLabel(f, text=value, font=("Segoe UI", 16, "bold"),
                         text_color=color).pack(anchor="w")

        ping_color = COLOR_OK if ping_ms and ping_ms < 100 else (COLOR_WARN if ping_ms else COLOR_BAD)
        stat("ПИНГ", f"{ping_ms} ms" if ping_ms else "—", ping_color)

        loss_color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
        stat("ПОТЕРИ", f"{loss_pct}%", loss_color)

        sc = http_result.get("status_code")
        stat("HTTP", str(sc) if sc else "—")

        rt = http_result.get("response_ms")
        stat("ОТВЕТ", f"{rt} ms" if rt else "—")

    def _start_check(self):
        if self._running:
            return
        raw = self.url_entry.get().strip()
        if not raw:
            return

        if not raw.startswith("http"):
            raw = "https://" + raw

        self._running = True
        self.check_btn.configure(state="disabled", text="Проверка...")

        def worker():
            host = urlparse(raw).hostname or raw
            ping_result = ping_host(host)
            http_result = http_check(raw)
            self.after(0, lambda: self._on_done(ping_result, http_result, raw))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, ping_result, http_result, url):
        self._show_result(ping_result, http_result, url)
        self._running = False
        self.check_btn.configure(state="normal", text="Проверить")

    def handle_result(self, msg: dict):
        pass  # custom tab doesn't use the shared queue
```

- [ ] **Step 2: Verify custom tab works**

```bash
python main.py
```
Expected: Custom tab shows input field. Entering a URL and clicking "Проверить" shows a result card with ping, loss, HTTP status, response time.

- [ ] **Step 3: Commit**

```bash
git add tabs/custom_check.py
git commit -m "feat: custom check tab with single resource testing"
```

---

## Task 11: PyInstaller portable build

**Files:**
- Create: `build.bat`

- [ ] **Step 1: Create build.bat**

```bat
@echo off
echo Building VPN Checker portable exe...
call .venv\Scripts\activate
pyinstaller --onefile --windowed --name VPN-Checker ^
  --add-data "services.json;." ^
  --icon NONE ^
  main.py
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
```

- [ ] **Step 2: Run the build**

```bash
cmd /c build.bat
```
Expected: `dist/VPN-Checker.exe` created, ~35-50 MB, runs without Python installed.

- [ ] **Step 3: Test the exe**

Double-click `dist/VPN-Checker.exe`. App should open with full functionality.

- [ ] **Step 4: Commit**

```bash
git add build.bat
git commit -m "feat: PyInstaller build script for portable exe"
```

---

## Task 12: Push to GitHub

- [ ] **Step 1: Push all commits**

```bash
git push origin master
```

- [ ] **Step 2: Verify on GitHub**

Open https://github.com/krazzer00/vpn_cheker — all commits visible, all files present.
