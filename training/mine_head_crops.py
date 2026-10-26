"""Mine labelled head crops from the Myanmar HELMET training clips, to teach a second-stage classifier
what CCTV helmets / caps / bare heads look like (the main model confuses caps and hats with helmets here).

Ground truth is per motorcycle, not per head. A detected head inside a motorcycle box gets the bike's label
only when every person on that bike agrees (all Helmet -> helmet, all NoHelmet -> no_helmet); mixed bikes and
heads inside two motorcycle boxes are skipped. Only the 'training' split is used, so the test/validation
clips used by eval_pipeline.py stay unseen.

Usage: python -I training/mine_head_crops.py        -> training/_exp/headcls/{train,val}/{helmet,no_helmet}/*.jpg
"""
import collections
import csv
import io
import re
import zipfile
from pathlib import Path, PurePosixPath

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_helmet_myanmar"
CLIPS = DATA / "clips_train"
OUT = ROOT / "training" / "_exp" / "headcls"
FT = ROOT / "training" / "_exp" / "finetune_cctv"   # YOLO frames + labels (detector fine-tuning set)
PERSON = re.compile(r"(D|P\d)(NoHelmet|Helmet)")
STEP = 3
HOLDOUT_EVERY = 5     # every 5th clip becomes the classifier's validation set

split = {r["video_id"]: r["Set"] for r in csv.DictReader(open(DATA / "data_split.csv", encoding="utf-8-sig"))}
DONE_FILE = OUT / "mined_clips.txt"
OUT.mkdir(parents=True, exist_ok=True)
already = set(DONE_FILE.read_text().split()) if DONE_FILE.exists() else set()

# every finished part_N.zip (osf_fetch.py only creates the zip once the download is complete)
want = []          # (clip, zip, {frame: zip member name})
for zpath in sorted(DATA.glob("part_*.zip")):
    try:
        part = zipfile.ZipFile(zpath)
    except zipfile.BadZipFile:
        continue
    members = collections.defaultdict(dict)
    for n in part.namelist():
        m = re.fullmatch(r"part_\d+/(\w+_\d+)/(\d+)\.jpg", n)
        if m and split.get(m.group(1)) == "training":
            members[m.group(1)][int(m.group(2))] = n
    for clip in sorted(members):
        if clip not in already:
            want.append((clip, part, members[clip]))
print(len(want), "new training clips to mine", flush=True)

ann = zipfile.ZipFile(DATA / "annotation.zip")
head = YOLO(str(ROOT / "backend" / "models" / "best.pt"))
counts = collections.Counter()
for clip, part, frames in want:
    subset = "val" if int(re.sub(r"\D", "", clip)) % HOLDOUT_EVERY == 0 else "train"   # stable per clip, whatever the order
    for f in range(1, 101, STEP):
        if f in frames:
            out = CLIPS / clip / f"{f}.jpg"
            if not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(part.read(frames[f]))
    gt = collections.defaultdict(list)
    for r in csv.DictReader(io.StringIO(ann.read(f"annotation/{clip}.csv").decode("utf-8", "replace"))):
        people = PERSON.findall(r["label"])
        if not people:
            continue
        states = {s for _, s in people}
        label = "helmet" if states == {"Helmet"} else "no_helmet" if states == {"NoHelmet"} else None
        x, y, w, h = (int(float(r[k])) for k in ("x", "y", "w", "h"))
        gt[int(r["frame_id"])].append(((x, y, x + w, y + h), label))
    for f in range(1, 101, STEP):
        p = CLIPS / clip / f"{f}.jpg"
        if not p.exists() or f not in gt:
            continue
        img = cv2.imread(str(p))
        H, W = img.shape[:2]
        res = head.predict(img, imgsz=1280, conf=0.25, verbose=False)[0]
        rows, clean = [], True     # YOLO label rows for the fine-tuning set; clean = no head left unexplained
        for b, dconf in zip(res.boxes.xyxy.tolist(), res.boxes.conf.tolist()):
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            hw, hh = b[2] - b[0], b[3] - b[1]
            if min(hw, hh) < 20:
                continue
            inside = [lab for (x1, y1, x2, y2), lab in gt[f] if x1 <= cx <= x2 and y1 <= cy <= y2]
            if inside and (len(inside) != 1 or inside[0] is None):
                if dconf >= 0.4:
                    clean = False      # a rider we cannot label reliably: do not use this frame for fine-tuning
                continue
            if not inside:
                continue
            rows.append(f"{0 if inside[0] == 'helmet' else 1} {cx / W:.6f} {cy / H:.6f} {hw / W:.6f} {hh / H:.6f}")
            m = int(0.15 * max(hw, hh))
            crop = img[max(0, int(b[1]) - m):int(b[3]) + m, max(0, int(b[0]) - m):int(b[2]) + m]
            d = OUT / subset / inside[0]
            d.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d / f"{clip}_{f}_{int(b[0])}_{int(b[1])}.jpg"), crop)
            counts[(subset, inside[0])] += 1
        if clean and rows:     # whole frame + YOLO labels for the Colab fine-tuning notebook
            (FT / subset / "images").mkdir(parents=True, exist_ok=True)
            (FT / subset / "labels").mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(FT / subset / "images" / f"{clip}_{f}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
            (FT / subset / "labels" / f"{clip}_{f}.txt").write_text("\n".join(rows) + "\n")
            counts["frames"] += 1
    with open(DONE_FILE, "a") as fh:
        fh.write(clip + "\n")
    print("mined", clip, dict(counts), flush=True)
print("DONE", dict(counts), flush=True)
