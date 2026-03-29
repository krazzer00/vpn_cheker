# engine/ping.py
import socket
import time
from typing import TypedDict

import ping3

PING_TIMEOUT = 2
PING_COUNT = 4


class PingResult(TypedDict):
    ping_ms: float | None
    loss_pct: float | None
    method: str


def ping_host(host: str, count: int = PING_COUNT) -> PingResult:
    """
    ICMP ping with packet loss. Falls back to TCP on permission error.
    Returns: {ping_ms, loss_pct, method}
    """
    # Probe once to detect PermissionError before running the full loop
    try:
        ping3.ping(host, timeout=PING_TIMEOUT, unit="ms")
    except PermissionError:
        return tcp_ping(host, 443)

    try:
        results = []
        for _ in range(count):
            rtt = ping3.ping(host, timeout=PING_TIMEOUT, unit="ms")
            results.append(rtt)
        lost = sum(1 for r in results if r is None)
        valid = [r for r in results if r is not None]
        return PingResult(
            ping_ms=round(sum(valid) / len(valid), 1) if valid else None,
            loss_pct=round((lost / count) * 100, 1),
            method="icmp",
        )
    except (OSError, Exception):
        return tcp_ping(host, 443)


def tcp_ping(host: str, port: int, timeout: float = 2.0) -> PingResult:
    """TCP connect as ping fallback. Loss cannot be measured via TCP."""
    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
        return PingResult(
            ping_ms=round(elapsed, 1),
            loss_pct=None,  # TCP single-shot cannot measure loss
            method="tcp",
        )
    except OSError:
        return PingResult(
            ping_ms=None,
            loss_pct=100.0,
            method="tcp",
        )
