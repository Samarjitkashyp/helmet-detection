"""Custom admin dashboard (Jinja2 + HTMX + Chart.js) served under /panel."""
import csv
import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

import config
from core.ratelimit import client_ip, login_limiter
from core.security import verify_password
from db.crud import load_settings
from db.database import get_db
from db.models import Detection, Setting, User, Video
from services.video_processor import raw_path

SESSION_KEY = "admin_id"
PAGE_SIZE = 25

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
router = APIRouter(prefix="/panel", include_in_schema=False)


class NotLoggedIn(Exception):
    pass


def current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get(SESSION_KEY)
    user = db.get(User, user_id) if user_id else None
    if not user or user.role != "admin" or not user.is_active:
        raise NotLoggedIn()
    return user


def render(request: Request, name: str, admin: User | None = None, **ctx):
    return templates.TemplateResponse(request, name, {"admin": admin, **ctx})


# ---------- auth ----------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html", error=None)


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    key = f"panel|{client_ip(request)}|{email.strip().lower()}"
    if login_limiter.blocked(key):
        return render(request, "login.html", error="Too many failed attempts. Try again in a few minutes.")
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    ok = user and user.role == "admin" and user.is_active and verify_password(password, user.password_hash)
    if not ok:
        login_limiter.fail(key)
        return render(request, "login.html", error="Wrong email or password, or not an admin.")
    login_limiter.reset(key)
    request.session[SESSION_KEY] = user.id
    return RedirectResponse("/panel/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/panel/login", status_code=303)


# ---------- dashboard ----------
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    total_users = db.scalar(select(func.count(User.id)))
    total_videos = db.scalar(select(func.count(Video.id)))
    failed_videos = db.scalar(select(func.count(Video.id)).where(Video.status == "failed"))
    base = select(func.count(Detection.id)).where(Detection.is_false_positive.is_(False))
    violations = db.scalar(base.where(Detection.label == "no_helmet"))
    compliant = db.scalar(base.where(Detection.label == "helmet"))
    total_det = (violations or 0) + (compliant or 0)
    pct = round(100 * (violations or 0) / total_det, 1) if total_det else 0

    since = datetime.utcnow() - timedelta(days=13)
    rows = db.execute(
        select(func.date(Detection.created_at), func.count(Detection.id))
        .where(Detection.label == "no_helmet", Detection.is_false_positive.is_(False), Detection.created_at >= since)
        .group_by(func.date(Detection.created_at))
    ).all()
    per_day = {str(d): c for d, c in rows}
    labels = [(since + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)]
    series = [per_day.get(day, 0) for day in labels]

    recent = db.scalars(select(Video).options(joinedload(Video.user)).order_by(Video.id.desc()).limit(8)).all()
    return render(
        request, "dashboard.html", admin, active="dashboard",
        stats={"users": total_users, "videos": total_videos, "failed": failed_videos,
               "violations": violations or 0, "pct": pct},
        chart={"labels": labels, "data": series}, recent=recent,
    )


# ---------- violations ----------
def _violation_query(label: str, fp: str, user_id: int | None):
    q = select(Detection).options(joinedload(Detection.video).joinedload(Video.user))
    if label in ("helmet", "no_helmet"):
        q = q.where(Detection.label == label)
    if fp == "yes":
        q = q.where(Detection.is_false_positive.is_(True))
    elif fp == "no":
        q = q.where(Detection.is_false_positive.is_(False))
    if user_id:
        q = q.join(Video, Detection.video_id == Video.id).where(Video.user_id == user_id)
    return q


