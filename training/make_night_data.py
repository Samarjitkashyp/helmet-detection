"""Make night-looking training data from the daytime CCTV frames (same labels, darkened / infrared-style / dusk).

There is no real night footage in the Myanmar dataset, so this is a stand-in: it teaches the model what dark,
noisy, grey infrared images with headlight glare look like. It does not replace real night footage from your own
cameras (add that in the Colab notebook, step 3).

Usage: python -I training/make_night_data.py [train_frames] [val_frames]
Output: training/_exp/finetune_night/{train,val_night,val_day}/{images,labels}
        (val_day = the same validation frames left in daylight, for an honest day-vs-night comparison)
"""
import random
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "training" / "_exp" / "finetune_cctv"
OUT = ROOT / "training" / "_exp" / "finetune_night"
N_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 900
N_VAL = int(sys.argv[2]) if len(sys.argv) > 2 else 200
rng = np.random.default_rng(21)
random.seed(21)


def glare(f, count):
    h, w = f.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(count):                       # headlights and street lamps
        cx, cy, r = rng.uniform(0, w), rng.uniform(0.3 * h, h), rng.uniform(20, 90)
        blob = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
        f += (blob * rng.uniform(0.3, 0.9))[..., None]
    return f


def lowlight(img):
    f = (img.astype(np.float32) / 255) ** rng.uniform(2.2, 3.4) * rng.uniform(0.12, 0.5)
    f[..., 0] *= rng.uniform(1.0, 1.3)           # blue-ish night colour (BGR order)
    f[..., 2] *= rng.uniform(0.7, 0.95)
    if rng.random() < 0.6:
        f = glare(f, int(rng.integers(1, 4)))
    f += rng.normal(0, rng.uniform(4, 13) / 255, f.shape)
    out = np.clip(f, 0, 1)
    return cv2.GaussianBlur((out * 255).astype(np.uint8), (3, 3), 0) if rng.random() < 0.4 else (out * 255).astype(np.uint8)


def infrared(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g = np.clip(g ** rng.uniform(1.3, 2.0) * rng.uniform(0.8, 1.4), 0, 1)
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    g *= np.clip(1.15 - 0.9 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2), 0.25, 1)    # IR light falls off to the corners
    f = np.repeat(g[..., None], 3, axis=2)
    if rng.random() < 0.4:
        f = glare(f, int(rng.integers(1, 3)))
    f += rng.normal(0, rng.uniform(5, 15) / 255, f.shape)
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)


def dusk(img):
    f = (img.astype(np.float32) / 255) ** rng.uniform(1.4, 2.1) * rng.uniform(0.35, 0.75)
    f[..., 2] *= rng.uniform(1.0, 1.15)          # warm
    f += rng.normal(0, rng.uniform(2, 6) / 255, f.shape)
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)


def night(img):
    r = rng.random()
    return lowlight(img) if r < 0.5 else infrared(img) if r < 0.8 else dusk(img)


def build(subset, count, outs):
    imgs = sorted((SRC / subset / "images").glob("*.jpg"))
    by_clip = {}
    for p in imgs:
        by_clip.setdefault(p.stem.rsplit("_", 1)[0], []).append(p)
    per = max(1, -(-count // len(by_clip)))
    chosen = []
    for frames in by_clip.values():
        random.shuffle(frames)
        chosen += frames[:per]
    random.shuffle(chosen)
    for out_name, transform in outs:
        (OUT / out_name / "images").mkdir(parents=True, exist_ok=True)
        (OUT / out_name / "labels").mkdir(parents=True, exist_ok=True)
    for p in chosen[:count]:
        img = cv2.imread(str(p))
        if img.shape[1] > 1280:
            img = cv2.resize(img, (1280, round(img.shape[0] * 1280 / img.shape[1])), interpolation=cv2.INTER_AREA)
        for out_name, transform in outs:
            cv2.imwrite(str(OUT / out_name / "images" / p.name), transform(img) if transform else img, [cv2.IMWRITE_JPEG_QUALITY, 88])
            shutil.copy(SRC / subset / "labels" / (p.stem + ".txt"), OUT / out_name / "labels" / (p.stem + ".txt"))
    print(subset, len(chosen[:count]), "frames from", len(by_clip), "clips ->", [o for o, _ in outs], flush=True)


if OUT.exists():
    shutil.rmtree(OUT)
build("train", N_TRAIN, [("train", night)])
build("val", N_VAL, [("val_night", night), ("val_day", None)])

