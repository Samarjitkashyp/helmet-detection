"""Head labels from the Indian rider labels (Kaggle master_traffic_violation: boxes around RIDERS marked WithHelmet / WithoutHelmet).

Our detector finds heads inside each labelled rider box; the best head there gets the rider's label (0 = helmet, 1 = no_helmet), even when
the detector disagrees: those are exactly the mistakes we want to teach it. Riders without any believable head are skipped (no guessed boxes).
Same idea as for the Myanmar data (mine_head_crops.py). Pedestrians and unlabelled people stay unlabelled.

Output: training/_exp/finetune_india/{train,val}/{images,labels}
  train = a sample of the dataset's train split, one picture per source photo (Roboflow made 3 augmented copies of each)
  val   = the dataset's valid + test splits (the same 577-image set used by eval_indian.py), never used for training

Usage: python -I training/make_indian_labels.py [train_images]      (default 3000)
"""
import collections
import random
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "data_india" / "kaggle" / "master_traffic_violation" / "master_traffic_violation_dataset"
OUT = ROOT / "training" / "_exp" / "finetune_india"
N_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
WITH, WITHOUT = 1, 2
random.seed(11)


def load(split):
    items = {}
    for ip in sorted((DS / split / "images").glob("*.jpg")):
        key = ip.name.split(".rf.")[0]
        if key in items:
            continue                       # an augmented copy of a photo we already have
        riders = []
        for line in (DS / split / "labels" / (ip.stem + ".txt")).read_text().splitlines():
            p = line.split()
            if len(p) == 5 and int(p[0]) in (WITH, WITHOUT):
                cx, cy, w, h = map(float, p[1:])
                riders.append((int(p[0]) == WITHOUT, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))
        if riders:
            items[key] = (ip, riders)
    return items


def head_for(rider_box, heads):
    x1, y1, x2, y2 = rider_box
    rw, rh = x2 - x1, y2 - y1
    best = None
    for conf, (a1, b1, a2, b2) in heads:
        cx, cy = (a1 + a2) / 2, (b1 + b2) / 2
        if not (x1 <= cx <= x2 and y1 <= cy <= y1 + 0.6 * rh):
            continue
        if (b2 - b1) > 0.45 * rh or (a2 - a1) > 0.8 * rw or (b2 - b1) < 0.02:
            continue
        if best is None or conf > best[0]:
            best = (conf, (a1, b1, a2, b2))
    return best


def run(name, items):
    model = YOLO(str(ROOT / "backend" / "models" / "best.pt"))
    (OUT / name / "images").mkdir(parents=True, exist_ok=True)
    (OUT / name / "labels").mkdir(parents=True, exist_ok=True)
    stats = collections.Counter()
    for i, (key, (ip, riders)) in enumerate(items):
        img = cv2.imread(str(ip))
        h, w = img.shape[:2]
        r = model.predict(img, imgsz=960, conf=0.2, verbose=False)[0]
        heads = [(float(s), (b[0] / w, b[1] / h, b[2] / w, b[3] / h)) for b, s in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist())]
        rows = []
        for bare, box in riders:
            stats["riders"] += 1
            hd = head_for(box, heads)
            if hd is None:
                stats["no head found"] += 1
                continue
            a1, b1, a2, b2 = hd[1]
            rows.append(f"{1 if bare else 0} {(a1 + a2) / 2:.6f} {(b1 + b2) / 2:.6f} {a2 - a1:.6f} {b2 - b1:.6f}")
            stats["labelled no_helmet" if bare else "labelled helmet"] += 1
        if rows:
            stem = f"in_{key}"
            cv2.imwrite(str(OUT / name / "images" / f"{stem}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
            (OUT / name / "labels" / f"{stem}.txt").write_text("\n".join(rows) + "\n")
            stats["images"] += 1
        if i % 200 == 0:
            print(f"  {name} {i}/{len(items)} {dict(stats)}", flush=True)
    print(name, dict(stats), flush=True)


train_all = load("train")
val_all = {**load("valid"), **load("test")}
overlap = set(train_all) & set(val_all)
print(f"unique source photos: train {len(train_all)}, valid+test {len(val_all)}, shared between them: {len(overlap)}", flush=True)
train_pool = [kv for kv in train_all.items() if kv[0] not in val_all]
bare_imgs = [kv for kv in train_pool if any(b for b, _ in kv[1][1])]
helm_imgs = [kv for kv in train_pool if not any(b for b, _ in kv[1][1])]
random.shuffle(bare_imgs); random.shuffle(helm_imgs)
n_h = min(len(helm_imgs), N_TRAIN // 3)
train_items = bare_imgs[:N_TRAIN - n_h] + helm_imgs[:n_h]
print(f"train sample: {len(train_items)} photos ({len(bare_imgs)} with a bare-headed rider, {len(helm_imgs)} helmet only available)", flush=True)
run("val", list(val_all.items()))
run("train", train_items)
