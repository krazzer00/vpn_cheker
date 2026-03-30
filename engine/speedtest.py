# engine/speedtest.py
"""
Speed measurement via Cloudflare speed test endpoints.
Time-bounded parallel streams: measure bytes transferred in N seconds → Mbps.
"""
import time
import threading
from typing import TypedDict

import requests

_PING_URL  = "https://speed.cloudflare.com/cdn-cgi/trace"
_DL_URL    = "https://speed.cloudflare.com/__down?bytes=1000000000"   # 1 GB ceiling
_UL_URL    = "https://speed.cloudflare.com/__up"

_THREADS      = 4
_TEST_SECS    = 10.0   # measure for this many seconds per direction
_JOIN_TIMEOUT = _TEST_SECS + 8
_CHUNK        = 65_536
_UL_CHUNK     = 65_536


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


# ── ping ───────────────────────────────────────────────────────────────────────

def _measure_ping(samples: int = 6) -> float:
    times: list[float] = []
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            requests.get(_PING_URL, timeout=5,
                         headers={"User-Agent": "VPNChecker/2.0"})
        except Exception:
            continue
        times.append((time.perf_counter() - t0) * 1000)
    if not times:
        return 0.0
    times.sort()
    best = times[:max(1, len(times) - 1)]   # drop worst outlier
    return round(sum(best) / len(best), 1)


# ── download ───────────────────────────────────────────────────────────────────

def _dl_worker(results: list, idx: int, stop: threading.Event) -> None:
    total = 0
    try:
        r = requests.get(
            _DL_URL, stream=True, timeout=_JOIN_TIMEOUT,
            headers={"User-Agent": "VPNChecker/2.0"},
        )
        for chunk in r.iter_content(_CHUNK):
            if stop.is_set():
                break
            total += len(chunk)
    except Exception:
        pass
    results[idx] = total


def _measure_download() -> float:
    stop    = threading.Event()
    results = [0] * _THREADS
    threads = [threading.Thread(target=_dl_worker, args=(results, i, stop), daemon=True)
               for i in range(_THREADS)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    time.sleep(_TEST_SECS)
    stop.set()
    for t in threads:
        t.join(_JOIN_TIMEOUT)
    elapsed = time.perf_counter() - t0
    return sum(results) / elapsed if elapsed > 0 else 0.0


# ── upload ─────────────────────────────────────────────────────────────────────

def _ul_generator(stop: threading.Event):
    """Yield chunks until stop is set."""
    block = b"\x00" * _UL_CHUNK
    while not stop.is_set():
        yield block


def _ul_worker(results: list, idx: int, stop: threading.Event) -> None:
    total = 0
    try:
        while not stop.is_set():
            chunk_count = 0

            def gen():
                nonlocal chunk_count
                block = b"\x00" * _UL_CHUNK
                for _ in range(1024):           # max 64 MB per POST
                    if stop.is_set():
                        return
                    chunk_count += 1
                    yield block

            requests.post(
                _UL_URL,
                data=gen(),
                timeout=_JOIN_TIMEOUT,
                headers={
                    "Content-Type":   "application/octet-stream",
                    "User-Agent":     "VPNChecker/2.0",
                },
            )
            total += chunk_count * _UL_CHUNK
    except Exception:
        pass
    results[idx] = total


def _measure_upload() -> float:
    stop    = threading.Event()
    results = [0] * _THREADS
    threads = [threading.Thread(target=_ul_worker, args=(results, i, stop), daemon=True)
               for i in range(_THREADS)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    time.sleep(_TEST_SECS)
    stop.set()
    for t in threads:
        t.join(_JOIN_TIMEOUT)
    elapsed = time.perf_counter() - t0
    return sum(results) / elapsed if elapsed > 0 else 0.0


# ── public API ─────────────────────────────────────────────────────────────────

def run_speedtest() -> SpeedResult:
    try:
        ping_ms       = _measure_ping()
        download_bps  = _measure_download()
        upload_bps    = _measure_upload()

        return SpeedResult(
            download_mbps=round(download_bps / 1_000_000, 1),
            upload_mbps=round(upload_bps   / 1_000_000, 1),
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
