# engine/speedtest.py
import time
from typing import TypedDict

import requests

DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=25000000"  # 25 MB
UPLOAD_URL = "https://speed.cloudflare.com/__up"
PING_URL = "https://speed.cloudflare.com/__ping"
TIMEOUT = 30


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


def run_speedtest() -> SpeedResult:
    """
    Measure download/upload speed and ping using Cloudflare speed test endpoints.
    Pure requests-based — no external CLI tools, works in frozen PyInstaller exe.
    """
    try:
        # Ping measurement
        start = time.perf_counter()
        requests.get(PING_URL, timeout=5, headers={"User-Agent": "VPNChecker/1.0"})
        ping_ms = round((time.perf_counter() - start) * 1000, 1)

        # Download measurement
        start = time.perf_counter()
        r = requests.get(DOWNLOAD_URL, stream=True, timeout=TIMEOUT,
                         headers={"User-Agent": "VPNChecker/1.0"})
        downloaded = sum(len(chunk) for chunk in r.iter_content(chunk_size=65536))
        dl_elapsed = time.perf_counter() - start
        download_mbps = round((downloaded * 8) / (dl_elapsed * 1_000_000), 1)

        # Upload measurement (5 MB payload)
        payload = b"0" * 5_000_000
        start = time.perf_counter()
        requests.post(UPLOAD_URL, data=payload, timeout=TIMEOUT,
                      headers={"User-Agent": "VPNChecker/1.0",
                               "Content-Type": "application/octet-stream"})
        ul_elapsed = time.perf_counter() - start
        upload_mbps = round((len(payload) * 8) / (ul_elapsed * 1_000_000), 1)

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
