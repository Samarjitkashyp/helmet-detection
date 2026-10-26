"""Endpoints used by the CCTV worker (it runs on a PC near the camera, not on this server).

Every call carries the shared key in the X-Worker-Key header (CCTV_WORKER_KEY in .env). Without a key
configured the endpoints answer 404, so a server that does not use CCTV exposes nothing.
"""
import hmac
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

import config
from core.ratelimit import client_ip
from db.database import get_db
from db.models import Camera, CctvEvent
from services import cctv_status, push, telegram

router = APIRouter(prefix="/api/cctv", tags=["cctv"], include_in_schema=False)

CCTV_DIR = config.STORAGE_DIR / "cctv"
MAX_PHOTO_BYTES = 6 * 1024 * 1024
_bad_keys: dict[str, list[float]] = {}


def worker_auth(request: Request):
    if not config.CCTV_WORKER_KEY:
        raise HTTPException(404)
    ip = client_ip(request)
    recent = [t for t in _bad_keys.get(ip, []) if time.time() - t < 600]
    if len(recent) >= 10:
        raise HTTPException(429, "Too many wrong keys")
    sent = request.headers.get("x-worker-key", "")
    if not hmac.compare_digest(sent.encode(), config.CCTV_WORKER_KEY.encode()):
        recent.append(time.time())
        _bad_keys[ip] = recent
        raise HTTPException(401, "Bad worker key")
    _bad_keys.pop(ip, None)


@router.get("/cameras/{cam_id}", dependencies=[Depends(worker_auth)])
def camera_config(cam_id: int, db: Session = Depends(get_db)):
    cam = db.get(Camera, cam_id)
    if not cam:
        raise HTTPException(404, "No such camera")
    return {"id": cam.id, "name": cam.name, "rtsp_url": cam.rtsp_url, "is_active": cam.is_active}


class Heartbeat(BaseModel):
    camera_name: str = ""
    stream_ok: bool = True


@router.post("/heartbeat", dependencies=[Depends(worker_auth)])
def heartbeat(body: Heartbeat):
    cctv_status.record_heartbeat(body.stream_ok, body.camera_name[:100])
    return {"ok": True}


@router.post("/event", dependencies=[Depends(worker_auth)])
async def new_event(camera_id: int | None = Form(None), camera_name: str = Form(...), track_id: int = Form(0),
                    confidence: float = Form(...), people: int = Form(1), photo: UploadFile = File(...),
                    db: Session = Depends(get_db)):
    data = await photo.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES or data[:3] != b"\xff\xd8\xff":
        raise HTTPException(400, "Photo must be a JPEG under 6 MB")
    camera_name = camera_name.strip()[:100] or "Camera"
    if camera_id is not None and not db.get(Camera, camera_id):
        camera_id = None
    CCTV_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}.jpg"   # never trust a client-supplied file name
    (CCTV_DIR / name).write_bytes(data)
    now = datetime.now()
    caption = (f"{people} {'person' if people == 1 else 'people'} without helmet\nCamera: {camera_name}\n"
               f"Time: {now:%d %b %Y %H:%M:%S}\nConfidence: {confidence:.0%}")
    sent = telegram.send_photo(data, caption)
    ev = CctvEvent(camera_id=camera_id, camera_name=camera_name, track_id=track_id, confidence=confidence,
                   photo=name, telegram_sent=sent)
    db.add(ev)
    db.commit()
    push.notify_event(ev.id, camera_name, people)
    return {"ok": True, "id": ev.id, "telegram_sent": sent}
