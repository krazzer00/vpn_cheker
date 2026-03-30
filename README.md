<div align="center">

# 🛡 VPN Checker

**Десктопное приложение для Windows — проверяет, работает ли ваш VPN**

Тестирует доступность сервисов, определяет гео-блокировки для AI, измеряет реальную скорость интернета

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Windows-x64-0078D6?logo=windows&logoColor=white)](https://github.com/krazzer00/vpn_cheker/releases)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)

</div>

---

## ✨ Возможности

| | |
|---|---|
| 🌐 **Проверка сервисов** | YouTube, Telegram, Instagram, GitHub, Discord, VRChat и другие |
| 🤖 **AI регион** | Определяет, доступны ли Claude, ChatGPT и Gemini в вашем регионе |
| ⚡ **Замер скорости** | Официальный Ookla Speedtest CLI — точные значения с живым прогрессом |
| 🔀 **SOCKS5 прокси** | Один клик — весь трафик проверок идёт через 127.0.0.1:2080 |
| 🔒 **Публичный DNS** | Все запросы резолвятся через 8.8.8.8 / 1.1.1.1, минуя локальный DNS |
| 📋 **История проверок** | Каждый результат сохраняется локально с временем и IP |
| 🎨 **5 тем оформления** | Dark, Midnight Blue, Forest, Crimson, Slate |
| 📦 **Портабельный .exe** | Один файл, без установки |

---

## 🚀 Быстрый старт

### Готовый .exe

1. Скачать `VPN-Checker.exe` из [Releases](../../releases)
2. Положить рядом `speedtest.exe` ([скачать с Ookla](https://www.speedtest.net/apps/cli))
3. Запустить

### Из исходников

```bat
git clone https://github.com/krazzer00/vpn_cheker.git
cd vpn_cheker

:: Установить зависимости (нужен uv)
uv sync

:: Запустить
uv run main.py

:: Собрать .exe
build.bat
```

> Перед сборкой положите `speedtest.exe` в корень проекта — он автоматически включится в бандл.

---

## 🗂 Структура проекта

```
vpn_cheker/
├── main.py              # Точка входа, установка DNS-хука
├── app.py               # Главное окно, вкладки, IP-бейдж
├── theme.py             # Темы и палитры
├── services.json        # Список сервисов (можно редактировать)
├── VPN-Checker.spec     # Конфиг PyInstaller
├── build.bat            # Сборка одной командой
├── speedtest.exe        # Ookla Speedtest CLI (скачать отдельно)
│
├── engine/              # Логика проверок
│   ├── checker.py       # Оркестратор (потоки, очередь)
│   ├── http_check.py    # HTTP + проверка AI-региона
│   ├── ping.py          # ICMP/TCP пинг с SOCKS5 fallback
│   ├── speedtest.py     # Обёртка над Ookla CLI (live JSONL)
│   ├── dns.py           # Хук публичного DNS
│   ├── proxy.py         # Состояние SOCKS5 прокси
│   ├── verdict.py       # Итоговый вердикт
│   ├── history.py       # История результатов
│   └── config.py        # Настройки
│
├── tabs/                # Вкладки интерфейса
├── widgets/             # UI-компоненты (карточки, спидбар)
└── tests/               # pytest тесты
```

---

## ⚙️ Конфигурация сервисов

Сервисы описаны в `services.json` — можно добавлять свои:

```json
{
  "id": "myservice",
  "name": "My Service",
  "icon": "🔥",
  "category": "Other",
  "check_url": "https://myservice.com",
  "check_type": "http",
  "port": 443,
  "enabled": true
}
```

**`check_type`:**
- `http` — проверяет доступность по HTTP
- `ai_region` — считает сервис доступным при ответах 200/400/401/422 (без ключа — нормально), при 403 или таймауте — гео-блок

---

## 🔀 SOCKS5 прокси

Кнопка **SOCKS5** в шапке приложения — один клик, и все проверки идут через `127.0.0.1:2080`:

- HTTP-запросы используют схему `socks5h://` — DNS резолвится на стороне прокси, утечек нет
- Пинг идёт через TCP connect via PySocks (`rdns=True`)
- Замер скорости работает напрямую (Ookla CLI независим)

---

## 🧪 Тесты

```bat
uv run pytest tests/ -v
```

---

## 📦 Зависимости

| Пакет | Назначение |
|---|---|
| PyQt5 | Интерфейс |
| requests | HTTP-проверки |
| PySocks | SOCKS5 прокси |
| ping3 | ICMP пинг |

Скорость измеряется через официальный [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) — не библиотека Python.

---

<div align="center">

MIT License

</div>
