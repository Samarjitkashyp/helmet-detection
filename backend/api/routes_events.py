"""CCTV events for the phone app (admins only, normal login token). The worker-facing endpoints live in routes_cctv.py."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from core.deps import require_admin
from db.database import get_db
from db.models import Camera, CctvEvent, PushDevice, Setting, User

router = APIRouter(prefix="/cctv", tags=["cctv"])
CCTV_DIR = config.STORAGE_DIR / "cctv"


def _event_json(e: CctvEvent) -> dict:
    return {"id": e.id, "camera_id": e.camera_id, "camera_name": e.camera_name, "confidence": round(e.confidence, 3),
            "created_at": e.created_at.isoformat(timespec="seconds"), "has_photo": bool(e.photo),
            "photo_url": f"/cctv/events/{e.id}/photo" if e.photo else None, "is_false_positive": e.is_false_positive}


@router.get("/events")
def list_events(since_id: int = Query(0, ge=0), before_id: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100),
                include_false_positives: bool = False, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Newest first. `since_id` returns only events newer than that id (for polling); `before_id` pages back in time."""
    q = select(CctvEvent)
    if since_id:
        q = q.where(CctvEvent.id > since_id)
    if before_id:
        q = q.where(CctvEvent.id < before_id)
    if not include_false_positives:
        q = q.where(CctvEvent.is_false_positive.is_(False))
    return [_event_json(e) for e in db.scalars(q.order_by(CctvEvent.id.desc()).limit(limit))]


@router.get("/events/{event_id}/photo")
def event_photo(event_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    ev = db.get(CctvEvent, event_id)
    if not ev or not ev.photo:
        raise HTTPException(404)
    root = CCTV_DIR.resolve()
    target = (root / ev.photo).resolve()
    if target.parent != root or not target.is_file():
        raise HTTPException(404)
    return FileResponse(target, media_type="image/jpeg")


@router.post("/events/{event_id}/false-positive")
def toggle_false_positive(event_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    ev = db.get(CctvEvent, event_id)
    if not ev:
        raise HTTPException(404)
    ev.is_false_positive = not ev.is_false_positive
    db.commit()
    return _event_json(ev)


@router.get("/status")
def status(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Is the CCTV worker alive? (seconds since its last heartbeat, None = never seen)"""
    row = db.get(Setting, "cctv_last_heartbeat")
    age = (datetime.utcnow() - datetime.fromisoformat(row.value)).total_seconds() if row and row.value else None
    cams = db.scalars(select(Camera).order_by(Camera.id)).all()
    return {"worker_seconds_since_heartbeat": None if age is None else int(age),
            "worker_online": age is not None and age < config.CCTV_OFFLINE_MINUTES * 60,
            "cameras": [{"id": c.id, "name": c.name, "is_active": c.is_active} for c in cams]}


class DeviceIn(BaseModel):
    token: str = Field(min_length=20, max_length=300)


@router.post("/devices", status_code=204)
def register_device(body: DeviceIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """The app sends its FCM token after sign-in; the same token always belongs to the latest signed-in user."""
    row = db.scalar(select(PushDevice).where(PushDevice.token == body.token))
    if row:
        row.user_id = admin.id
    else:
        db.add(PushDevice(user_id=admin.id, token=body.token))
    db.commit()


@router.delete("/devices", status_code=204)
def unregister_device(body: DeviceIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.scalar(select(PushDevice).where(PushDevice.token == body.token))
    if row:
        db.delete(row)
        db.commit()
