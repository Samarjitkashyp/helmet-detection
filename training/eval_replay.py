"""Fast sweeps of the worker's decision logic (tracking, confirmation, repeat filter) on recorded detections.

Pass 1 (slow, once): run the models on frames of the busiest test clips and cache vehicles + heads.
Pass 2 (seconds): replay the cache through FrameAnalyzer.decide() with many settings and score each against the
per-motorcycle ground truth:  covered = share of bare-headed people that got an alert (alerts capped at one per person),
repeats = alerts beyond the number of bare-headed people, false = alerts on fully helmeted bikes.

Usage: python -I training/eval_replay.py            (builds the cache if missing, then sweeps)
"""
import argparse
import collections
import csv
import io
import itertools
import pickle
import re
import sys
import time
import zipfile
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "training"))
import eval_pipeline as ep
from services.cctv_worker import FrameAnalyzer, SimpleTracker

PERSON = re.compile(r"(D|P\d)(NoHelmet|Helmet)")
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "base"      # base | fast | fastnocrops
VARIANTS = {"base": dict(imgsz=960, vehicle_imgsz=960, crop_imgsz=640, no_crops=False),
            "fast": dict(imgsz=768, vehicle_imgsz=640, crop_imgsz=512, no_crops=False),
            "fastnocrops": dict(imgsz=768, vehicle_imgsz=640, crop_imgsz=512, no_crops=True),
            "adaptive": dict(imgsz=768, vehicle_imgsz=640, crop_imgsz=512, no_crops=False, adaptive_crops=True)}
CACHE = ROOT / "training" / "_exp" / ("replay_cache.pkl" if VARIANT == "base" else f"replay_cache_{VARIANT}.pkl")
N_CLIPS, SRC_STEP = 14, 5          # source frames between cached frames (10 fps video -> 0.5 s)
ann = zipfile.ZipFile(ep.DATA / "annotation.zip")


def gt_rows(clip):
    rows = list(csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace"))))
    boxes = collections.defaultdict(list)
    labels = collections.defaultdict(collections.Counter)
    per_frame = collections.Counter()
    for r in rows:
        people = PERSON.findall(r["label"])
        x, y, w, h = (int(float(r[k])) for k in ("x", "y", "w", "h"))
        boxes[int(r["frame_id"])].append(((x, y, x + w, y + h), any(s == "NoHelmet" for _, s in people)))
        labels[r["track_id"]][r["label"]] += 1
        per_frame[r["frame_id"]] += len(people)
    bad = sum(sum(1 for _, s in PERSON.findall(c.most_common(1)[0][0]) if s == "NoHelmet") for c in labels.values())
    return boxes, bad, max(per_frame.values(), default=0)


def judge(box, boxes):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hit = [bad for (x1, y1, x2, y2), bad in boxes if x1 <= cx <= x2 and y1 <= cy <= y2]
    return "out" if not hit else ("tp" if any(hit) else "fa")


cached = sorted({k[0] for k in pickle.load(open(ep.CACHE, "rb"))})
clips = sorted(cached, key=lambda c: -gt_rows(c)[2])[:N_CLIPS]

if CACHE.exists():
    det = pickle.load(open(CACHE, "rb"))
else:
    base = argparse.Namespace(conf=0.5, no_classifier=False, cls_threshold=0.85, all_heads=False, min_box=16, min_hits=2,
                              single_conf=0.55, tracker="simple", tracker_gate=1.5, **VARIANTS[VARIANT])
    an = FrameAnalyzer(base)
    det = {}
    t_det, n_det = 0.0, 0
    for clip in clips:
        for f in range(1, 101, SRC_STEP):
            p = ep.frame_path(clip, f)
            if p:
                t0 = time.time()
                det[(clip, f)] = an.detect(cv2.imread(str(p)))
                t_det += time.time() - t0; n_det += 1
        print("cached", clip, flush=True)
    pickle.dump(det, open(CACHE, "wb"))
    print(f"detect speed: {t_det / n_det:.2f} s per frame ({VARIANT})", flush=True)


def run(step, **kw):
    cfg = dict(min_box=16, min_hits=2, single_conf=0.65, tracker="simple", tracker_gate=1.5, dedup_dist=2.5, dedup_gap=6)
    cfg.update(kw)
    args = argparse.Namespace(**cfg)
    tot = collections.Counter()
    for clip in clips:
        an = FrameAnalyzer.__new__(FrameAnalyzer)           # decision logic only: no models needed
        an.args, an.vmodel, an.cmodel = args, True, None
        an.tracker = SimpleTracker(gate=args.tracker_gate)
        an.recent, an.stats, an.alerts, an.alerts_sent, an.frame_no, an.memory = [], {}, 0, 0, 0, {}
        boxes, bad, _ = gt_rows(clip)
        sim = {"t": 0.0}
        an.clock = lambda: sim["t"]
        sent = 0
        for f in range(1, 101, step):
            if (clip, f) not in det:
                continue
            sim["t"] = f / 10.0
            _, fresh = an.decide(None, *det[(clip, f)])
            sent += len(fresh)
            for b, _, _ in fresh:
                tot[judge(b, boxes.get(f, []))] += 1
        tot.update(bad=bad, sent=sent, covered=min(bad, sent), repeats=max(0, sent - bad))
    return tot


def show(label, step, **kw):
    t = run(step, **kw)
    fa = t["fa"] / max(1, t["tp"] + t["fa"])
    print(f"{label:46} sent {t['sent']:4}  covered {t['covered'] / t['bad']:4.0%}  repeats {t['repeats']:3}  "
          f"on helmeted bikes {t['fa']:2} ({fa:.0%})", flush=True)


if __name__ == "__main__":
    print("variant:", VARIANT, flush=True)
    for step in (10, 5):
        print(f"--- analysed every {step} source frames ({step / 10:.1f} s apart), {len(clips)} clips, GT bare-headed people {sum(gt_rows(c)[1] for c in clips)}")
        show("no repeat filter", step, dedup_dist=0.0)
        show("worker defaults (dist 1.2, gap 3, single 0.55)", step, single_conf=0.55, dedup_dist=1.2, dedup_gap=3)
    print("DONE", flush=True)


