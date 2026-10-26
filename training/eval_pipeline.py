"""Compare CCTV detection pipelines on the Myanmar HELMET clips (extracted by eval_cctv.py).

Detections are computed once per frame and cached (training/_exp/pipeline_cache.pkl), then several
ways of turning them into "this rider has no helmet" are scored against the per-motorcycle ground truth:

  full    helmet model on the whole frame (what the worker did first)
  rider   full + only heads that belong to a motorcycle (COCO vehicle model; cyclists/pedestrians dropped)
  crops   rider + the helmet model also run on an enlarged crop around every motorcycle (heads get bigger)

A GT motorcycle is a violation if any person on it has no helmet. It is "caught" when a no_helmet head whose
centre lies in its box is found in >= MIN_FRAMES sampled frames. "stray" = flagged heads that are not inside
any GT motorcycle (pedestrians, cyclists, unlabelled bikes): in the live worker these would be false alarms
unless they really are riders without helmet that the dataset did not label.

Usage: python -I training/eval_pipeline.py
"""
import collections
import csv
import io
import os
import pickle
import re
import sys
import time
import zipfile
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
DATA = ROOT / "data_helmet_myanmar"
CLIPS = DATA / "clips"
CACHE = ROOT / "training" / "_exp" / "pipeline_cache.pkl"
PERSON = re.compile(r"(D|P\d)(NoHelmet|Helmet)")
CONF, MIN_FRAMES, STEP = 0.4, 2, 2
NO_HELMET = 1
BICYCLE, MOTORCYCLE = 1, 3


def frame_path(clip, f):
    for name in (f"{f}.jpg", f"{f:02d}.jpg"):
        p = CLIPS / clip / name
        if p.exists():
            return p
    return None


def load_gt():
    ann = zipfile.ZipFile(DATA / "annotation.zip")
    gt = {}
    for clip in sorted(p.name for p in CLIPS.iterdir() if p.is_dir()):
        frames = collections.defaultdict(list)
        rows = csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace")))
        for r in rows:
            people = PERSON.findall(r["label"])
            x, y, w, h = (int(float(r[k])) for k in ("x", "y", "w", "h"))
            frames[int(r["frame_id"])].append((r["track_id"], (x, y, x + w, y + h),
                                               any(s == "NoHelmet" for _, s in people)))
        gt[clip] = frames
    return gt


def load_gt_and_update_cache():
    """For eval_cls.py: ground truth of all extracted test clips and a cache that covers them all."""
    gt = load_gt()
    cache = pickle.load(open(CACHE, "rb")) if CACHE.exists() else {}
    if cache and not os.environ.get("EXPAND_EVAL"):
        gt = {c: v for c, v in gt.items() if c in {k[0] for k in cache}}   # keep one fixed test set so runs stay comparable
    elif {c for c in gt} - {k[0] for k in cache}:
        cache = compute_cache(gt, cache)    # slow: ~2 s per frame on CPU, 50 frames per new clip
        pickle.dump(cache, open(CACHE, "wb"))
    return gt, cache


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def nms(dets, thr=0.5):
    keep = []
    for d in sorted(dets, key=lambda d: -d[1]):
        if all(iou(d[2], k[2]) < thr for k in keep):
            keep.append(d)
    return keep


def crop_region(box, w, h):
    bw, bh = box[2] - box[0], box[3] - box[1]
    return (max(0, int(box[0] - 0.5 * bw)), max(0, int(box[1] - 2.5 * bh)),
            min(w, int(box[2] + 0.5 * bw)), min(h, int(box[3] + 0.3 * bh)))


