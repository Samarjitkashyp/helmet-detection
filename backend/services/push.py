"""Push notifications to the phone app through Firebase Cloud Messaging (HTTP v1).

Needs, on the server: FCM_PROJECT_ID and FCM_SERVICE_ACCOUNT_FILE in .env (see deploy/README_DEPLOY.md) and the
google-auth package. Without them every function here quietly does nothing, so CCTV alerts keep working through Telegram.
"""
import json
import threading
import urllib.error
import urllib.request

import config
from db.database import SessionLocal
from db.models import PushDevice, User

SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_creds = None
_lock = threading.Lock()


def configured() -> bool:
    return bool(config.FCM_PROJECT_ID and config.FCM_SERVICE_ACCOUNT_FILE)


def _access_token() -> str | None:
    """Short-lived OAuth token for the service account (cached and refreshed by google-auth)."""
    global _creds
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
    except ImportError:
        print("push: google-auth is not installed", flush=True)
        return None
    with _lock:
        if _creds is None:
            _creds = service_account.Credentials.from_service_account_file(config.FCM_SERVICE_ACCOUNT_FILE, scopes=[SCOPE])
        if not _creds.valid:
            _creds.refresh(Request())
        return _creds.token


def _send(token: str, bearer: str, title: str, body: str, data: dict) -> int:
    msg = {"message": {"token": token, "notification": {"title": title, "body": body},
                       "data": {k: str(v) for k, v in data.items()},
                       "android": {"priority": "HIGH", "notification": {"channel_id": "cctv_alerts"}}}}
    req = urllib.request.Request(f"https://fcm.googleapis.com/v1/projects/{config.FCM_PROJECT_ID}/messages:send",
                                 data=json.dumps(msg).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def _notify(title: str, body: str, data: dict) -> None:
    try:
        bearer = _access_token()
        if not bearer:
            return
        with SessionLocal() as db:
            admin_ids = [u.id for u in db.query(User).filter(User.role == "admin", User.is_active.is_(True))]
            devices = db.query(PushDevice).filter(PushDevice.user_id.in_(admin_ids)).all()
            for d in devices:
                status = _send(d.token, bearer, title, body, data)
                if status in (404, 400):     # the phone uninstalled the app or the token expired
                    db.delete(d)
            db.commit()
    except Exception as e:     # a push problem must never break event handling
        print("push failed:", type(e).__name__, flush=True)


def notify_event(event_id: int, camera_name: str, people: int) -> None:
    """Fire and forget: tell every admin phone about a new CCTV event."""
    if not configured():
        return
    title = f"{people} {'person' if people == 1 else 'people'} without helmet"
    threading.Thread(target=_notify, args=(title, camera_name, {"event_id": event_id, "type": "cctv_event"}), daemon=True).start()
