"""Worker heartbeat bookkeeping and the offline watchdog (Telegram when the CCTV worker or its camera goes quiet)."""
import threading
import time
from datetime import datetime

import config
from db.database import SessionLocal
from db.models import Setting
from services import push, telegram

LAST_HEARTBEAT = "cctv_last_heartbeat"     # ISO time (UTC) of the newest heartbeat
OFFLINE_NOTIFIED = "cctv_offline_notified"  # "1" while an "offline" alert is out
STREAM_BAD_SINCE = "cctv_stream_bad_since"  # ISO time the camera stream was first reported down ("" = fine)
STREAM_NOTIFIED = "cctv_stream_notified"


def _get(db, key: str, default: str = "") -> str:
    row = db.get(Setting, key)
    return row.value if row else default


def _set(db, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))


def _age_text(seconds: float) -> str:
    minutes = int(seconds // 60)
    return f"{minutes} min" if minutes < 120 else f"{minutes // 60} h"


def record_heartbeat(stream_ok: bool, camera_name: str) -> None:
    """Called for every heartbeat from the worker. Sends 'back online' messages when things recover."""
    now = datetime.utcnow()
    messages = []
    with SessionLocal() as db:
        if _get(db, OFFLINE_NOTIFIED) == "1":
            messages.append("CCTV worker is back online.")
            _set(db, OFFLINE_NOTIFIED, "0")
        if stream_ok:
            if _get(db, STREAM_NOTIFIED) == "1":
                messages.append(f"Camera '{camera_name}' stream is back.")
                _set(db, STREAM_NOTIFIED, "0")
            _set(db, STREAM_BAD_SINCE, "")
        elif not _get(db, STREAM_BAD_SINCE):
            _set(db, STREAM_BAD_SINCE, now.isoformat())
        _set(db, LAST_HEARTBEAT, now.isoformat())
        db.commit()
    for m in messages:
        telegram.send_message(m)
        push.notify_text("CCTV", m)


def check_once() -> None:
    now = datetime.utcnow()
    limit = config.CCTV_OFFLINE_MINUTES * 60
    messages = []
    with SessionLocal() as db:
        last = _get(db, LAST_HEARTBEAT)
        if not last:
            return   # no worker has ever reported: nothing to watch
        age = (now - datetime.fromisoformat(last)).total_seconds()
        if age > limit and _get(db, OFFLINE_NOTIFIED) != "1":
            messages.append(f"CCTV worker is OFFLINE (last seen {_age_text(age)} ago). "
                            "No helmet checks are running. Is the PC on?")
            _set(db, OFFLINE_NOTIFIED, "1")
        bad = _get(db, STREAM_BAD_SINCE)
        if bad and age <= limit and (now - datetime.fromisoformat(bad)).total_seconds() > limit \
                and _get(db, STREAM_NOTIFIED) != "1":
            messages.append("CCTV camera stream is not reachable. The worker is running but sees no video.")
            _set(db, STREAM_NOTIFIED, "1")
        db.commit()
    for m in messages:
        telegram.send_message(m)
        push.notify_text("CCTV", m)


def _loop():
    while True:
        time.sleep(60)
        try:
            check_once()
        except Exception as e:   # the watchdog must never die
            print("cctv watchdog error:", type(e).__name__, flush=True)


def start_watchdog() -> None:
    if config.CCTV_WORKER_KEY:
        threading.Thread(target=_loop, daemon=True, name="cctv-watchdog").start()
