"""Compare tracker settings on one video: how many distinct 'people' (tracks) come out?

Usage: python -I training/tracker_experiment.py VIDEO WORKDIR [A B C ...]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import ultralytics
from ultralytics import YOLO

VIDEO = sys.argv[1]
MODEL = str(Path(__file__).resolve().parents[1] / "backend" / "models" / "best.pt")
CFG = Path(ultralytics.__file__).parent / "cfg" / "trackers"
WORK = Path(sys.argv[2]).resolve()
WORK.mkdir(parents=True, exist_ok=True)


def make_yaml(base: str, name: str, **over) -> str:
    text = (CFG / base).read_text()
    for k, v in over.items():
        text, n = re.subn(rf"^{k}:.*$", f"{k}: {v}", text, flags=re.M)
        assert n == 1, (k, n)
    p = WORK / name
    p.write_text(text)
    return str(p)


def run(tracker: str, skip: int, conf: float = 0.4, min_box: int = 60, min_hits: int = 3):
    model = YOLO(MODEL)
    cap = cv2.VideoCapture(VIDEO)
    tracks = defaultdict(lambda: {"hits": 0, "score": defaultdict(float)})
    idx = -1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        if idx % skip:
            continue
        r = model.track(frame, persist=True, conf=conf, imgsz=640, tracker=tracker, verbose=False)[0]
        if r.boxes is None or r.boxes.id is None:
            continue
        for box, tid, cls, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(),
                                    r.boxes.cls.int().tolist(), r.boxes.conf.tolist()):
            if box[3] - box[1] < min_box:
                continue
            tracks[tid]["hits"] += 1
            tracks[tid]["score"][model.names[cls]] += c
    cap.release()
    kept = {k: v for k, v in tracks.items() if v["hits"] >= min_hits}
    verdict = [max(v["score"], key=v["score"].get) for v in kept.values()]
    return len(tracks), len(kept), verdict.count("no_helmet"), verdict.count("helmet")


configs = {
    "A": ("bytetrack skip4 (live setup)", "bytetrack.yaml", 4),
    "B": ("bytetrack skip2", "bytetrack.yaml", 2),
    "C": ("botsort+GMC skip4", "botsort.yaml", 4),
    "D": ("botsort skip4 buffer90", make_yaml("botsort.yaml", "bot90_a.yaml", track_buffer=90), 4),
    "E": ("botsort skip2 buffer90", make_yaml("botsort.yaml", "bot90_b.yaml", track_buffer=90), 2),
}
only = sys.argv[3:]
for key, (label, trk, skip) in configs.items():
    if only and key not in only:
        continue
    total, kept, nohelmet, helmet = run(trk, skip)
    print(f"{key} {label:30} raw_tracks={total:3} kept={kept:2} -> no_helmet={nohelmet} helmet={helmet}", flush=True)
print("DONE", flush=True)