def compute_cache(gt, cache=None):
    """Adds detections for every GT clip that is not cached yet (so new test clips cost only their own time)."""
    head = YOLO(str(ROOT / "backend" / "models" / "best.pt"))
    veh = YOLO(str(ROOT / "backend" / "models" / "coco_yolov8s.pt"))
    cache = cache if cache is not None else {}
    done = {k[0] for k in cache}
    for clip in gt:
        if clip in done:
            continue
        for f in range(1, 101, STEP):
            p = frame_path(clip, f)
            if p is None or f not in gt[clip]:
                continue
            img = cv2.imread(str(p))
            h, w = img.shape[:2]
            r = head.predict(img, imgsz=1280, conf=CONF, verbose=False)[0]
            full = [(int(c), float(s), tuple(b)) for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
            v = veh.predict(img, imgsz=960, conf=0.25, classes=[BICYCLE, MOTORCYCLE], verbose=False)[0]
            vehicles = [(int(c), tuple(b)) for b, c in zip(v.boxes.xyxy.tolist(), v.boxes.cls.tolist())]
            crops = []
            for cls, box in vehicles:
                if cls != MOTORCYCLE:
                    continue
                x1, y1, x2, y2 = crop_region(box, w, h)
                if x2 - x1 < 20 or y2 - y1 < 20:
                    continue
                cr = head.predict(img[y1:y2, x1:x2], imgsz=640, conf=CONF, verbose=False)[0]
                for b, c, s in zip(cr.boxes.xyxy.tolist(), cr.boxes.cls.tolist(), cr.boxes.conf.tolist()):
                    crops.append((int(c), float(s), (b[0] + x1, b[1] + y1, b[2] + x1, b[3] + y1)))
            cache[(clip, f)] = {"full": full, "vehicles": vehicles, "crops": crops}
        print("cached", clip, flush=True)
    CACHE.parent.mkdir(exist_ok=True)
    pickle.dump(cache, open(CACHE, "wb"))
    return cache


def nearest_vehicle(head, vehicles):
    cx, cy = (head[0] + head[2]) / 2, (head[1] + head[3]) / 2
    best, best_d = None, None
    for cls, (vx1, vy1, vx2, vy2) in vehicles:
        bw, bh = max(vx2 - vx1, 1), max(vy2 - vy1, 1)
        if not (vx1 - 0.25 * bw <= cx <= vx2 + 0.25 * bw and vy1 - 2.2 * bh <= cy <= vy1 + 0.6 * bh):
            continue
        d = (((cx - (vx1 + vx2) / 2) / bw) ** 2 + ((cy - vy1) / bh) ** 2) ** 0.5
        if best_d is None or d < best_d:
            best, best_d = cls, d
    return best


def sane(head, vehicles):
    """A rider's head is small next to its motorcycle and roughly as wide as tall. Enlarged crops of far
    bikes sometimes make the model box a whole rider+bike as one giant 'head'; those are rejected."""
    cx, cy = (head[0] + head[2]) / 2, (head[1] + head[3]) / 2
    hw, hh = head[2] - head[0], head[3] - head[1]
    best, best_d = None, None
    for cls, v in vehicles:
        bw, bh = max(v[2] - v[0], 1), max(v[3] - v[1], 1)
        if not (v[0] - 0.25 * bw <= cx <= v[2] + 0.25 * bw and v[1] - 2.2 * bh <= cy <= v[1] + 0.6 * bh):
            continue
        d = (((cx - (v[0] + v[2]) / 2) / bw) ** 2 + ((cy - v[1]) / bh) ** 2) ** 0.5
        if best_d is None or d < best_d:
            best, best_d = (cls, v), d
    if best is None or best[0] != MOTORCYCLE:
        return False
    _, v = best
    return hh <= SANE_H * (v[3] - v[1]) and hw <= SANE_W * (v[2] - v[0]) and 0.6 <= hh / max(hw, 1) <= 2.2


SANE_H, SANE_W = 0.75, 0.8


def heads_for(entry, mode):
    if mode == "crops_sane":
        merged = nms(entry["full"] + entry["crops"])
        return [d for d in merged if sane(d[2], entry["vehicles"])]
    if mode == "rider_sane":
        return [d for d in entry["full"] if sane(d[2], entry["vehicles"])]
    if mode == "full":
        return entry["full"]
    if mode == "rider":
        return [d for d in entry["full"] if nearest_vehicle(d[2], entry["vehicles"]) == MOTORCYCLE]
    if mode == "crops":
        merged = nms(entry["full"] + entry["crops"])
        return [d for d in merged if nearest_vehicle(d[2], entry["vehicles"]) == MOTORCYCLE]
    raise ValueError(mode)


def score(gt, cache, mode, conf=CONF):
    per_track = collections.defaultdict(lambda: {"viol": False, "frames": 0, "flag": 0})
    stray = 0
    for (clip, f), entry in cache.items():
        dets = [d for d in heads_for(entry, mode) if d[1] >= conf]
        inside_any = set()
        for track, (x1, y1, x2, y2), viol in gt[clip][f]:
            t = per_track[(clip, track)]
            t["viol"] = t["viol"] or viol
            t["frames"] += 1
            hit = False
            for c, s, b in dets:
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    inside_any.add(id(b))
                    hit = hit or c == NO_HELMET
            t["flag"] += hit
        stray += sum(1 for c, s, b in dets if c == NO_HELMET and id(b) not in inside_any)
    tp = fp = fn = tn = 0
    for t in per_track.values():
        if t["frames"] < 3:
            continue
        pred = t["flag"] >= MIN_FRAMES
        if t["viol"] and pred: tp += 1
        elif t["viol"]: fn += 1
        elif pred: fp += 1
        else: tn += 1
    print(f"{mode:6} conf>={conf:.2f}: caught {tp}/{tp + fn} (recall {tp / max(1, tp + fn):.2f})  "
          f"false alarms on compliant bikes {fp}/{fp + tn}  precision {tp / max(1, tp + fp):.2f}  "
          f"stray no_helmet heads outside GT bikes: {stray}", flush=True)


if __name__ == "__main__":
    gt = load_gt()
    cache = pickle.load(open(CACHE, "rb")) if CACHE.exists() else {}
    if {c for c in gt} - {k[0] for k in cache}:
        t0 = time.time()
        cache = compute_cache(gt, cache)
        print(f"cache updated in {time.time() - t0:.0f}s", flush=True)
    print(f"{len(cache)} frames", flush=True)
    for mode in ("rider", "rider_sane", "crops", "crops_sane"):
        for conf in (0.4, 0.5, 0.6):
            score(gt, cache, mode, conf)
    for sh, sw in ((0.6, 0.7), (0.5, 0.6), (0.4, 0.5)):
        SANE_H, SANE_W = sh, sw
        print(f"sane limits height<={sh} width<={sw}", flush=True)
        score(gt, cache, "crops_sane", 0.5)
    print("DONE", flush=True)