@router.get("/violations", response_class=HTMLResponse)
def violations(request: Request, label: str = "no_helmet", fp: str = "no", user_id: int | None = None,
               page: int = 1, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    q = _violation_query(label, fp, user_id)
    total = db.scalar(select(func.count()).select_from(q.order_by(None).subquery()))
    items = db.scalars(q.order_by(Detection.id.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)).unique().all()
    users = db.scalars(select(User).order_by(User.name)).all()
    return render(request, "violations.html", admin, active="violations", items=items, total=total, page=page,
                  pages=max(1, -(-total // PAGE_SIZE)), label=label, fp=fp, user_id=user_id, users=users)


@router.post("/violations/{det_id}/toggle-fp", response_class=HTMLResponse)
def toggle_fp(det_id: int, request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    det = db.get(Detection, det_id, options=[joinedload(Detection.video).joinedload(Video.user)])
    if not det:
        raise HTTPException(404)
    det.is_false_positive = not det.is_false_positive
    db.commit()
    return render(request, "_violation_row.html", admin, d=det)


# ---------- users ----------
@router.get("/users", response_class=HTMLResponse)
def users(request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Video.user_id, func.count(Video.id)).group_by(Video.user_id)).all())
    items = db.scalars(select(User).order_by(User.id)).all()
    return render(request, "users.html", admin, active="users", items=items, counts=counts)


def _user_row(request, admin, db, user_id):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    count = db.scalar(select(func.count(Video.id)).where(Video.user_id == user_id))
    return render(request, "_user_row.html", admin, u=user, counts={user.id: count})


@router.post("/users/{user_id}/toggle-active", response_class=HTMLResponse)
def toggle_active(user_id: int, request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(400, "You cannot block yourself")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    user.is_active = not user.is_active
    db.commit()
    return _user_row(request, admin, db, user_id)


@router.post("/users/{user_id}/toggle-role", response_class=HTMLResponse)
def toggle_role(user_id: int, request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(400, "You cannot change your own role")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    user.role = "user" if user.role == "admin" else "admin"
    db.commit()
    return _user_row(request, admin, db, user_id)


# ---------- videos ----------
@router.get("/videos", response_class=HTMLResponse)
def videos(request: Request, status: str = "", page: int = 1, admin: User = Depends(current_admin),
           db: Session = Depends(get_db)):
    q = select(Video).options(joinedload(Video.user))
    if status in ("processing", "done", "failed"):
        q = q.where(Video.status == status)
    total = db.scalar(select(func.count()).select_from(q.order_by(None).subquery()))
    items = db.scalars(q.order_by(Video.id.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)).all()
    det_counts = dict(db.execute(
        select(Detection.video_id, func.count(Detection.id))
        .where(Detection.label == "no_helmet", Detection.is_false_positive.is_(False))
        .group_by(Detection.video_id)).all())
    return render(request, "videos.html", admin, active="videos", items=items, total=total, page=page,
                  pages=max(1, -(-total // PAGE_SIZE)), status=status, det_counts=det_counts)


# ---------- settings ----------
@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, saved: int = 0, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    return render(request, "settings.html", admin, active="settings", values=load_settings(db), saved=bool(saved), error=None)


# key -> (type, min, max, label used in error messages)
SETTING_RULES = {
    "confidence_threshold": (float, 0.05, 0.99, "confidence 0.05-0.99"),
    "frame_skip": (int, 1, 30, "frame skip 1-30"),
    "max_video_seconds": (int, 5, 3600, "max video 5-3600 s"),
    "min_box_px": (int, 0, 600, "min person height 0-600 px"),
    "min_track_hits": (int, 1, 20, "min frames per person 1-20"),
    "infer_imgsz": (int, 320, 1920, "image size 320-1920"),
}


@router.post("/settings", response_class=HTMLResponse)
async def settings_save(request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    form = await request.form()
    parsed, bad = {}, []
    for key, (kind, lo, hi, label) in SETTING_RULES.items():
        try:
            val = kind(form.get(key, ""))
        except ValueError:
            bad.append(label)
            continue
        if not lo <= val <= hi:
            bad.append(label)
        parsed[key] = val
    if bad:
        shown = {**load_settings(db), **{k: form.get(k, "") for k in SETTING_RULES}}
        return render(request, "settings.html", admin, active="settings", saved=False, values=shown,
                      error="Values out of range: " + "; ".join(bad) + ".")
    for key, val in parsed.items():
        row = db.get(Setting, key)
        if row:
            row.value = str(val)
        else:
            db.add(Setting(key=key, value=str(val)))
    db.commit()
    return RedirectResponse("/panel/settings?saved=1", status_code=303)


# ---------- export + media ----------
@router.get("/export.csv")
def export_csv(admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(Detection).options(joinedload(Detection.video).joinedload(Video.user))
                      .order_by(Detection.id)).unique().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["detection_id", "video_id", "user_email", "label", "confidence", "timestamp_seconds",
                "is_false_positive", "created_at"])
    for d in rows:
        w.writerow([d.id, d.video_id, d.video.user.email if d.video.user else "", d.label,
                    f"{d.confidence:.3f}", f"{d.timestamp_seconds:.2f}", d.is_false_positive, d.created_at])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=detections.csv"})


@router.get("/export-training.zip")
def export_training(include: str = "fp", admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    """Zip of un-annotated frames + YOLO label files for retraining.

    include=fp  : only detections flagged as false positive, labelled with the OPPOSITE class (a proposal).
    include=all : every detection, labelled as the model predicted (unreviewed pseudo-labels).
    Labels must be checked by a human before training (e.g. in Roboflow or LabelImg).
    """
    q = select(Detection).where(Detection.screenshot_path.is_not(None))
    q = q.where(Detection.is_false_positive.is_(True)) if include == "fp" else q
    zbuf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_STORED) as z:
        for d in db.scalars(q.order_by(Detection.id)):
            path = config.RESULTS_DIR / raw_path(d.screenshot_path)
            if not path.is_file():
                continue  # older detections have no raw frame saved
            data = path.read_bytes()
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                continue
            h, w = img.shape[:2]
            cls = {"helmet": 0, "no_helmet": 1}[d.label]
            if d.is_false_positive:
                cls = 1 - cls
            cx, cy = (d.bbox_x1 + d.bbox_x2) / 2 / w, (d.bbox_y1 + d.bbox_y2) / 2 / h
            bw, bh = (d.bbox_x2 - d.bbox_x1) / w, (d.bbox_y2 - d.bbox_y1) / h
            z.writestr(f"images/det_{d.id}.jpg", data)
            z.writestr(f"labels/det_{d.id}.txt", f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
            count += 1
        z.writestr("data.yaml", "train: images\nval: images\nnc: 2\nnames: [helmet, no_helmet]\n")
        z.writestr("README.txt",
                   f"{count} frames exported (include={include}).\n"
                   "Classes: 0=helmet, 1=no_helmet.\n"
                   "For include=fp the label is the OPPOSITE of what the model said; if the person is neither\n"
                   "(e.g. not a person at all) delete that label file. Review every label before training.\n")
    zbuf.seek(0)
    return StreamingResponse(iter([zbuf.getvalue()]), media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename=training_{include}.zip"})


@router.get("/media/{path:path}")
def media(path: str, admin: User = Depends(current_admin)):
    root = config.RESULTS_DIR.resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(404)
    return FileResponse(target)
