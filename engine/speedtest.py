# engine/speedtest.py
"""
Speed measurement via Cloudflare speed test endpoints.
Uses concurrent HTTP streams for download/upload, HTTP RTT for ping.
No third-party speedtest library — fully compatible with PyInstaller.
"""
import time
import threading
from typing import TypedDict

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "VPNChecker/2.0"

_DL_URL  = "https://speed.cloudflare.com/__down?bytes=25000000"   # 25 MB
_UL_URL  = "https://speed.cloudflare.com/__up"
_PING_URL = "https://speed.cloudflare.com/cdn-cgi/trace"
_THREADS  = 4
_TIMEOUT  = 30


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


# ── helpers ────────────────────────────────────────────────────────────────────

def _measure_ping(samples: int = 5) -> float:
    """Average HTTP RTT in ms (fastest 3 of 5 samples)."""
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            _SESSION.get(_PING_URL, timeout=5)
        except Exception:
            continue
        times.append((time.perf_counter() - t0) * 1000)
    if not times:
        return 0.0
    times.sort()
    return round(sum(times[:3]) / min(3, len(times)), 1)


def _download_worker(results: list, idx: int) -> None:
    try:
        t0 = time.perf_counter()
        r = _SESSION.get(_DL_URL, timeout=_TIMEOUT, stream=True)
        total = 0
        for chunk in r.iter_content(65536):
            total += len(chunk)
        elapsed = time.perf_counter() - t0
        if elapsed > 0:
            results[idx] = total / elapsed  # bytes/sec
    except Exception:
        results[idx] = 0.0


def _upload_worker(results: list, idx: int, size: int = 8_000_000) -> None:
    try:
        data = b"0" * size
        t0 = time.perf_counter()
        _SESSION.post(_UL_URL, data=data, timeout=_TIMEOUT,
                      headers={"Content-Type": "application/octet-stream"})
        elapsed = time.perf_counter() - t0
        if elapsed > 0:
            results[idx] = size / elapsed
    except Exception:
        results[idx] = 0.0


# ── public API ─────────────────────────────────────────────────────────────────

def run_speedtest() -> SpeedResult:
    try:
        ping_ms = _measure_ping()

        # --- download ---
        dl_results = [0.0] * _THREADS
        threads = [threading.Thread(target=_download_worker, args=(dl_results, i))
                   for i in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        download_bps = sum(dl_results)

        # --- upload ---
        ul_results = [0.0] * _THREADS
        threads = [threading.Thread(target=_upload_worker, args=(ul_results, i))
                   for i in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        upload_bps = sum(ul_results)

        return SpeedResult(
            download_mbps=round(download_bps / 1_000_000, 1),
            upload_mbps=round(upload_bps / 1_000_000, 1),
            ping_ms=ping_ms,
            error=None,
        )

    except Exception as e:
        return SpeedResult(
            download_mbps=None,
            upload_mbps=None,
            ping_ms=None,
            error=str(e),
        )
