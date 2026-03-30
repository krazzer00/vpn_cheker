# engine/speedtest.py
import concurrent.futures
import time
from typing import TypedDict

import requests

from engine.ping import ping_host

_BASE = "https://speed.cloudflare.com"
_UA = {"User-Agent": "VPNChecker/1.0"}
TIMEOUT = 45

_DL_STREAMS = 4
_DL_BYTES = 10_000_000   # 10 MB per stream
_UL_STREAMS = 3
_UL_BYTES = 5_000_000    # 5 MB per stream


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


def _download_one() -> int:
    r = requests.get(f"{_BASE}/__down?bytes={_DL_BYTES}", timeout=TIMEOUT, headers=_UA)
    return len(r.content)


def _upload_one() -> int:
    payload = b"x" * _UL_BYTES
    requests.post(
        f"{_BASE}/__up", data=payload, timeout=TIMEOUT,
        headers={**_UA, "Content-Type": "application/octet-stream"},
    )
    return _UL_BYTES


def run_speedtest() -> SpeedResult:
    """
    Measure download/upload speed and latency via Cloudflare.
    Ping uses ICMP (via engine.ping) for accuracy matching speedtest.net.
    Parallel streams for download/upload to saturate high-bandwidth connections.
    """
    session = requests.Session()
    session.headers.update(_UA)

    try:
        # Warm-up: establish TCP + TLS before measurements
        session.get(f"{_BASE}/__down?bytes=1", timeout=8)

        # Ping: ICMP for accurate network RTT (matches speedtest.net methodology)
        ping_result = ping_host("speed.cloudflare.com")
        ping_ms = ping_result.get("ping_ms")

        # Download: parallel streams to saturate high-bandwidth connections
        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=_DL_STREAMS) as ex:
            futures = [ex.submit(_download_one) for _ in range(_DL_STREAMS)]
            total_dl = sum(f.result() for f in concurrent.futures.as_completed(futures))
        dl_elapsed = time.perf_counter() - t0
        download_mbps = round((total_dl * 8) / (dl_elapsed * 1_000_000), 1)

        # Upload: parallel streams
        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=_UL_STREAMS) as ex:
            futures = [ex.submit(_upload_one) for _ in range(_UL_STREAMS)]
            total_ul = sum(f.result() for f in concurrent.futures.as_completed(futures))
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
            download_mbps=None, upload_mbps=None,
            ping_ms=None, error=str(e),
        )
