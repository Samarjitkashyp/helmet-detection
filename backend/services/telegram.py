"""Minimal Telegram Bot API client (standard library only). Errors never include the URL: it holds the bot token."""
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid

import config


def configured() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def _post(method: str, body: bytes, content_type: str) -> bool:
    req = urllib.request.Request(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}", data=body,
                                 headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return bool(json.load(r).get("ok"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"telegram {method} failed: {type(e).__name__}", flush=True)
        return False


def send_message(text: str) -> bool:
    if not configured():
        return False
    body = urllib.parse.urlencode({"chat_id": config.TELEGRAM_CHAT_ID, "text": text}).encode()
    return _post("sendMessage", body, "application/x-www-form-urlencoded")


def send_photo(jpeg: bytes, caption: str) -> bool:
    if not configured():
        return False
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (("chat_id", config.TELEGRAM_CHAT_ID), ("caption", caption)):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="alert.jpg"\r\n'
                 f"Content-Type: image/jpeg\r\n\r\n".encode() + jpeg + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return _post("sendPhoto", b"".join(parts), f"multipart/form-data; boundary={boundary}")
