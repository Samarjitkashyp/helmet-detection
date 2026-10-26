"""Extract every frame of the test/validation clips from each finished part_N.zip into data_helmet_myanmar/clips
(used by eval_pipeline.py / eval_cls.py and for the looping test video).  Usage: python -I training/extract_test_clips.py"""
import collections
import csv
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_helmet_myanmar"
CLIPS = DATA / "clips"
split = {r["video_id"]: r["Set"] for r in csv.DictReader(open(DATA / "data_split.csv", encoding="utf-8-sig"))}
added = collections.Counter()
for zpath in sorted(DATA.glob("part_*.zip")):
    try:
        z = zipfile.ZipFile(zpath)
    except zipfile.BadZipFile:
        continue
    for n in z.namelist():
        m = re.fullmatch(r"part_\d+/(\w+_\d+)/(\d+)\.jpg", n)
        if not m or split.get(m.group(1)) not in ("test", "validation"):
            continue
        out = CLIPS / m.group(1) / f"{int(m.group(2))}.jpg"
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(n))
            added[m.group(1)] += 1
print(len(added), "clips added,", sum(added.values()), "frames", flush=True)
