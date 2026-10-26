"""Cut head crops out of the general training set (data_merged) as extra, more varied examples (caps, hats,
many helmet types) for the head-crop classifier. Run once: python -I training/crop_merged_heads.py [per_class]"""
import random
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data_merged" / "train"
OUT = ROOT / "training" / "_exp" / "headcls_extra"
PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
random.seed(7)

items = {0: [], 1: []}
for lab in (SRC / "labels").glob("*.txt"):
    for line in lab.read_text().splitlines():
        p = line.split()
        if len(p) == 5 and p[0] in ("0", "1"):
            items[int(p[0])].append((lab.stem, [float(v) for v in p[1:]]))
print({k: len(v) for k, v in items.items()}, flush=True)

for cls, name in ((0, "helmet"), (1, "no_helmet")):
    (OUT / name).mkdir(parents=True, exist_ok=True)
    random.shuffle(items[cls])
    saved = 0
    for stem, (cx, cy, w, h) in items[cls]:
        if saved >= PER_CLASS:
            break
        img_path = next((SRC / "images").glob(stem + ".*"), None)
        img = cv2.imread(str(img_path)) if img_path else None
        if img is None:
            continue
        H, W = img.shape[:2]
        bw, bh = w * W, h * H
        if min(bw, bh) < 24:
            continue
        m = 0.15 * max(bw, bh)
        x1, y1, x2, y2 = int(cx * W - bw / 2 - m), int(cy * H - bh / 2 - m), int(cx * W + bw / 2 + m), int(cy * H + bh / 2 + m)
        crop = img[max(0, y1):y2, max(0, x1):x2]
        if crop.size:
            cv2.imwrite(str(OUT / name / f"{stem}_{saved}.jpg"), crop)
            saved += 1
    print(name, saved, flush=True)
