# engine/speedtest.py
from typing import TypedDict

import speedtest as st


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps: float | None
    ping_ms: float | None
    error: str | None


def run_speedtest() -> SpeedResult:
    """
    Run a speedtest. Returns download/upload in Mbps and ping in ms.
    Returns: {download_mbps, upload_mbps, ping_ms, error}
    """
    try:
        s = st.Speedtest(secure=True)
        s.get_best_server()
        s.download()
        s.upload()
        results = s.results.dict()
        return SpeedResult(
            download_mbps=round(results["download"] / 1_000_000, 1),
            upload_mbps=round(results["upload"] / 1_000_000, 1),
            ping_ms=round(results["ping"], 1),
            error=None,
        )
    except Exception as e:
        return SpeedResult(
            download_mbps=None,
            upload_mbps=None,
            ping_ms=None,
            error=str(e),
        )
