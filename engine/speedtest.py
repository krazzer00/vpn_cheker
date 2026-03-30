# engine/speedtest.py
"""
Speed measurement via speedtest.net (Ookla) infrastructure.
Uses speedtest-cli which selects the closest Ookla server automatically.
"""
from typing import TypedDict

import speedtest as _st_lib


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


def run_speedtest() -> SpeedResult:
    """
    Measure download/upload speed and latency using Ookla speedtest.net servers.
    Automatically selects the best (lowest latency) server.
    """
    try:
        st = _st_lib.Speedtest(secure=False, timeout=20)

        # Fetch server list and select closest by latency
        st.get_best_server()

        # Download (uses multiple threads internally)
        download_bps = st.download(threads=4)

        # Upload
        upload_bps = st.upload(threads=4, pre_allocate=False)

        results = st.results.dict()
        ping_ms = round(results.get("ping", 0), 1)
        download_mbps = round(download_bps / 1_000_000, 1)
        upload_mbps = round(upload_bps / 1_000_000, 1)

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
