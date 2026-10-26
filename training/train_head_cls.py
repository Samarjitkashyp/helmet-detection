"""Train the head-crop classifier (helmet vs no_helmet) that double-checks the detector's verdict.

Training data: CCTV head crops mined from the Myanmar training clips (mine_head_crops.py), plus general
crops (crop_merged_heads.py). Validation: CCTV crops of held-out clips only, so the score reflects the target
domain. The CCTV class counts are balanced by sampling, because most CCTV riders have no helmet.

Usage: python -I training/train_head_cls.py [epochs]
Output: backend/models/head_cls.pt  (+ training/_exp/cls_runs/...)
"""
import random
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "training" / "_exp"
CCTV, EXTRA = EXP / "headcls", EXP / "headcls_extra"
STAGE = EXP / "headcls_stage"
EPOCHS = int(sys.argv[1]) if len(sys.argv) > 1 else 25
random.seed(11)


def files(d):
    return sorted(d.glob("*.jpg")) if d.is_dir() else []


if STAGE.exists():
    shutil.rmtree(STAGE)
MAX_CCTV, MAX_EXTRA, MAX_VAL = 2500, 1000, 600     # per class: keeps a CPU-only training run to about half an hour
n = {}
for cls in ("helmet", "no_helmet"):
    cctv_train = files(CCTV / "train" / cls)
    random.shuffle(cctv_train)
    cctv_train = cctv_train[:MAX_CCTV]
    extra = files(EXTRA / cls)
    random.shuffle(extra)
    chosen = [("cctv", p) for p in cctv_train] + [("extra", p) for p in extra[:MAX_EXTRA]]
    n[cls] = len(chosen)
    for src, p in chosen:
        dst = STAGE / "train" / cls / f"{src}_{p.name}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    val = files(CCTV / "val" / cls)
    random.shuffle(val)
    for p in val[:MAX_VAL]:
        dst = STAGE / "val" / cls / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
print("train images per class:", n, flush=True)
print("val images:", {c: len(files(STAGE / "val" / c)) for c in ("helmet", "no_helmet")}, flush=True)

model = YOLO("yolov8n-cls.pt")
model.train(data=str(STAGE), epochs=EPOCHS, imgsz=96, batch=64, workers=4, project=str(EXP / "cls_runs"),
            name="head_cls", exist_ok=True, patience=8, fliplr=0.5, hsv_h=0.02, hsv_s=0.5, hsv_v=0.4,
            degrees=8, scale=0.3, erasing=0.2, verbose=False)
best = EXP / "cls_runs" / "head_cls" / "weights" / "best.pt"
shutil.copy2(best, ROOT / "backend" / "models" / "head_cls.pt")
print("saved backend/models/head_cls.pt", flush=True)
