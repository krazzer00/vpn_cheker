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
    ICMP ping with packet loss.
    When SOCKS5 proxy is active, falls back to TCP-through-SOCKS5
    (ICMP cannot be tunnelled through a SOCKS5 proxy).
    """
    from engine.proxy import is_enabled, socks5_host, socks5_port
    if is_enabled():
        return _socks5_tcp_ping(host, 443, count,
                                socks5_host(), socks5_port())

    # Normal ICMP path
    try:
        ping3.ping(host, timeout=PING_TIMEOUT, unit="ms")
    except PermissionError:
        return tcp_ping(host, 443)

    try:
        results = []
        for _ in range(count):
            rtt = ping3.ping(host, timeout=PING_TIMEOUT, unit="ms")
            results.append(rtt)
        lost  = sum(1 for r in results if r is None)
        valid = [r for r in results if r is not None]
        if not valid:
            # All ICMP probes timed out — ICMP is likely blocked by firewall
            return tcp_ping(host, 443)
        return PingResult(
            ping_ms=round(sum(valid) / len(valid), 1),
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
            loss_pct=None,
            method="tcp",
        )
    except OSError:
        return PingResult(ping_ms=None, loss_pct=100.0, method="tcp")


def _socks5_tcp_ping(host: str, port: int, count: int,
                     proxy_host: str, proxy_port: int) -> PingResult:
    """TCP-through-SOCKS5 latency measurement (used when proxy is active)."""
    import socks  # PySocks

    times: list[float] = []
    for _ in range(count):
        try:
            s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            s.set_proxy(socks.SOCKS5, proxy_host, proxy_port, rdns=True)
            s.settimeout(3.0)
            t0 = time.perf_counter()
            s.connect((host, port))
            times.append((time.perf_counter() - t0) * 1000)
            s.close()
        except Exception:
            pass

    if not times:
        return PingResult(ping_ms=None, loss_pct=100.0, method="socks5-tcp")
    return PingResult(
        ping_ms=round(sum(times) / len(times), 1),
        loss_pct=round((1 - len(times) / count) * 100, 1),
        method="socks5-tcp",
    )
