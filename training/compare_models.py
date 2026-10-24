"""Compare two YOLO weights on held-out test images, split into 'original' and 'head-covering' groups.

Usage: python -I training/compare_models.py best.pt best_v2.pt
Both files are looked up in backend/models. Output: mAP50, and precision/recall/F1 at conf 0.4 per class.
"""
import random
import shutil
import sys
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path(r"E:\helmet_detection")
TEST = ROOT / "data_merged" / "test"
WORK = ROOT / "training" / "compare_subsets"
CONF = 0.4
N_ORIGINAL = 300


def make_subset(name: str, files: list[Path]) -> Path:
    d = WORK / name
    (d / "images").mkdir(parents=True)
    (d / "labels").mkdir(parents=True)
    for p in files:
        shutil.copy2(p, d / "images" / p.name)
        shutil.copy2(TEST / "labels" / (p.stem + ".txt"), d / "labels" / (p.stem + ".txt"))
    (d / "data.yaml").write_text(
        f"path: {d.as_posix()}\ntrain: images\nval: images\nnc: 2\nnames: [helmet, no_helmet]\n")
    return d / "data.yaml"


def main(old_name: str, new_name: str):
    if WORK.exists():
        shutil.rmtree(WORK)
    imgs = sorted((TEST / "images").iterdir())
    extra = [p for p in imgs if p.name.startswith("extra_")]
    original = [p for p in imgs if not p.name.startswith("extra_")]
    original = random.Random(11).sample(original, N_ORIGINAL)
    sets = {"original (riders/people, 300 imgs)": make_subset("original", original),
            f"head-coverings (cap/hat/hijab, {len(extra)} imgs)": make_subset("extra", extra)}

    px = np.linspace(0, 1, 1000)
    i = int(np.argmin(np.abs(px - CONF)))
    for label, yaml_path in sets.items():
        print(f"\n##### TEST SET: {label}", flush=True)
        for name in (old_name, new_name):
            m = YOLO(str(ROOT / "backend" / "models" / name)).val(
                data=str(yaml_path), imgsz=640, batch=8, plots=False, verbose=False, workers=0)
            b = m.box
            cells = []
            for k, cls in enumerate(["helmet", "no_helmet"]):
                if k >= len(b.p_curve) or not len(b.p_curve[k]):
                    continue
                p, r = float(b.p_curve[k][i]), float(b.r_curve[k][i])
                f1 = 2 * p * r / (p + r) if p + r else 0.0
                cells.append(f"{cls} P={p:.2f} R={r:.2f} F1={f1:.2f}")
            print(f"{name:12} mAP50={b.map50:.3f} mAP50-95={b.map:.3f} | at conf {CONF}: " + " | ".join(cells), flush=True)
    shutil.rmtree(WORK, ignore_errors=True)
    print("\nDONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
