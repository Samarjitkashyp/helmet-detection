"""Held-out test of the old and the new helmet model on datasets neither was trained on (data_india/kaggle/*).

Head-box datasets: a ground-truth head is matched to the most confident detection with IoU >= 0.3 (heads are tiny).
Rider-box dataset (helmet_violations_roboflow): scored like eval_indian.py (head centre in the upper 60 % of the rider box);
photos that also exist in master_traffic_violation (used for training) are dropped by an average-hash check.

  python -I training/eval_heldout.py [--uit-check]   --uit-check prints how uit_helmet_v8's classes '0'/'1' line up with the model
"""
import pickle
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "data_india" / "kaggle"
CACHE = ROOT / "training" / "_exp" / "heldout_cache.pkl"
MODELS = {"old": ROOT / "backend" / "models" / "backup" / "best_before_india.pt", "new": ROOT / "backend" / "models" / "best.pt"}
N_PER_SET = 350
IMGSZ = 960
UIT_BARE = "0"          # from --uit-check: the model calls uit class '0' no_helmet (99 of 103) and class '1' helmet (181 of 181)
random.seed(5)
IMG_EXT = {".jpg", ".jpeg", ".png"}


def yolo_items(img_dir, lab_dir, helmet, bare):
    items = []
    for ip in sorted(img_dir.glob("*")):
        if ip.suffix.lower() not in IMG_EXT:
            continue
        lp = lab_dir / (ip.stem + ".txt")
        if not lp.exists():
            continue
        gts = []
        for line in lp.read_text().splitlines():
            p = line.split()
            if p and (p[0] in helmet or p[0] in bare):
                if len(p) == 5:
                    cx, cy, w, h = map(float, p[1:])
                    gts.append((p[0] in bare, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))
                elif len(p) > 6 and len(p) % 2 == 1:           # segmentation polygon: use its bounding box
                    xs = [float(v) for v in p[1::2]]; ys = [float(v) for v in p[2::2]]
                    gts.append((p[0] in bare, (min(xs), min(ys), max(xs), max(ys))))
        if gts:
            items.append((ip, gts))
    return items


def load_sets():
    sets = {}
    items = []
    for x in sorted((K / "bikes_helmets_voc_764").rglob("*.xml")):
        r = ET.parse(x).getroot()
        W = float(r.findtext("size/width")); H = float(r.findtext("size/height"))
        ip = None
        for ext in (".jpg", ".png", ".jpeg"):
            c = x.with_suffix(ext)
            if c.exists():
                ip = c
                break
        if ip is None:
            c = list(x.parent.glob(x.stem + ".*"))
            c = [a for a in c if a.suffix.lower() in IMG_EXT]
            ip = c[0] if c else None
        if ip is None:
            continue
        gts = []
        for o in r.findall("object"):
            b = o.find("bndbox")
            gts.append((o.findtext("name").startswith("Without"),
                        (float(b.findtext("xmin")) / W, float(b.findtext("ymin")) / H, float(b.findtext("xmax")) / W, float(b.findtext("ymax")) / H)))
        if gts:
            items.append((ip, gts))
    sets["bikes_helmets_voc (heads)"] = items
    items = []
    base = K / "driver_passenger_7class" / "data"
    for sp in ("test", "train", "vaid"):
        items += yolo_items(base / sp / "images", base / sp / "labels", {"0", "3"}, {"5", "6"})
    sets["driver_passenger_7class (heads)"] = items
    items = []
    for sp in ("train", "valid", "test"):
        items += yolo_items(K / "uit_helmet_v8" / sp / "images", K / "uit_helmet_v8" / sp / "labels", {"0" if UIT_BARE == "1" else "1"}, {UIT_BARE})
    sets["uit_helmet_v8 (heads)"] = items
    items = []
    base = K / "mp_final_dataset" / "Dataset" / "helmet_no_helmet_train_val"
    for sp in ("train", "val"):
        items += yolo_items(base / sp / "images", base / sp / "labels", {"0"}, {"1"})
    sets["mp_final helmet_no_helmet (heads)"] = items
    return sets


def ahash(img):
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (8, 8), interpolation=cv2.INTER_AREA)
    return (g > g.mean()).flatten()


