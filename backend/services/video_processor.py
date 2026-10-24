"""Run YOLO + tracking over an uploaded video and store one detection per tracked person."""
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2

import config
from db.crud import load_settings
from db.database import SessionLocal
from db.models import Detection, Video

SCREENSHOT_WIDTH = 640
DELETED_MARK = "(deleted)"  # original_path value once the uploaded file was removed after analysis

_model = None
_model_lock = threading.Lock()
_job_lock = threading.Lock()  # CPU box: process one video at a time


def raw_path(screenshot_rel: str) -> str:
    """Un-annotated full-size frame saved next to each screenshot (used for retraining)."""
    return screenshot_rel[: -len(".jpg")] + "_raw.jpg"


def get_model():
    global _model
    with _model_lock:
        if _model is None:
            from ultralytics import YOLO
            _model = YOLO(str(config.MODEL_PATH))
    return _model


def probe_duration(path: str) -> float | None:
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return None
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        return frames / fps if fps > 0 and frames > 0 else None
    finally:
        cap.release()


def _shrink(img):
    h, w = img.shape[:2]
    if w <= SCREENSHOT_WIDTH:
        return img
    return cv2.resize(img, (SCREENSHOT_WIDTH, int(h * SCREENSHOT_WIDTH / w)))


def _jpeg(img, quality=85) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Could not encode frame")
    return buf.tobytes()


def process_video(video_id: int) -> None:
    with _job_lock:
        _process(video_id)


def _process(video_id: int) -> None:
    with SessionLocal() as db:
        video = db.get(Video, video_id)
        if not video:
            return
        try:
            cfg = load_settings(db)
            result = _run_model(
                video.original_path,
                conf=float(cfg["confidence_threshold"]),
                skip=max(1, int(cfg["frame_skip"])),
                min_box_px=int(cfg["min_box_px"]),
                imgsz=int(cfg["infer_imgsz"]),
            )
            min_hits = max(1, int(cfg["min_track_hits"]))
            out_dir = config.RESULTS_DIR / str(video_id)
            out_dir.mkdir(parents=True, exist_ok=True)

            for track_id, t in result["tracks"].items():
                if t["hits"] < min_hits:
                    continue
                # one verdict per person: the label with more total confidence wins
                label = max(t["score"], key=t["score"].get)
                best = t["best"][label]
                rel = f"{video_id}/track_{track_id}.jpg"
                (config.RESULTS_DIR / rel).write_bytes(best["shot"])
                (config.RESULTS_DIR / raw_path(rel)).write_bytes(best["raw"])
                x1, y1, x2, y2 = best["box"]
                db.add(Detection(video_id=video_id, frame_number=best["frame"],
                                 timestamp_seconds=best["frame"] / result["fps"], label=label,
                                 confidence=best["conf"], bbox_x1=x1, bbox_y1=y1, bbox_x2=x2, bbox_y2=y2,
                                 screenshot_path=rel))
            video.duration_seconds = result["duration"]
            video.status = "done"
            video.error = None
            video.processed_at = datetime.utcnow()
            if not config.KEEP_ORIGINAL_VIDEOS:  # screenshots are the evidence we keep; the big upload can go
                Path(video.original_path).unlink(missing_ok=True)
                video.original_path = DELETED_MARK
            db.commit()
        except Exception as e:  # noqa: BLE001 - any failure must end in a visible 'failed' status
            db.rollback()
            video = db.get(Video, video_id)
            video.status = "failed"
            video.error = f"{type(e).__name__}: {e}"[:500]
            video.processed_at = datetime.utcnow()
            db.commit()


def _run_model(path: str, conf: float, skip: int, min_box_px: int, imgsz: int) -> dict:
    model = get_model()
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video file")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    names = model.names
    tracks = defaultdict(lambda: {"hits": 0, "score": defaultdict(float), "best": {}})
    model.predictor = None  # fresh tracker state for each video

    idx = -1
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            if idx % skip:
                continue
            res = model.track(frame, persist=True, conf=conf, imgsz=imgsz,
                              tracker="bytetrack.yaml", verbose=False)[0]
            if res.boxes is None or res.boxes.id is None:
                continue
            encoded = None  # raw + annotated JPEGs, built once per frame and only if needed
            for box, tid, cls, c in zip(res.boxes.xyxy.tolist(), res.boxes.id.int().tolist(),
                                        res.boxes.cls.int().tolist(), res.boxes.conf.tolist()):
                if box[3] - box[1] < min_box_px:
                    continue  # too small/far away to judge reliably
                label = names[cls]
                t = tracks[tid]
                t["hits"] += 1
                t["score"][label] += c
                prev = t["best"].get(label)
                if prev is None or c > prev["conf"]:
                    if encoded is None:
                        encoded = (_jpeg(_shrink(res.plot())), _jpeg(frame, 92))
                    t["best"][label] = {"conf": c, "frame": idx, "box": box,
                                        "shot": encoded[0], "raw": encoded[1]}
    finally:
        cap.release()
        model.predictor = None
    duration = (total / fps) if total else (idx + 1) / fps
    return {"tracks": tracks, "fps": fps, "duration": duration}


def fail_stale_jobs() -> None:
    """On server start, videos left in 'processing' by a crash/restart can never finish."""
    with SessionLocal() as db:
        for v in db.query(Video).filter(Video.status == "processing").all():
            v.status, v.error = "failed", "Server restarted while processing; please upload again."
        db.commit()
