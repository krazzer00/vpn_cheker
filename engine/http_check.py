# engine/http_check.py
import time
from typing import TypedDict

import requests
from engine.proxy import requests_proxies

HTTP_TIMEOUT = 5
AI_TIMEOUT = 8  # AI endpoints are slower to respond with auth errors

# Status codes meaning the endpoint is reachable (just no auth)
_REACHABLE_STATUSES = {200, 201, 400, 401, 405, 422}


class HttpResult(TypedDict):
    accessible: bool
    status_code: int | None
    response_ms: float | None
    error: str | None


class AiRegionResult(TypedDict):
    region_accessible: bool
    status_code: int | None
    error: str | None


def http_check(url: str) -> HttpResult:
    """
    HEAD request to check HTTP availability.
    Returns: {accessible, status_code, response_ms, error}
    """
    try:
        start = time.perf_counter()
        r = requests.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True,
                          headers={"User-Agent": "VPNChecker/1.0"},
                          proxies=requests_proxies())
        elapsed = (time.perf_counter() - start) * 1000
        return HttpResult(
            accessible=r.status_code < 500,
            status_code=r.status_code,
            response_ms=round(elapsed, 1),
            error=None,
        )
    except Exception as e:
        return HttpResult(
            accessible=False,
            status_code=None,
            response_ms=None,
            error=str(e),
        )


def ai_region_check(check_url: str) -> AiRegionResult:
    """
    Check if an AI service is accessible in this region.
    401 = reachable (just no key). 403/timeout = geo-blocked.
    Returns: {region_accessible, status_code, error}
    """
    try:
        r = requests.get(check_url, timeout=AI_TIMEOUT,
                         headers={"User-Agent": "VPNChecker/1.0"},
                         proxies=requests_proxies())
        return AiRegionResult(
            region_accessible=r.status_code in _REACHABLE_STATUSES,
            status_code=r.status_code,
            error=None,
        )
    except Exception as e:
        return AiRegionResult(
            region_accessible=False,
            status_code=None,
            error=str(e),
        )
