import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PROD = APP_ENV == "production"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:CHANGE_ME@localhost:5432/helmet_db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))

# production hardening (all overridable from .env)
COOKIE_SECURE = _flag("COOKIE_SECURE", IS_PROD)              # admin session cookie only over HTTPS
DOCS_ENABLED = _flag("DOCS_ENABLED", not IS_PROD)            # /docs, /redoc, /openapi.json
ADMIN_ALLOWED_IPS = [ip.strip() for ip in os.getenv("ADMIN_ALLOWED_IPS", "").split(",") if ip.strip()]
KEEP_ORIGINAL_VIDEOS = _flag("KEEP_ORIGINAL_VIDEOS", True)   # false = delete the upload once analysed (saves disk)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "300"))       # behind Cloudflare's proxy keep this under 100

STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULTS_DIR = STORAGE_DIR / "results"
MODEL_PATH = BASE_DIR / "models" / "best.pt"

if IS_PROD and (SECRET_KEY == "dev-only-change-me" or len(SECRET_KEY) < 32):
    raise RuntimeError("APP_ENV=production needs a SECRET_KEY of at least 32 characters in .env")
if IS_PROD and "CHANGE_ME" in DATABASE_URL:
    raise RuntimeError("APP_ENV=production needs a real DATABASE_URL in .env")
