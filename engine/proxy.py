# engine/proxy.py
"""
Global SOCKS5 proxy toggle.
All engine modules read from here; the UI writes to here.
"""

_enabled: bool = False
_HOST: str = "127.0.0.1"
_PORT: int  = 2080


def is_enabled() -> bool:
    return _enabled


def set_enabled(v: bool) -> None:
    global _enabled
    _enabled = v


def requests_proxies() -> dict | None:
    """Proxies dict for requests.  socks5h = proxy-side DNS (no local leak)."""
    if not _enabled:
        return None
    url = f"socks5h://{_HOST}:{_PORT}"
    return {"http": url, "https": url}


def socks5_host() -> str:
    return _HOST


def socks5_port() -> int:
    return _PORT
