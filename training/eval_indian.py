"""Indian-road test of helmet models on Kaggle's master_traffic_violation dataset (valid + test splits, 577 images the models never saw).

The dataset labels RIDER boxes (a person on a bike) as WithHelmet or WithoutHelmet, not heads. A model that finds heads is scored per rider:
a rider is called "no helmet" when a no_helmet head whose centre lies in the upper part of the rider box is found, "helmet" when only
helmet heads are found there, and "missed" when no head is found at all.

  python -I training/eval_indian.py            runs every model once (slow on CPU) and caches the detections, then prints the tables
  python -I training/eval_indian.py --table    only prints the tables from the cache
"""
import pickle
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "data_india" / "kaggle" / "master_traffic_violation" / "master_traffic_violation_dataset"
CACHE = ROOT / "training" / "_exp" / "indian_cache.pkl"
WITH, WITHOUT = 1, 2
MODELS = {   # name: (weights, image size, class number of helmet, class number of bare head)
    "ours (CCTV fine-tune, 1280)": (ROOT / "backend" / "models" / "best.pt", 1280, 0, 1),
    "ours (CCTV fine-tune, 640)": (ROOT / "backend" / "models" / "best.pt", 640, 0, 1),
    "NEW ours + India (1280)": (ROOT / "best (1).pt", 1280, 0, 1),
    "NEW ours + India (640)": (ROOT / "best (1).pt", 640, 0, 1),
    "smolry helmet.onnx (640)": (ROOT / "data_india" / "smolry-helmet" / "helmet.onnx", 640, 0, 1),
    "dxvyaaa best.pt (416)": (ROOT / "data_india" / "dxvyaaa-yolo-helmet" / "best.pt", 416, 0, 1),
}


def gt_riders():
    items = []
    for split in ("valid", "test"):
        for ip in sorted((DS / split / "images").glob("*.jpg")):
            lp = DS / split / "labels" / (ip.stem + ".txt")
            riders = []
            for line in lp.read_text().splitlines():
                p = line.split()
                if len(p) == 5 and int(p[0]) in (WITH, WITHOUT):
                    cx, cy, w, h = map(float, p[1:])
                    riders.append((int(p[0]) == WITHOUT, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))
            items.append((ip, riders))
    return items


def run_models(items):
    from ultralytics import YOLO
    cache = pickle.load(open(CACHE, "rb")) if CACHE.exists() else {}
    for name, (weights, imgsz, _, _) in MODELS.items():
        if name in cache:
            continue
        print("running", name, flush=True)
        model = YOLO(str(weights), task="detect")
        out = {}
        for i, (ip, _) in enumerate(items):
            img = cv2.imread(str(ip))
            h, w = img.shape[:2]
            r = model.predict(img, imgsz=imgsz, conf=0.15, verbose=False)[0]
            out[str(ip)] = [(int(c), float(s), (b[0] / w, b[1] / h, b[2] / w, b[3] / h))
                            for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
            if i % 100 == 0:
                print("  ", i, "/", len(items), flush=True)
        cache[name] = out
        CACHE.parent.mkdir(exist_ok=True)
        pickle.dump(cache, open(CACHE, "wb"))
    return cache


def score(items, dets, helmet_cls, head_cls, conf):
    tp = fn_bare = fa = ok_helmet = miss_bare = miss_helm = n_bare = n_helm = 0
    for ip, riders in items:
        heads = [(c, b) for c, s, b in dets[str(ip)] if s >= conf]
        for bare, (x1, y1, x2, y2) in riders:
            inside = []
            for c, (a1, b1, a2, b2) in heads:
                cx, cy = (a1 + a2) / 2, (b1 + b2) / 2
                if x1 <= cx <= x2 and y1 <= cy <= y1 + 0.6 * (y2 - y1):
                    inside.append(c)
            said_bare = head_cls in inside
            said_helmet = helmet_cls in inside and not said_bare
            if bare:
                n_bare += 1
                tp += said_bare
                fn_bare += said_helmet
                miss_bare += (not inside)
            else:
                n_helm += 1
                fa += said_bare
                ok_helmet += said_helmet
                miss_helm += (not inside)
    return n_bare, n_helm, tp, fn_bare, miss_bare, fa, ok_helmet, miss_helm


def tables(items, cache):
    nb = sum(1 for _, r in items for b, _ in r if b)
    nh = sum(1 for _, r in items for b, _ in r if not b)
    print(f"\n{len(items)} images, {nb} riders without helmet, {nh} riders with helmet\n")
    print(f"{'model':32} {'conf':>5} {'bare caught':>12} {'bare said helmet':>17} {'bare missed':>12} {'helmeted false alarm':>21} {'helmeted missed':>16}")
    for name, (_, _, hc, bc) in MODELS.items():
        if name not in cache:
            continue
        for conf in (0.25, 0.4, 0.55):
            n_bare, n_helm, tp, fnb, mb, fa, okh, mh = score(items, cache[name], hc, bc, conf)
            print(f"{name:32} {conf:5.2f} {tp / n_bare:11.0%} {fnb / n_bare:16.0%} {mb / n_bare:11.0%} {fa / n_helm:20.0%} {mh / n_helm:15.0%}")


if __name__ == "__main__":
    items = gt_riders()
    cache = pickle.load(open(CACHE, "rb")) if "--table" in sys.argv and CACHE.exists() else run_models(items)
    tables(items, cache)
