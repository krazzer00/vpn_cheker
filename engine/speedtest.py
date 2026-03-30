# engine/speedtest.py
"""
Speed measurement using the official Ookla speedtest CLI (speedtest.exe).
Streams JSONL output in real-time so the UI can show live progress.
"""
import json
import os
import queue
import subprocess
import sys
from typing import TypedDict


class SpeedResult(TypedDict):
    download_mbps: float | None
    upload_mbps:   float | None
    ping_ms:       float | None
    loss_pct:      float | None
    error:         str | None


def _find_exe() -> str:
    """Locate speedtest.exe — works from source and inside a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS          # PyInstaller temp dir
    else:
        # project root is one level above engine/
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "speedtest.exe")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"speedtest.exe not found at: {path}")
    return path


def run_speedtest_streaming(result_queue: queue.Queue) -> None:
    """
    Run the official Ookla speedtest CLI and push incremental
    {"type": "speed", ...} messages to result_queue as the test progresses.
    Fields not yet measured are omitted so the UI keeps its previous value.
    A final message with all fields is always emitted on completion.
    """
    try:
        exe = _find_exe()
    except FileNotFoundError as e:
        result_queue.put({"type": "speed",
                          "download_mbps": None, "upload_mbps": None,
                          "ping_ms": None, "loss_pct": None,
                          "error": str(e)})
        return

    from engine.proxy import is_enabled, socks5_host, socks5_port
    cmd = [exe,
           "--format=jsonl",
           "--accept-license",
           "--accept-gdpr",
           "--progress=yes"]
    if is_enabled():
        cmd.append(f"--proxy=socks5://{socks5_host()}:{socks5_port()}")

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW   # no console pop-up

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            creationflags=creation_flags,
        )
    except Exception as e:
        result_queue.put({"type": "speed",
                          "download_mbps": None, "upload_mbps": None,
                          "ping_ms": None, "loss_pct": None,
                          "error": str(e)})
        return

    # Accumulate known values so every emitted message is a full snapshot
    state: dict = {
        "download_mbps": None,
        "upload_mbps":   None,
        "ping_ms":       None,
        "loss_pct":      None,
        "error":         None,
    }

    def _emit() -> None:
        result_queue.put({"type": "speed", **state})

    for raw in proc.stdout:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        t = data.get("type")

        if t == "ping":
            ping = data.get("ping", {})
            state["ping_ms"] = round(ping.get("latency", 0), 1)
            _emit()

        elif t == "download":
            bw = data.get("download", {}).get("bandwidth", 0)
            state["download_mbps"] = round(bw * 8 / 1_000_000, 1)
            _emit()

        elif t == "upload":
            bw = data.get("upload", {}).get("bandwidth", 0)
            state["upload_mbps"] = round(bw * 8 / 1_000_000, 1)
            _emit()

        elif t == "result":
            ping = data.get("ping", {})
            dl   = data.get("download", {})
            ul   = data.get("upload", {})
            state["ping_ms"]       = round(ping.get("latency", 0), 1)
            state["download_mbps"] = round(dl.get("bandwidth", 0) * 8 / 1_000_000, 1)
            state["upload_mbps"]   = round(ul.get("bandwidth", 0) * 8 / 1_000_000, 1)
            state["loss_pct"]      = data.get("packetLoss")
            _emit()

    proc.wait()

    # If we never received any data, emit an error
    if state["ping_ms"] is None and state["download_mbps"] is None:
        state["error"] = "speedtest.exe returned no results (rc={})".format(
            proc.returncode
        )
        _emit()
