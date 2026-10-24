"""Measure which inference image size / confidence threshold works best on held-out test images.

Usage: python -I training/eval_settings.py
Builds a fixed random 300-image subset of data_merged/test, runs validation at several image sizes and
prints precision / recall / F1 per class at several confidence thresholds.
"""
import random
import shutil
import sys
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path(r"E:\helmet_detection")
SRC = ROOT / "data_merged" / "test"
SUB = ROOT / "training" / "eval_subset"
N_IMAGES = 300
IMGSZ = [640, 800, 960]
CONFS = [0.25, 0.35, 0.45, 0.5, 0.55, 0.65, 0.75]


def build_subset():
    if SUB.exists():
        shutil.rmtree(SUB)
    (SUB / "images").mkdir(parents=True)
    (SUB / "labels").mkdir(parents=True)
    imgs = sorted((SRC / "images").iterdir())
    for p in random.Random(11).sample(imgs, N_IMAGES):
        shutil.copy2(p, SUB / "images" / p.name)
        shutil.copy2(SRC / "labels" / (p.stem + ".txt"), SUB / "labels" / (p.stem + ".txt"))
    (SUB / "data.yaml").write_text(
        f"path: {SUB.as_posix()}\ntrain: images\nval: images\nnc: 2\nnames: [helmet, no_helmet]\n")


def main():
    build_subset()
    model = YOLO(str(ROOT / "backend" / "models" / "best.pt"))
    for sz in IMGSZ:
        m = model.val(data=str(SUB / "data.yaml"), imgsz=sz, batch=8, plots=False, verbose=False, workers=0)
        b = m.box
        px = np.linspace(0, 1, 1000)
        print(f"\n=== imgsz {sz}: mAP50={b.map50:.3f} mAP50-95={b.map:.3f}", flush=True)
        print("  conf | helmet P/R/F1 | no_helmet P/R/F1", flush=True)
        for c in CONFS:
            i = int(np.argmin(np.abs(px - c)))
            row = []
            for k in range(2):
                p, r = float(b.p_curve[k][i]), float(b.r_curve[k][i])
                f1 = 2 * p * r / (p + r) if p + r else 0.0
                row.append(f"{p:.2f}/{r:.2f}/{f1:.2f}")
            print(f"  {c:.2f} | {row[0]} | {row[1]}", flush=True)
    print("\nDONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
