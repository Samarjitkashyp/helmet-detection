"""Does the head-crop classifier fix the detector's cap/hat-as-helmet mistakes? Scores several ways of combining
the two on the Myanmar test/validation clips (uses training/_exp/pipeline_cache.pkl from eval_pipeline.py).

Usage: python -I training/eval_cls.py
"""
import pickle
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))
import eval_pipeline as ep

gt, cache = ep.load_gt_and_update_cache()
print(len({k[0] for k in cache}), "test clips,", len(cache), "frames", flush=True)
cls_model = YOLO(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "backend" / "models" / "head_cls.pt"))
names = cls_model.names
NO = [k for k, v in names.items() if v == "no_helmet"][0]
print("classifier classes:", names, flush=True)


def crop_of(img, b):
    x1, y1, x2, y2 = (int(v) for v in b)
    m = int(0.15 * max(x2 - x1, y2 - y1))
    return img[max(0, y1 - m):y2 + m, max(0, x1 - m):x2 + m]


# p(no_helmet) for every head the pipeline keeps, per frame
probs = {}
for (clip, f), e in cache.items():
    heads = ep.heads_for(e, "crops_sane")
    if not heads:
        probs[(clip, f)] = []
        continue
    img = cv2.imread(str(ep.frame_path(clip, f)))
    crops = [crop_of(img, d[2]) for d in heads]
    ok = [i for i, c in enumerate(crops) if c.size]
    res = cls_model.predict([crops[i] for i in ok], imgsz=96, verbose=False) if ok else []
    p = [None] * len(heads)
    for i, r in zip(ok, res):
        p[i] = float(r.probs.data[NO])
    probs[(clip, f)] = list(zip(heads, p))
print("classified", flush=True)


def make(rule):
    def fn(entry_key):
        out = []
        for (c, s, b), p in probs[entry_key]:
            if p is None:
                out.append((c, s, b)); continue
            out.append(rule(c, s, b, p))
        return out
    return fn


rules = {
    "detector only": lambda c, s, b, p: (c, s, b),
    "classifier only": lambda c, s, b, p: (1 if p >= 0.5 else 0, max(p, 1 - p), b),
}
for t in (0.5, 0.7, 0.85):
    rules[f"flip helmet->no_helmet if cls>={t}"] = lambda c, s, b, p, t=t: (1, p, b) if (c == 0 and p >= t) else (c, s, b)
    rules[f"...and no_helmet->helmet if cls<={1 - t:.2f}"] = (
        lambda c, s, b, p, t=t: (1, p, b) if (c == 0 and p >= t) else ((0, 1 - p, b) if (c == 1 and p <= 1 - t) else (c, s, b)))

orig = ep.heads_for
for name, rule in rules.items():
    fn = make(rule)
    ep.heads_for = lambda entry, mode, fn=fn: fn(next(k for k, v in cache.items() if v is entry))
    print(f"{name:42}", end=" ", flush=True)
    ep.score(gt, cache, "x", 0.5)
