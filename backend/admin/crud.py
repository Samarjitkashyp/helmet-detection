"""SQLAdmin (auto CRUD pages under /admin). Shares the /panel login session."""
import base64
import json

import itsdangerous
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

import config
from admin.panel import SESSION_KEY
from db.database import SessionLocal, engine
from db.models import Detection, Setting, User, Video

PANEL_COOKIE = "panel_session"
SESSION_MAX_AGE = 14 * 24 * 3600


def _panel_user_id(request: Request) -> int | None:
    """Decode the signed Starlette session cookie set by the /panel login."""
    raw = request.cookies.get(PANEL_COOKIE)
    if not raw:
        return None
    try:
        data = itsdangerous.TimestampSigner(config.SECRET_KEY).unsign(raw.encode(), max_age=SESSION_MAX_AGE)
        return json.loads(base64.b64decode(data)).get(SESSION_KEY)
    except (itsdangerous.BadSignature, ValueError):
        return None


class PanelAuth(AuthenticationBackend):
    async def login(self, request: Request):
        return RedirectResponse("/panel/login", status_code=303)

    async def logout(self, request: Request):
        return RedirectResponse("/panel/logout", status_code=303)

    async def authenticate(self, request: Request):
        user_id = _panel_user_id(request)
        if user_id:
            with SessionLocal() as db:
                user = db.get(User, user_id)
                if user and user.role == "admin" and user.is_active:
                    return True
        return RedirectResponse("/panel/login", status_code=303)


class UserAdmin(ModelView, model=User):
    name, name_plural, icon = "User", "Users", "fa-solid fa-users"
    column_list = [User.id, User.name, User.email, User.role, User.is_active, User.created_at]
    column_searchable_list = [User.name, User.email]
    column_sortable_list = [User.id, User.name, User.created_at]
    form_columns = [User.name, User.role, User.is_active]  # users register via the app; no password edits here
    can_create = False


class VideoAdmin(ModelView, model=Video):
    name, name_plural, icon = "Video", "Videos", "fa-solid fa-video"
    column_list = [Video.id, Video.filename, Video.user, Video.status, Video.duration_seconds, Video.uploaded_at]
    column_searchable_list = [Video.filename]
    column_sortable_list = [Video.id, Video.uploaded_at, Video.status]
    can_create = False
    can_edit = False


class DetectionAdmin(ModelView, model=Detection):
    name, name_plural, icon = "Detection", "Detections", "fa-solid fa-triangle-exclamation"
    column_list = [Detection.id, Detection.video_id, Detection.label, Detection.confidence,
                   Detection.timestamp_seconds, Detection.is_false_positive]
    column_sortable_list = [Detection.id, Detection.confidence, Detection.timestamp_seconds]
    form_columns = [Detection.is_false_positive]
    can_create = False


class SettingAdmin(ModelView, model=Setting):
    name, name_plural, icon = "Setting", "Settings", "fa-solid fa-gear"
    column_list = [Setting.key, Setting.value]
    form_columns = [Setting.key, Setting.value]


def mount_sqladmin(app: FastAPI) -> None:
    admin = Admin(app, engine, base_url="/admin", authentication_backend=PanelAuth(secret_key=config.SECRET_KEY),
                  title="Helmet Admin")
    for view in (UserAdmin, VideoAdmin, DetectionAdmin, SettingAdmin):
        admin.add_view(view)
