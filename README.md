# VPN Checker

A desktop app for Windows that checks whether your VPN is working correctly — tests service accessibility, measures real network speed, and detects geo-restrictions for AI services.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Service accessibility check** — tests reachability of popular services (YouTube, Telegram, Instagram, GitHub, Discord, VRChat, etc.)
- **AI region detection** — verifies whether Claude, ChatGPT, and Gemini are accessible from your current region (detects geo-blocks)
- **Real speed measurement** — uses the official Ookla Speedtest CLI for accurate download/upload/ping results with live progress
- **SOCKS5 proxy support** — toggle all checks through a local SOCKS5 proxy (127.0.0.1:2080) with one click
- **Public DNS** — all DNS lookups go through 8.8.8.8 / 1.1.1.1 to avoid local DNS poisoning
- **Check history** — every check is saved locally with timestamp and IP info
- **Custom checks** — run checks for individual services on demand
- **5 UI themes** — Dark, Midnight Blue, Forest, Crimson, Slate
- **Portable build** — single `.exe`, no installation needed

---

## Screenshots

> Run a check, watch cards update in real time, get a verdict with speed stats.

---

## Quick Start (pre-built)

1. Download `VPN-Checker.exe` from [Releases](../../releases)
2. Place `speedtest.exe` (Ookla CLI) in the same folder — [download here](https://www.speedtest.net/apps/cli)
3. Run `VPN-Checker.exe`

---

## Build from Source

**Requirements:** Python 3.11+, [uv](https://github.com/astral-sh/uv), Windows x64

```bat
# Install dependencies
uv sync

# Run from source
uv run main.py

# Build portable .exe
build.bat
```

The built executable will be at `dist/VPN-Checker.exe`.

> **Note:** `speedtest.exe` (Ookla CLI for Windows) must be present in the project root before building — it gets bundled automatically via the spec file.

---

## Project Structure

```
vpn_cheker/
├── main.py              # Entry point, DNS hook installation
├── app.py               # Main window, tab routing, IP badge
├── theme.py             # Theme definitions and palette
├── services.json        # Service definitions (editable)
├── VPN-Checker.spec     # PyInstaller build spec
├── build.bat            # One-click build script
├── speedtest.exe        # Ookla Speedtest CLI (not in repo, download separately)
│
├── engine/
│   ├── checker.py       # Main check orchestrator (threading)
│   ├── http_check.py    # HTTP reachability + AI region checks
│   ├── ping.py          # ICMP/TCP ping with SOCKS5 fallback
│   ├── speedtest.py     # Ookla CLI wrapper with live JSONL streaming
│   ├── dns.py           # Public DNS hook (patches socket.getaddrinfo)
│   ├── proxy.py         # SOCKS5 proxy state and requests integration
│   ├── verdict.py       # Overall check verdict logic
│   ├── history.py       # Local check history (JSON)
│   └── config.py        # Settings persistence
│
├── tabs/
│   ├── full_check.py    # Full check tab UI
│   ├── custom_check.py  # Custom check tab UI
│   ├── history.py       # History tab UI
│   └── settings.py      # Settings tab UI
│
├── widgets/
│   ├── service_card.py  # Individual service result card
│   ├── speed_bar.py     # Live speed measurement bar
│   └── smooth_scroll.py # Smooth scroll area
│
└── tests/               # pytest test suite
```

---

## Services

Services are defined in `services.json`. You can add, remove, or disable entries.

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `name` | Display name |
| `icon` | Emoji icon |
| `category` | Group label (AI, Media, Social, Other) |
| `check_url` | URL to test |
| `check_type` | `http` or `ai_region` |
| `port` | TCP port for ping fallback |
| `enabled` | Include in full check |

**`ai_region`** check sends a request and considers the service reachable if the server responds (even with 401/400/422 — meaning it's accessible but auth is missing). A 403 or timeout means geo-blocked.

---

## SOCKS5 Proxy

Click the **SOCKS5** button in the header to route all checks through `127.0.0.1:2080`.

- HTTP/HTTPS checks use `socks5h://` (proxy-side DNS, no local leak)
- Ping uses TCP connect through PySocks with `rdns=True`
- Speed test does **not** go through the proxy (Ookla CLI runs independently)

---

## Running Tests

```bat
uv run pytest tests/ -v
```

---

## Dependencies

| Package | Purpose |
|---|---|
| PyQt5 | GUI framework |
| requests | HTTP checks |
| PySocks | SOCKS5 proxy support |
| ping3 | ICMP ping |

Speed measurement uses the official [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) binary — not a Python library.

---

## License

MIT