def violations_items():
    seen = {}
    master = K / "master_traffic_violation" / "master_traffic_violation_dataset"
    mh = []
    for ip in master.rglob("*.jpg"):
        if "images" in ip.parts:
            im = cv2.imread(str(ip))
            if im is not None:
                mh.append(ahash(im))
    mh = np.array(mh)
    items, dup_m, dup_s = [], 0, 0
    for ver in ("HelmetViolations", "HelmetViolationsV2"):
        for sp in ("train", "valid", "test"):
            d = K / "helmet_violations_roboflow" / ver / sp
            for ip in sorted((d / "images").glob("*")):
                lp = d / "labels" / (ip.stem + ".txt")
                if ip.suffix.lower() not in IMG_EXT or not lp.exists():
                    continue
                riders = []
                for line in lp.read_text().splitlines():
                    p = line.split()
                    if len(p) == 5 and p[0] in ("1", "2"):
                        cx, cy, w, h = map(float, p[1:])
                        riders.append((p[0] == "2", (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))
                if not riders:
                    continue
                im = cv2.imread(str(ip))
                if im is None:
                    continue
                hh = ahash(im)
                if len(mh) and (mh != hh).sum(axis=1).min() <= 5:
                    dup_m += 1
                    continue
                key = hh.tobytes()
                if key in seen:
                    dup_s += 1
                    continue
                seen[key] = 1
                items.append((ip, riders))
    print(f"violations: kept {len(items)}, dropped {dup_m} (also in master_traffic) and {dup_s} (repeats)", flush=True)
    return items


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0


def detect(items, label):
    from ultralytics import YOLO
    cache = pickle.load(open(CACHE, "rb")) if CACHE.exists() else {}
    for mname, w in MODELS.items():
        key = (mname, label)
        if key in cache and all(str(ip) in cache[key] for ip, _ in items):
            continue
        print("running", mname, label, len(items), flush=True)
        m = YOLO(str(w))
        out = cache.get(key, {})
        for i, (ip, _) in enumerate(items):
            if str(ip) in out:
                continue
            img = cv2.imread(str(ip))
            h, wd = img.shape[:2]
            r = m.predict(img, imgsz=IMGSZ, conf=0.15, verbose=False)[0]
            out[str(ip)] = [(int(c), float(s), (b[0] / wd, b[1] / h, b[2] / wd, b[3] / h))
                            for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
            if i % 100 == 0:
                print("  ", i, "/", len(items), flush=True)
        cache[key] = out
        pickle.dump(cache, open(CACHE, "wb"))
    return cache


def score(items, dets, conf, rider):
    n = {True: 0, False: 0}; said_bare = {True: 0, False: 0}; said_help = {True: 0, False: 0}; miss = {True: 0, False: 0}
    for ip, gts in items:
        ds = [(c, b) for c, s, b in dets[str(ip)] if s >= conf]
        for bare, g in gts:
            if rider:
                cl = [c for c, (a1, b1, a2, b2) in ds
                      if g[0] <= (a1 + a2) / 2 <= g[2] and g[1] <= (b1 + b2) / 2 <= g[1] + 0.6 * (g[3] - g[1])]
                sb = 1 in cl; sh = (0 in cl) and not sb
            else:
                best = None
                for (c, s, b) in [(c, s, b) for c, s, b in dets[str(ip)] if s >= conf]:
                    if iou(g, b) >= 0.3 and (best is None or s > best[1]):
                        best = (c, s)
                sb = best is not None and best[0] == 1; sh = best is not None and best[0] == 0
            n[bare] += 1
            if sb: said_bare[bare] += 1
            elif sh: said_help[bare] += 1
            else: miss[bare] += 1
    return n, said_bare, said_help, miss


def report(label, items, cache, rider):
    nb = sum(1 for _, g in items for b, _ in g if b); nh = sum(1 for _, g in items for b, _ in g if not b)
    print(f"\n{label}: {len(items)} images, {nb} bare heads/riders, {nh} helmeted")
    print(f"  {'model':5} {'conf':>5} {'bare caught':>12} {'bare->helmet':>13} {'bare missed':>12} | {'helmet->bare (false alarm)':>27} {'helmet missed':>14}")
    for conf in (0.25, 0.40, 0.55):
        for mname in ("old", "new"):
            n, sb, sh, ms = score(items, cache[(mname, label)], conf, rider)
            print(f"  {mname:5} {conf:5.2f} {sb[True] / max(n[True], 1):11.0%} {sh[True] / max(n[True], 1):12.0%} {ms[True] / max(n[True], 1):11.0%} | "
                  f"{sb[False] / max(n[False], 1):26.0%} {ms[False] / max(n[False], 1):13.0%}")


if __name__ == "__main__":
    if "--uit-check" in sys.argv:
        from ultralytics import YOLO
        m = YOLO(str(MODELS["old"]))
        items = []
        for sp in ("valid", "test"):
            items += yolo_items(K / "uit_helmet_v8" / sp / "images", K / "uit_helmet_v8" / sp / "labels", {"0"}, {"1"})
        tab = {}
        for ip, gts in items[:200]:
            img = cv2.imread(str(ip))
            r = m.predict(img, imgsz=IMGSZ, conf=0.4, verbose=False)[0]
            dets = [(int(c), tuple(b)) for b, c in zip(r.boxes.xyxyn.tolist(), r.boxes.cls.tolist())]
            for isb, g in gts:
                best = max(((iou(g, b), c) for c, b in dets), default=(0, None))
                if best[0] >= 0.3:
                    k = ("uit class " + ("1" if isb else "0"), "model " + ("no_helmet" if best[1] == 1 else "helmet"))
                    tab[k] = tab.get(k, 0) + 1
        for k, v in sorted(tab.items()):
            print(k, v)
        sys.exit()
    sets = load_sets()
    sets.pop("bikes_helmets_voc (heads)")      # BikesHelmets photos are part of master_traffic_violation (47 were trained on): not held out
    mp = sets.pop("mp_final helmet_no_helmet (heads)")
    sets["helmet_violations_roboflow (riders)"] = violations_items()
    sets["mp_final helmet_no_helmet (heads)"] = mp
    for label, items in sets.items():
        items = list(items)
        random.shuffle(items)
        items = items[:N_PER_SET]
        sets[label] = items
        print(label, len(items), flush=True)
    for label, items in sets.items():
        cache = detect(items, label)
    for label, items in sets.items():
        report(label, items, cache, rider="riders" in label)
