"""Public download page for the Android app. Only admins can upload (see admin/panel.py)."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from services import app_release

router = APIRouter(tags=["app"], include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "admin" / "templates"))

APK_MEDIA_TYPE = "application/vnd.android.package-archive"


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
