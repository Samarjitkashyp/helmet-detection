"""Figures for the Axom AI helmet-detection research pages.

Runs the worker's own detection logic on frames of the public HELMET dataset (CC BY 4.0, clips the model never trained on),
pixelates every detected head so nobody is recognisable, draws the verdict boxes (red = no helmet, green = helmet)
and writes web-sized JPEGs plus the 1200x630 social-share image.

Usage (from the repo root):  python -I website/research/make_figures.py
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "dist" / "research" / "assets"
sys.path.insert(0, str(ROOT / "backend"))
from services.cctv_worker import FrameAnalyzer, HELMET, NO_HELMET, is_rider_head  # noqa: E402

RED, GREEN = (60, 60, 235), (80, 190, 60)          # BGR
FRAMES = [("Pakokku_urban_69", 40, "detection-street"), ("Yangon_II_33", 50, "detection-junction")]

args = argparse.Namespace(imgsz=768, conf=0.5, no_crops=False, crop_imgsz=512, vehicle_imgsz=640, no_classifier=False,
                          cls_threshold=0.85, all_heads=False, min_box=16, min_hits=2, single_conf=0.55,
                          tracker="simple", tracker_gate=1.5, crop_every=1)
an = FrameAnalyzer(args)
OUT.mkdir(parents=True, exist_ok=True)


def pixelate(img, box, blocks=5):
    x1, y1, x2, y2 = (int(v) for v in box)
    x1, y1 = max(0, x1), max(0, y1)
    roi = img[y1:y2, x1:x2]
    if roi.size == 0:
        return
    h, w = roi.shape[:2]
    small = cv2.resize(roi, (max(1, blocks), max(1, blocks)), interpolation=cv2.INTER_AREA)
    img[y1:y2, x1:x2] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def annotate(path):
    img = cv2.imread(str(path))
    vehicles, heads = an.detect(img)
    riders = [h for h in heads if is_rider_head(h[2], vehicles)]
    for _, _, b in riders:
        pixelate(img, b)
    for cls, conf, b in riders:
        x1, y1, x2, y2 = (int(v) for v in b)
        color = RED if cls == NO_HELMET else GREEN
        cv2.rectangle(img, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), color, 4)
    return img, sum(1 for c, _, _ in riders if c == NO_HELMET), sum(1 for c, _, _ in riders if c == HELMET)


def save_jpeg(img, name, width=1280, quality=82):
    h, w = img.shape[:2]
    if w > width:
        img = cv2.resize(img, (width, round(h * width / w)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT / name), img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    print("wrote", name, img.shape[1], "x", img.shape[0], (OUT / name).stat().st_size // 1024, "KB", flush=True)


first = None
for clip, frame_no, name in FRAMES:
    src = ROOT / "data_helmet_myanmar" / "clips" / clip / f"{frame_no}.jpg"
    img, bad, ok = annotate(src)
    print(clip, frame_no, "no helmet:", bad, "helmet:", ok, flush=True)
    save_jpeg(img, f"{name}.jpg")
    first = first if first is not None else img

# social share image 1200x630: the first figure with a dark panel and the title
card = cv2.resize(first, (1200, round(first.shape[0] * 1200 / first.shape[1])))
card = card[max(0, (card.shape[0] - 630) // 2):][:630]
if card.shape[0] < 630:
    card = cv2.copyMakeBorder(card, 0, 630 - card.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(32, 18, 11))
shade = np.zeros_like(card)
shade[:] = (32, 18, 11)
alpha = np.linspace(0.92, 0.35, 630)[:, None, None]
card = (card * (1 - alpha) + shade * alpha).astype(np.uint8)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

pil = Image.fromarray(cv2.cvtColor(card, cv2.COLOR_BGR2RGB))
d = ImageDraw.Draw(pil)


def font(size, bold=True):
    for p in ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


d.text((60, 70), "AXOM AI RESEARCH", font=font(30), fill=(52, 211, 153))
d.text((60, 130), "Helmet Detection", font=font(88), fill=(255, 255, 255))
d.text((60, 235), "AI that checks every rider,", font=font(44, False), fill=(226, 232, 240))
d.text((60, 292), "from a phone video or a CCTV camera", font=font(44, False), fill=(226, 232, 240))
d.text((60, 540), "aiaxom.co.in/research/helmet-detection", font=font(30), fill=(251, 191, 36))
pil.save(OUT / "og-helmet-detection.jpg", quality=86, optimize=True)
print("wrote og-helmet-detection.jpg", (OUT / "og-helmet-detection.jpg").stat().st_size // 1024, "KB")

