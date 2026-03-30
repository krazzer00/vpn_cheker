# engine/speedtest.py
import concurrent.futures
import statistics
import time
from typing import TypedDict

import requests

_BASE = "https://speed.cloudflare.com"
_UA = {"User-Agent": "VPNChecker/1.0"}
TIMEOUT = 45

# Parallel streams — needed to saturate high-bandwidth connections
_DL_STREAMS = 4
_DL_BYTES = 10_000_000   # 10 MB per stream
_UL_STREAMS = 3
_UL_BYTES = 5_000_000    # 5 MB per stream
_PING_SAMPLES = 8        # measure 8 times, take median


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


def run_speedtest() -> SpeedResult:
    """
    Measure download/upload speed and latency via Cloudflare endpoints.
    - Uses a Session so TCP+TLS is established once and reused for ping measurements.
    - Parallel streams for download/upload to saturate high-bandwidth connections.
    - Ping = median of 8 RTTs on warmed-up connection (excludes TLS handshake).
    """
    session = requests.Session()
    session.headers.update(_UA)

    try:
        # ── Warm-up: establish TCP + TLS ──────────────────────────────────────
        session.get(f"{_BASE}/__down?bytes=1", timeout=8)

        # ── Ping: median RTT on warm connection ───────────────────────────────
        samples = []
        for _ in range(_PING_SAMPLES):
            t = time.perf_counter()
            session.get(f"{_BASE}/__down?bytes=1", timeout=8)
            samples.append((time.perf_counter() - t) * 1000)
        # Drop the highest outlier, take median of the rest
        samples.sort()
        ping_ms = round(statistics.median(samples[:-1]), 1)

        # ── Download: parallel streams ────────────────────────────────────────
        def _dl():
            r = requests.get(
                f"{_BASE}/__down?bytes={_DL_BYTES}",
                timeout=TIMEOUT, headers=_UA,
            )
            return len(r.content)

        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=_DL_STREAMS) as ex:
            total_bytes = sum(ex.map(_dl, range(_DL_STREAMS)))
        dl_elapsed = time.perf_counter() - t0
        download_mbps = round((total_bytes * 8) / (dl_elapsed * 1_000_000), 1)

        # ── Upload: parallel streams ──────────────────────────────────────────
        payload = b"x" * _UL_BYTES

        def _ul():
            requests.post(
                f"{_BASE}/__up",
                data=payload, timeout=TIMEOUT,
                headers={**_UA, "Content-Type": "application/octet-stream"},
            )
            return _UL_BYTES

        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=_UL_STREAMS) as ex:
            total_ul = sum(ex.map(_ul, range(_UL_STREAMS)))
        ul_elapsed = time.perf_counter() - t0
        upload_mbps = round((total_ul * 8) / (ul_elapsed * 1_000_000), 1)

        return SpeedResult(
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
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
