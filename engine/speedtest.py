# engine/speedtest.py
"""
Speed measurement via Cloudflare speed test endpoints.
Per-worker sessions, streaming download, fixed-blob upload, timed windows.
"""
import os
import time
import threading
from typing import TypedDict

import requests

_PING_URL = "https://speed.cloudflare.com/cdn-cgi/trace"
_DL_URL   = "https://speed.cloudflare.com/__down?bytes=104857600"  # 100 MB ceiling
_UL_URL   = "https://speed.cloudflare.com/__up"

_THREADS  = 4
_DL_SECS  = 8.0
_UL_SECS  = 8.0
_CHUNK    = 65_536
_UL_BLOB  = 256 * 1024           # 256 KB per POST — works for 1 Mbps … 1 Gbps
_HDR      = {"User-Agent": "VPNChecker/2.0"}


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps:   float | None
    ping_ms:       float | None
    error:         str | None


# ── ping ───────────────────────────────────────────────────────────────────────

def _measure_ping(samples: int = 5) -> float:
    latencies: list[float] = []
    for _ in range(samples):
        try:
            t0 = time.perf_counter()
            requests.get(_PING_URL, timeout=4, headers=_HDR)
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception:
            pass
    if not latencies:
        return 0.0
    latencies.sort()
    keep = latencies[:max(1, len(latencies) * 2 // 3)]  # drop slowest third
    return round(sum(keep) / len(keep), 1)


# ── download ───────────────────────────────────────────────────────────────────

def _dl_worker(results: list, idx: int, stop: threading.Event) -> None:
    total = 0
    try:
        with requests.Session() as sess:
            sess.headers.update(_HDR)
            while not stop.is_set():
                try:
                    with sess.get(_DL_URL, stream=True, timeout=_DL_SECS + 10) as r:
                        r.raise_for_status()
                        for chunk in r.iter_content(_CHUNK):
                            if stop.is_set():
                                break
                            total += len(chunk)
                except Exception:
                    break
    except Exception:
        pass
    results[idx] = total


# ── upload ─────────────────────────────────────────────────────────────────────

def _ul_worker(results: list, idx: int, stop: threading.Event) -> None:
    total = 0
    blob = os.urandom(_UL_BLOB)
    hdrs = {**_HDR,
            "Content-Type":   "application/octet-stream",
            "Content-Length": str(_UL_BLOB)}
    try:
        with requests.Session() as sess:
            sess.headers.update(hdrs)
            while not stop.is_set():
                try:
                    sess.post(_UL_URL, data=blob, timeout=_UL_SECS + 10)
                    total += _UL_BLOB
                except Exception:
                    break
    except Exception:
        pass
    results[idx] = total


# ── timed parallel runner ──────────────────────────────────────────────────────

def _run_timed(worker_fn, secs: float) -> float:
    stop    = threading.Event()
    results = [0] * _THREADS
    threads = [
        threading.Thread(target=worker_fn, args=(results, i, stop), daemon=True)
        for i in range(_THREADS)
    ]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    time.sleep(secs)
    stop.set()
    for t in threads:
        t.join(secs + 15)
    elapsed = max(time.perf_counter() - t0, 0.001)
    return sum(results) / elapsed          # bytes / second


# ── public API ─────────────────────────────────────────────────────────────────

def run_speedtest() -> SpeedResult:
    try:
        ping_ms      = _measure_ping()
        download_bps = _run_timed(_dl_worker, _DL_SECS)
        upload_bps   = _run_timed(_ul_worker, _UL_SECS)
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
