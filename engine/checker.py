# engine/checker.py
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from engine.ping import ping_host
from engine.http_check import http_check, ai_region_check
from engine.speedtest import run_speedtest
from engine.verdict import compute_verdict


def _check_one_service(service: dict) -> dict:
    """Run all checks for a single service. Called in a thread."""
    host = urlparse(service["url"]).hostname
    ping_result = ping_host(host)

    if service["check_type"] == "ai_region":
        http_result = http_check(service["url"])
        ai_result = ai_region_check(service["check_url"])
        accessible = http_result["accessible"] and ai_result["region_accessible"]
        region_accessible = ai_result["region_accessible"]
    else:
        http_result = http_check(service["check_url"])
        accessible = http_result["accessible"]
        region_accessible = None

    return {
        "type": "service",
        "id": service["id"],
        "name": service["name"],
        "icon": service["icon"],
        "category": service["category"],
        "accessible": accessible,
        "region_accessible": region_accessible,
        "ping_ms": ping_result["ping_ms"],
        "loss_pct": ping_result["loss_pct"],
        "ping_method": ping_result["method"],
        "status_code": http_result.get("status_code"),
        "response_ms": http_result.get("response_ms"),
    }


def run_checks(services: list[dict], result_queue: queue.Queue) -> None:
    """
    Run all service checks + speedtest in parallel.
    Puts {type: "service", ...} and {type: "verdict", ...} into result_queue.
    Also puts {type: "speed", ...} when speedtest completes.
    """
    service_results = []
    lock = threading.Lock()

    if not services:
        result_queue.put({"type": "verdict", **compute_verdict([])})
        return

    def speedtest_worker():
        speed = run_speedtest()
        result_queue.put({"type": "speed", **speed})

    speed_thread = threading.Thread(target=speedtest_worker, daemon=True)
    speed_thread.start()

    with ThreadPoolExecutor(max_workers=min(len(services), 8)) as pool:
        futures = {pool.submit(_check_one_service, svc): svc for svc in services}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                svc = futures[future]
                result = {
                    "type": "service",
                    "id": svc["id"],
                    "name": svc["name"],
                    "icon": svc["icon"],
                    "category": svc["category"],
                    "accessible": False,
                    "region_accessible": None,
                    "ping_ms": None,
                    "loss_pct": 100.0,
                    "ping_method": "n/a",
                    "status_code": None,
                    "response_ms": None,
                    "error": str(e),
                }
            result_queue.put(result)
            with lock:
                service_results.append(result)

    verdict = compute_verdict(service_results)
    result_queue.put({"type": "verdict", **verdict})


def run_single_check(service: dict) -> dict:
    """Single service check for the custom tab. Exceptions propagate to caller."""
    return _check_one_service(service)
