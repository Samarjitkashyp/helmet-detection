import shutil
import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
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

    video = Video(user_id=user.id, filename=original[:255], original_path=str(dest),
                  status="processing", duration_seconds=duration)
    db.add(video)
    db.commit()
    background.add_task(process_video, video.id)
    return _summary(video)


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
