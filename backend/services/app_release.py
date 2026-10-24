"""The Android app (APK) offered for download from the admin panel and the public /app page.

One file is kept on disk (storage/app/helmet-check.apk) with a small meta.json next to it.
"""
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import config

APP_DIR = config.STORAGE_DIR / "app"
APK_PATH = APP_DIR / "helmet-check.apk"
META_PATH = APP_DIR / "meta.json"
MAX_APK_MB = 80  # stays under Cloudflare's 100 MB request limit


class InvalidApk(ValueError):
    pass


def validate_apk(path: Path) -> None:
    """An APK is a zip that contains AndroidManifest.xml and compiled code; reject anything else."""
    if not zipfile.is_zipfile(path):
        raise InvalidApk("This is not an APK file.")
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
    if "AndroidManifest.xml" not in names or not any(n.endswith(".dex") for n in names):
        raise InvalidApk("This zip does not look like an Android app (APK).")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def info() -> dict | None:
    """Metadata of the published APK, or None if nothing is published."""
    if not APK_PATH.is_file() or not META_PATH.is_file():
        return None
    try:
        meta = json.loads(META_PATH.read_text())
    except (OSError, ValueError):
        return None
    meta["size_mb"] = round(APK_PATH.stat().st_size / 1024 / 1024, 1)
    meta["download_name"] = f"HelmetCheck-{meta['version']}.apk" if meta.get("version") else "HelmetCheck.apk"
    return meta


def save(tmp_path: Path, version: str) -> dict:
    """Validate the uploaded file and publish it, replacing the previous one."""
    validate_apk(tmp_path)
    APP_DIR.mkdir(parents=True, exist_ok=True)
    version = "".join(c for c in version.strip() if c.isalnum() or c in ".-_+")[:30]
    meta = {
        "version": version,
        "sha256": _sha256(tmp_path),
        "uploaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    staged = APP_DIR / "incoming.apk"
    shutil.move(str(tmp_path), staged)
    os.replace(staged, APK_PATH)              # atomic: a download never sees a half-written file
    META_PATH.write_text(json.dumps(meta))
    return info() or meta


def remove() -> None:
    APK_PATH.unlink(missing_ok=True)
    META_PATH.unlink(missing_ok=True)
