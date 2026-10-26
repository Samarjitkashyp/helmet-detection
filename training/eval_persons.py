"""Person-level check of the live worker logic (FrameAnalyzer) on test clips with several riders per frame.

The ground truth names every person on a motorcycle (D = driver, P1/P2 = passengers) as Helmet or NoHelmet,
so per clip we can compare: people without helmet in the ground truth  vs  people the analyzer flagged,
and people with helmet vs tracks that were seen only with a helmet. Frames are fed like the live worker sees them
(one frame per `STEP` source frames; 10 = about 1 per second), with the tracker running across them.

Usage: python -I training/eval_persons.py [step] [max_clips]
"""
import argparse
import collections
import csv
import io
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
from services.cctv_worker import FrameAnalyzer

STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 10
MAX_CLIPS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
PERSON = re.compile(r"(D|P\d)(NoHelmet|Helmet)")

args = argparse.Namespace(imgsz=int(sys.argv[5 + 1]) if len(sys.argv) > 6 else 1280, conf=0.5, no_crops=False, crop_imgsz=640, vehicle_imgsz=960, no_classifier=False,
                          cls_threshold=0.85, all_heads=False, min_box=16, min_hits=2,
                          single_conf=float(sys.argv[3]) if len(sys.argv) > 3 else 0.8,
                          tracker=sys.argv[4] if len(sys.argv) > 4 else "simple",
                          tracker_gate=float(sys.argv[5]) if len(sys.argv) > 5 else 3.0)
cache = pickle.load(open(ep.CACHE, "rb"))
cached_clips = sorted({k[0] for k in cache})
ann = zipfile.ZipFile(ep.DATA / "annotation.zip")


def gt_boxes(clip):
    """frame -> [(box, True if somebody on that bike has no helmet)]"""
    out = collections.defaultdict(list)
    for r in csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace"))):
        people = PERSON.findall(r["label"])
        x, y, w, h = (int(float(r[k])) for k in ("x", "y", "w", "h"))
        out[int(r["frame_id"])].append(((x, y, x + w, y + h), any(s == "NoHelmet" for _, s in people)))
    return out


def judge(box, boxes):
    """'tp' = flagged head sits on a bike with a bare-headed person, 'fa' = on a fully helmeted bike, 'out' = on no labelled bike."""
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hit = [bad for (x1, y1, x2, y2), bad in boxes if x1 <= cx <= x2 and y1 <= cy <= y2]
    return "out" if not hit else ("tp" if any(hit) else "fa")


def gt_persons(clip):
    """(people without helmet, people with helmet, most riders visible at once) from the per-bike labels."""
    labels = collections.defaultdict(collections.Counter)
    per_frame = collections.Counter()
    for r in csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace"))):
        labels[r["track_id"]][r["label"]] += 1
        per_frame[r["frame_id"]] += len(PERSON.findall(r["label"]))
    bad = good = 0
    for c in labels.values():
        people = PERSON.findall(c.most_common(1)[0][0])
        bad += sum(1 for _, s in people if s == "NoHelmet")
        good += sum(1 for _, s in people if s == "Helmet")
    return bad, good, max(per_frame.values(), default=0)


# the clips with the most people in view (those are the crowded, multi-person cases)
ranked = sorted(cached_clips, key=lambda c: -gt_persons(c)[2])[:MAX_CLIPS]
tot = collections.Counter()
print(f"{'clip':22} {'GT no-helmet':>12} {'sent':>6} {'flagged':>8} {'GT helmet':>10} {'helmet-only tracks':>19} {'max riders in view':>19}", flush=True)
for clip in ranked:
    an = FrameAnalyzer(args)
    max_view = 0
    boxes = gt_boxes(clip)
    for f in range(1, 101, STEP):
        p = ep.frame_path(clip, f)
        if p is None:
            continue
        t0 = time.time()
        shown, fresh = an.analyze(cv2.imread(str(p)))
        tot["secs"] += time.time() - t0
        tot["frames"] += 1
        max_view = max(max_view, len(shown))
        for b, _, _ in fresh:
            tot[judge(b, boxes.get(f, []))] += 1
    flagged = sum(1 for s in an.stats.values() if s["alerted"])
    helmet_only = sum(1 for s in an.stats.values() if not s["alerted"] and s["ok"] >= 2 and s["bad"] == 0)
    bad, good, _ = gt_persons(clip)
    print(f"{clip:22} {bad:>12} {an.alerts_sent:>6} {flagged:>8} {good:>10} {helmet_only:>19} {max_view:>19}", flush=True)
    tot.update(bad=bad, flagged=flagged, good=good, helmet_only=helmet_only, sent=an.alerts_sent, capped=min(bad, an.alerts_sent), excess=max(0, an.alerts_sent - bad))
print(f"TOTAL: GT no-helmet {tot['bad']}, flagged {tot['flagged']}; GT helmet {tot['good']}, helmet-only tracks {tot['helmet_only']}", flush=True)
print(f"alerts sent {tot['sent']} for {tot['bad']} bare-headed people: at least {tot['capped'] / tot['bad']:.0%} covered, {tot['excess']} alerts beyond the number of people (repeats)", flush=True)
print(f"speed: {tot['secs'] / max(1, tot['frames']):.2f} s per analysed frame (while other jobs share the CPU)", flush=True)
alerts = tot["tp"] + tot["fa"] + tot["out"]
print(f"ALERTS {alerts}: on a bike with a bare-headed rider {tot['tp']}, on a fully helmeted bike (false alarm) {tot['fa']}, "
      f"outside labelled bikes {tot['out']};  false alarms {tot['fa'] / max(1, tot['tp'] + tot['fa']):.0%} of judged alerts", flush=True)
print("DONE", flush=True)

