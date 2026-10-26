"""How well does our model do on CCTV-style footage? Uses the Myanmar HELMET dataset (CC BY 4.0).

Ground truth is per motorcycle (a box around bike + riders) with a label such as DNoHelmetP1Helmet
(D = driver, P1/P2 = passengers). A bike counts as a VIOLATION if any person on it has no helmet.
Our model finds heads; a head detection whose centre lies inside a bike box is attributed to that bike.

Usage: python -I training/eval_cctv.py [imgsz ...]     (default: 640 960 1280)
Needs data_helmet_myanmar/{part_7.zip, annotation.zip, data_split.csv}.
"""
import collections
import csv
import io
import re
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_helmet_myanmar"
CLIPS = DATA / "clips"
CONF = 0.4
FRAME_STEP = 2          # use every 2nd frame (CPU time)
MIN_FRAMES = 2          # a bike must be flagged in this many sampled frames
SPLITS = {"test", "validation"}
PERSON = re.compile(r"(D|P\d)(NoHelmet|Helmet)")

split = {r["video_id"]: r["Set"] for r in csv.DictReader(open(DATA / "data_split.csv", encoding="utf-8-sig"))}

# 1) extract only the clips we evaluate (names are checked: only <clip>/<n>.jpg)
part = zipfile.ZipFile(DATA / "part_7.zip")
want = sorted({PurePosixPath(n).parent.name for n in part.namelist() if n.endswith(".jpg")
               if split.get(PurePosixPath(n).parent.name) in SPLITS})
for n in part.namelist():
    m = re.fullmatch(r"part_7/(Yangon_II_\d+)/(\d+)\.jpg", n)
    if m and m.group(1) in want:
        out = CLIPS / m.group(1) / f"{m.group(2)}.jpg"
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(part.read(n))
print(f"{len(want)} clips ({collections.Counter(split[c] for c in want)}) extracted to {CLIPS}", flush=True)

# 2) ground truth
ann = zipfile.ZipFile(DATA / "annotation.zip")
gt = {}   # clip -> frame -> [(track, (x1,y1,x2,y2), violation)]
for clip in want:
    rows = csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace")))
    frames = collections.defaultdict(list)
    for r in rows:
        people = PERSON.findall(r["label"])
        x, y, w, h = (int(float(r[k])) for k in ("x", "y", "w", "h"))
        frames[int(r["frame_id"])].append((r["track_id"], (x, y, x + w, y + h), any(s == "NoHelmet" for _, s in people)))
    gt[clip] = frames

model = YOLO(str(ROOT / "backend" / "models" / "best.pt"))


def evaluate(imgsz):
    per_track = collections.defaultdict(lambda: {"viol": False, "frames": 0, "flag": 0, "head": 0})
    t0, n = time.time(), 0
    for clip in want:
        for f in range(1, 101, FRAME_STEP):
            path = CLIPS / clip / f"{f}.jpg"
            if not path.exists() or f not in gt[clip]:
                continue
            res = model.predict(str(path), imgsz=imgsz, conf=CONF, verbose=False)[0]
            dets = [(int(c), ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)) for b, c in zip(res.boxes.xyxy.tolist(), res.boxes.cls.tolist())]
            n += 1
            for track, (x1, y1, x2, y2), viol in gt[clip][f]:
                inside = [c for c, (cx, cy) in dets if x1 <= cx <= x2 and y1 <= cy <= y2]
                t = per_track[(clip, track)]
                t["viol"] = t["viol"] or viol
                t["frames"] += 1
                t["head"] += bool(inside)
                t["flag"] += 1 in inside
    tp = fp = fn = tn = 0
    found_head = tot = 0
    for t in per_track.values():
        if t["frames"] < 3:
            continue
        tot += 1
        found_head += t["head"] >= MIN_FRAMES
        pred = t["flag"] >= MIN_FRAMES
        if t["viol"] and pred: tp += 1
        elif t["viol"]: fn += 1
        elif pred: fp += 1
        else: tn += 1
    prec = tp / max(1, tp + fp); rec = tp / max(1, tp + fn)
    print(f"imgsz {imgsz:4}: bikes={tot}  violations caught {tp}/{tp + fn} (recall {rec:.2f})  false alarms {fp}  "
          f"precision {prec:.2f}  | bikes with any head found {found_head}/{tot}  | {1000 * (time.time() - t0) / max(1, n):.0f} ms/frame", flush=True)


for s in [int(a) for a in sys.argv[1:]] or [640, 960, 1280]:
    evaluate(s)
print("DONE", flush=True)
