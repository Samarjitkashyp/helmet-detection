import json
import os
import re
import shutil
import time
import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import config
from core.deps import get_current_user
from db.crud import load_settings
from db.database import get_db
from db.models import Detection, User, Video
from services.video_processor import DELETED_MARK, probe_duration, process_video, raw_path

router = APIRouter(prefix="/videos", tags=["videos"])

ALLOWED_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp"}
MAX_UPLOAD_BYTES = config.MAX_UPLOAD_MB * 1024 * 1024
CHUNK = 1024 * 1024


def _own_video(db: Session, video_id: int, user: User) -> Video:
    video = db.get(Video, video_id)
    if not video or (video.user_id != user.id and user.role != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Video not found")
    return video


def _summary(v: Video, violations: int | None = None) -> dict:
    out = {"id": v.id, "filename": v.filename, "status": v.status, "error": v.error,
           "duration_seconds": v.duration_seconds, "uploaded_at": v.uploaded_at, "processed_at": v.processed_at}
    if violations is not None:
        out["violations"] = violations
    return out


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(background: BackgroundTasks, file: UploadFile = File(...),
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    original = Path(file.filename or "video").name
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported file type. Allowed: {sorted(ALLOWED_EXT)}")

    dest = config.UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                        f"File too large (max {MAX_UPLOAD_BYTES // 1024 // 1024} MB)")
                out.write(chunk)

        duration = probe_duration(str(dest))
        if duration is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not read this video file")
        max_seconds = int(load_settings(db)["max_video_seconds"])
        if duration > max_seconds:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Video is {duration:.0f}s long; the limit is {max_seconds}s")
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    return _register(db, user, background, original, dest, duration)


def _register(db: Session, user: User, background: BackgroundTasks, original: str, dest: Path, duration: float) -> dict:
    """Create the Video row for a file that is saved and checked, and queue its analysis."""
    video = Video(user_id=user.id, filename=original[:255], original_path=str(dest),
                  status="processing", duration_seconds=duration)
    db.add(video)
    db.commit()
    background.add_task(process_video, video.id)
    return _summary(video)


def _check_video_file(db: Session, dest: Path) -> float:
    """Return the duration, or raise an HTTP 400 and delete the file if it is unreadable or too long."""
    duration = probe_duration(str(dest))
    if duration is None:
        dest.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not read this video file")
    max_seconds = int(load_settings(db)["max_video_seconds"])
    if duration > max_seconds:
        dest.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Video is {duration:.0f}s long; the limit is {max_seconds}s")
    return duration


# ---- chunked upload ---------------------------------------------------------------------------
# Phones upload slowly, and Cloudflare cuts any single request that runs longer than ~100 s (error 524).
# So the app sends the video in small pieces: init -> PUT piece, PUT piece, ... -> complete.
CHUNK_BYTES = 2 * 1024 * 1024          # size the app should use
MAX_CHUNK_BYTES = 8 * 1024 * 1024      # hard cap per request
MAX_OPEN_UPLOADS = 3                   # per user
INCOMING_DIR = config.UPLOAD_DIR / "_incoming"
STALE_SECONDS = 24 * 3600


class UploadInit(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)


def _upload_dir(upload_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", upload_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found")
    return INCOMING_DIR / upload_id


def _upload_meta(upload_id: str, user: User) -> tuple[dict, Path]:
    d = _upload_dir(upload_id)
    try:
        meta = json.loads((d / "meta.json").read_text())
    except (OSError, ValueError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found or expired") from None
    if meta["user_id"] != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found or expired")
    return meta, d / "data.part"


def purge_stale_uploads() -> None:
    """Remove half-finished uploads that were abandoned (called on start-up and before new uploads)."""
    if not INCOMING_DIR.is_dir():
        return
    cutoff = time.time() - STALE_SECONDS
    for d in INCOMING_DIR.iterdir():
        try:
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
def init_upload(body: UploadInit, user: User = Depends(get_current_user)):
    ext = Path(body.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported file type. Allowed: {sorted(ALLOWED_EXT)}")
    if body.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"File too large (max {config.MAX_UPLOAD_MB} MB)")
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    purge_stale_uploads()
    open_uploads = 0
    for d in INCOMING_DIR.iterdir():
        try:
            if json.loads((d / "meta.json").read_text())["user_id"] == user.id:
                open_uploads += 1
        except (OSError, ValueError, KeyError):
            continue
    if open_uploads >= MAX_OPEN_UPLOADS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many unfinished uploads. Try again in a few minutes.")
    upload_id = uuid.uuid4().hex
    d = INCOMING_DIR / upload_id
    d.mkdir()
    (d / "data.part").touch()
    (d / "meta.json").write_text(json.dumps({"user_id": user.id, "filename": Path(body.filename).name, "size": body.size}))
    return {"upload_id": upload_id, "chunk_size": CHUNK_BYTES}


@router.put("/uploads/{upload_id}")
async def put_chunk(upload_id: str, request: Request, offset: int = Query(ge=0),
                    user: User = Depends(get_current_user)):
    """Store one piece at `offset`. Re-sending a piece is safe: anything after `offset` is overwritten."""
    meta, part = _upload_meta(upload_id, user)
    have = part.stat().st_size
    if offset > have:
        return JSONResponse({"detail": "Missing data before this piece", "received": have}, status_code=409)
    written = 0
    with open(part, "r+b") as f:
        f.seek(offset)
        f.truncate(offset)
        async for piece in request.stream():
            written += len(piece)
            if written > MAX_CHUNK_BYTES or offset + written > meta["size"]:
                f.truncate(offset)
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Piece is larger than allowed")
            f.write(piece)
    if written == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty piece")
    os.utime(part.parent)  # keeps an active upload from being purged as stale
    return {"received": offset + written}


@router.post("/uploads/{upload_id}/complete", status_code=status.HTTP_202_ACCEPTED)
def complete_upload(upload_id: str, background: BackgroundTasks, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    meta, part = _upload_meta(upload_id, user)
    got = part.stat().st_size
    if got != meta["size"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Upload incomplete ({got} of {meta['size']} bytes)")
    dest = config.UPLOAD_DIR / f"{uuid.uuid4().hex}{Path(meta['filename']).suffix.lower()}"
    shutil.move(str(part), dest)
    shutil.rmtree(part.parent, ignore_errors=True)
    duration = _check_video_file(db, dest)
    return _register(db, user, background, meta["filename"], dest, duration)


@router.get("")
def list_videos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Video).where(Video.user_id == user.id).order_by(Video.id.desc()).limit(100)).all()
    counts = dict(db.execute(
        select(Detection.video_id, func.count(Detection.id))
        .where(Detection.video_id.in_([v.id for v in rows]), Detection.label == "no_helmet",
               Detection.is_false_positive.is_(False))
        .group_by(Detection.video_id)).all()) if rows else {}
    return [_summary(v, counts.get(v.id, 0) if v.status == "done" else None) for v in rows]


@router.get("/{video_id}/status")
def video_status(video_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _summary(_own_video(db, video_id, user))


@router.get("/{video_id}/results")
def video_results(video_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _own_video(db, video_id, user)
    dets = db.scalars(select(Detection).where(Detection.video_id == video_id, Detection.is_false_positive.is_(False))
                      .order_by(Detection.timestamp_seconds)).all()
    items = [{"id": d.id, "label": d.label, "confidence": round(d.confidence, 3),
              "timestamp_seconds": round(d.timestamp_seconds, 2),
              "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2],
              "image_url": f"/videos/{video_id}/detections/{d.id}/image" if d.screenshot_path else None}
             for d in dets]
    violations = sum(1 for d in dets if d.label == "no_helmet")
    return {**_summary(video, violations), "people_checked": len(dets), "detections": items,
            "warnings": _quality_warnings(dets)}


DARK_BRIGHTNESS = 70      # mean grey level (0-255) below which a video is probably too dark
LOW_CONFIDENCE = 0.6


def _quality_warnings(dets: list[Detection]) -> list[str]:
    """Plain-language hints when the video quality makes the verdicts less trustworthy."""
    warnings = []
    levels = []
    for d in dets[:12]:
        if not d.screenshot_path:
            continue
        img = cv2.imread(str(config.RESULTS_DIR / raw_path(d.screenshot_path)), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            levels.append(float(img.mean()))
    if levels and sum(levels) / len(levels) < DARK_BRIGHTNESS:
        warnings.append("The video looks dark, so results may be less accurate. Record in better light.")
    if dets and sum(1 for d in dets if d.confidence < LOW_CONFIDENCE) > len(dets) / 2:
        warnings.append("The model was unsure about many people (they may be far away or blurry). "
                        "Move closer and keep the phone steady.")
    return warnings


@router.get("/{video_id}/detections/{detection_id}/image")
def detection_image(video_id: int, detection_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    _own_video(db, video_id, user)
    det = db.get(Detection, detection_id)
    if not det or det.video_id != video_id or not det.screenshot_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    root = config.RESULTS_DIR.resolve()
    path = (root / det.screenshot_path).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    return FileResponse(path, media_type="image/jpeg")


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _own_video(db, video_id, user)
    if video.status == "processing":
        raise HTTPException(status.HTTP_409_CONFLICT, "Video is still processing")
    if video.original_path != DELETED_MARK:
        Path(video.original_path).unlink(missing_ok=True)
    shutil.rmtree(config.RESULTS_DIR / str(video_id), ignore_errors=True)
    db.delete(video)
    db.commit()
