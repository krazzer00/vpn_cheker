# engine/speedtest.py
"""
Speed measurement via Cloudflare speed test endpoints.
Ping = TCP-connect RTT (no TLS overhead).
Download / upload = timed parallel streams, bytes-per-second.
"""
import os
import socket
import time
import threading
from typing import TypedDict

import requests

# ── constants ──────────────────────────────────────────────────────────────────

_CF_HOST  = "speed.cloudflare.com"
_DL_URL   = "https://speed.cloudflare.com/__down?bytes=26214400"  # 25 MB per request
_UL_URL   = "https://speed.cloudflare.com/__up"
_HDR      = {"User-Agent": "Mozilla/5.0 (VPNChecker/2.0)"}

_THREADS  = 4
_DL_SECS  = 8.0
_UL_SECS  = 8.0
_CHUNK    = 65_536
_UL_BLOB  = 262_144   # 256 KB per POST — good from 1 Mbps to 1 Gbps


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps:   float | None
    ping_ms:       float | None
    error:         str | None


# ── ping (TCP connect, no TLS overhead) ────────────────────────────────────────

def _measure_ping(host: str = _CF_HOST, port: int = 443,
                  samples: int = 6) -> float:
    times: list[float] = []
    for _ in range(samples):
        try:
            t0 = time.perf_counter()
            with socket.create_connection((host, port), timeout=3):
                pass
            times.append((time.perf_counter() - t0) * 1000)
        except Exception:
            pass
    if not times:
        return 0.0
    times.sort()
    keep = times[:max(1, len(times) - 1)]   # drop single worst outlier
    return round(sum(keep) / len(keep), 1)


# ── download ───────────────────────────────────────────────────────────────────

def _dl_worker(results: list, idx: int, stop: threading.Event) -> None:
    total  = 0
    errors = 0
    with requests.Session() as sess:
        sess.headers.update(_HDR)
        while not stop.is_set() and errors < 4:
            try:
                with sess.get(_DL_URL, stream=True, timeout=_DL_SECS + 10) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(_CHUNK):
                        if stop.is_set():
                            break
                        total += len(chunk)
                errors = 0
            except Exception:
                errors += 1
                time.sleep(0.3)
    results[idx] = total


# ── upload ─────────────────────────────────────────────────────────────────────

def _ul_worker(results: list, idx: int, stop: threading.Event) -> None:
    total  = 0
    errors = 0
    blob   = os.urandom(_UL_BLOB)
    hdrs   = {**_HDR,
              "Content-Type":   "application/octet-stream",
              "Content-Length": str(_UL_BLOB)}
    with requests.Session() as sess:
        sess.headers.update(hdrs)
        while not stop.is_set() and errors < 4:
            try:
                sess.post(_UL_URL, data=blob, timeout=_UL_SECS + 10)
                total += _UL_BLOB
                errors = 0
            except Exception:
                errors += 1
                time.sleep(0.3)
    results[idx] = total


# ── timed runner ───────────────────────────────────────────────────────────────

def _run_timed(worker_fn, secs: float) -> float:
    stop    = threading.Event()
    results = [0] * _THREADS
    threads = [
        threading.Thread(target=worker_fn, args=(results, i, stop), daemon=True)
        for i in range(_THREADS)
    ]
    t0 = time.perf_counter()
    # Stagger starts slightly so TCP handshakes don't all hit at once
    for i, t in enumerate(threads):
        t.start()
        if i < _THREADS - 1:
            time.sleep(0.05)
    time.sleep(secs)
    stop.set()
    for t in threads:
        t.join(secs + 20)
    elapsed = max(time.perf_counter() - t0, 0.001)
    return sum(results) / elapsed   # bytes / second


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
