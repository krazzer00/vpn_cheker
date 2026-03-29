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
