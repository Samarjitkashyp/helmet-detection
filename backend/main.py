from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

import config
from admin.crud import PANEL_COOKIE, SESSION_MAX_AGE, mount_sqladmin
from admin.panel import NotLoggedIn
from admin.panel import router as panel_router
from api.routes_app import router as app_router
from api.routes_auth import router as auth_router
from api.routes_video import router as video_router
from db.database import Base, engine
from services.video_processor import fail_stale_jobs

config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(engine)  # replaced by Alembic migrations later
fail_stale_jobs()

docs = {} if config.DOCS_ENABLED else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="Helmet Detection API", **docs)


@app.middleware("http")
async def admin_ip_allowlist(request: Request, call_next):
    """If ADMIN_ALLOWED_IPS is set, the admin panel and data editor answer 404 to everyone else."""
    if config.ADMIN_ALLOWED_IPS and request.url.path.startswith(("/panel", "/admin")):
        host = request.client.host if request.client else ""
        if host not in config.ADMIN_ALLOWED_IPS:
            return JSONResponse({"detail": "Not Found"}, status_code=404)
    return await call_next(request)


app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie=PANEL_COOKIE,
                   max_age=SESSION_MAX_AGE, same_site="lax", https_only=config.COOKIE_SECURE)


@app.exception_handler(NotLoggedIn)
async def not_logged_in(request: Request, exc: NotLoggedIn):
    return RedirectResponse("/panel/login", status_code=303)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/panel/")


app.include_router(auth_router)
app.include_router(video_router)
app.include_router(app_router)
app.include_router(panel_router)
mount_sqladmin(app)
