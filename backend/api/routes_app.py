"""Public download page for the Android app. Only admins can upload (see admin/panel.py)."""
import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

import config
from core.deps import get_current_user
from db.models import User
from services import app_release

router = APIRouter(tags=["app"], include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "admin" / "templates"))
templates.env.globals["published_app"] = app_release.info

APK_MEDIA_TYPE = "application/vnd.android.package-archive"

# On-device model for the app's live detection boxes (created by training/export_onnx.py).
LIVE_MODEL = config.BASE_DIR / "models" / "live.onnx"
LIVE_MODEL_META = LIVE_MODEL.with_suffix(".json")
_live_cache: dict = {}


def _live_info() -> dict | None:
    if not LIVE_MODEL.is_file():
        return None
    st = LIVE_MODEL.stat()
    key = (st.st_mtime_ns, st.st_size)
    if _live_cache.get("key") != key:   # hash again only when the file changed
        h = hashlib.sha256()
        with open(LIVE_MODEL, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        try:
            meta = json.loads(LIVE_MODEL_META.read_text())
        except (OSError, ValueError):
            meta = {}
        _live_cache.update(key=key, info={"version": h.hexdigest()[:16], "size": st.st_size,
                                          "imgsz": int(meta.get("imgsz", 416)),
                                          "classes": meta.get("classes", ["helmet", "no_helmet"])})
    return _live_cache["info"]


@router.get("/app/live-model/info")
def live_model_info(user: User = Depends(get_current_user)):
    info = _live_info()
    if not info:
        raise HTTPException(404, "Live detection model is not available.")
    return info


@router.get("/app/live-model")
def live_model(user: User = Depends(get_current_user)):
    if not _live_info():
        raise HTTPException(404, "Live detection model is not available.")
    return FileResponse(LIVE_MODEL, media_type="application/octet-stream", filename="live.onnx",
                        headers={"Cache-Control": "no-cache"})


@router.get("/app", response_class=HTMLResponse)
def app_page(request: Request):
    return templates.TemplateResponse(request, "app_download.html", {"admin": None, "app": app_release.info()})


@router.get("/app/download")
def app_download():
    meta = app_release.info()
    if not meta:
        raise HTTPException(404, "The app is not available yet.")
    return FileResponse(
        app_release.APK_PATH,
        media_type=APK_MEDIA_TYPE,
        filename=meta["download_name"],
        headers={"Cache-Control": "no-cache"},  # a new upload must reach users immediately
    )
