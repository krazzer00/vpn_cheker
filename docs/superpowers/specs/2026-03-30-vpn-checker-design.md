# VPN Checker — Design Spec
**Date:** 2026-03-30

## Overview
Desktop application for testing VPN effectiveness. Shows which services are accessible through the VPN, with ping, packet loss, speed per service, and an overall verdict.

## Technology
- **Language:** Python 3.11+
- **GUI:** CustomTkinter (dark theme)
- **Networking:** ping3, requests, speedtest-cli
- **Build:** PyInstaller --onefile portable .exe (~35-45 MB)

## Architecture

Three layers:
1. **GUI** — CustomTkinter window with tabs. UI updates via a thread-safe queue polled every 100ms on the main thread.
2. **Check Engine** — ThreadPoolExecutor runs all service checks in parallel. Each check reports results back through the queue.
3. **Config** — `services.json` defines all services (url, check method, icon, category). No code changes needed to add a service.

## File Structure

```
vpn_cheker/
├── main.py
├── app.py
├── tabs/
│   ├── full_check.py
│   └── custom_check.py
├── widgets/
│   ├── service_card.py
│   └── speed_bar.py
├── engine/
│   ├── checker.py
│   ├── ping.py
│   ├── http_check.py
│   └── speedtest.py
├── services.json
└── requirements.txt
```

## Services Checked

### AI Services
| Service | Region Check Method |
|---------|-------------------|
| Claude AI | POST api.anthropic.com/v1/messages — 401=accessible, 403/timeout=blocked |
| ChatGPT | GET api.openai.com/v1/models |
| Gemini | GET generativelanguage.googleapis.com/v1/models |

### Media / Social
YouTube, Twitch, Instagram, VK, Telegram, GitHub, Discord, VRChat, VRCDN

## Check Methods

- **Ping:** ping3 (ICMP). Fallback to TCP ping on port 443 if ICMP unavailable (no admin rights).
- **Packet loss:** 4 ICMP packets, count lost.
- **HTTP availability:** GET/HEAD with 5s timeout. HTTP 200-299 = accessible.
- **Regional AI check:** Hit the real API endpoint. 401 Unauthorized = service is accessible in region (just no key). 403 / connection reset / timeout = geo-blocked.
- **Speed:** speedtest-cli, runs once in parallel with service checks. Reports download + upload Mbps.

## Timeouts
- Ping: 2s per packet
- HTTP: 5s
- Speedtest: 30s

## UI Layout

### Full Check Tab
- **Left sidebar:** Checkboxes grouped by category (AI, Media, Social, Other). "Run" button at bottom.
- **Top bar:** Overall ping / download / upload / packet loss.
- **Main area:** Service cards in a grid, grouped by category. Each card shows: status badge, ping, packet loss, region check result, speed (where applicable).
- **Bottom verdict:** Score (X/10), summary text, actionable note if issues found.

### Custom Check Tab
- Single input field for URL/hostname.
- "Check" button.
- Results card: ping, packet loss, HTTP status, response time, speed.
- No full test needed — instant single-resource check.

## Verdict Algorithm
Each service contributes to the score:
- Accessible + low ping (<100ms) + 0% loss = 1.0 point
- Accessible + high ping (100-200ms) OR minor loss = 0.7 point
- Accessible + very high ping (>200ms) = 0.5 point
- Inaccessible = 0 points

Score = (sum / max_possible) × 10. Displayed as X/10.
**Score tiers with meme verdicts (randomized within tier):**

- **9-10:** "Топчик, всё летает 🚀" / "Пиздатый VPN, уважаю" / "Ни одна собака не заблочила, красавчик"
- **7-8:** "Норм впн, жить можно 👍" / "Почти идеально, но могло быть лучше" / "Сойдёт для сельской местности"
- **5-6:** "Ну такое... 😐" / "Работает через жопу, но работает" / "VPN страдает, но держится"
- **3-4:** "Это провал, Карл 💀" / "Твой VPN умирает на наших глазах" / "Роскомнадзор победил, поздравляю"
- **0-2:** "Это не VPN, это позор семьи 🗑" / "Братан, ты забыл включить VPN?" / "Полный пиздец, меняй провайдера"

## Error Handling
- Each worker wrapped in try/except — one failing check doesn't affect others.
- Timeout = service marked "Unavailable", loss 100%.
- If speedtest fails: show "N/A", don't block other results.

## Build
```
pyinstaller --onefile --windowed --name VPN-Checker \
  --add-data "services.json;." \
  main.py
```
Output: `dist/VPN-Checker.exe` — single portable file, no Python required.
