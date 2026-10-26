"""Builds helmet_finetune_colab.zip for training/finetune_cctv_colab.ipynb:
  cctv/{train,val}/{images,labels}   CCTV frames with labels from the Myanmar ground truth (mine_head_crops.py)
  replay/{images,labels}             general images incl. cap/hat hard negatives (so the model does not forget)
  data.yaml, README.txt
Usage: python -I training/build_finetune_zip.py [replay_images]   -> E:\\helmet_detection\\helmet_finetune_colab.zip
"""
import random
import sys
import zipfile

import cv2
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "training" / "_exp" / "finetune_cctv"
MERGED = ROOT / "data_merged" / "train"
OUT = ROOT / "helmet_finetune_colab.zip"
N_REPLAY = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
random.seed(5)

pairs = []
for lab in (MERGED / "labels").glob("*.txt"):
    img = next((MERGED / "images").glob(lab.stem + ".*"), None)
    if img and lab.read_text().strip():
        pairs.append((img, lab))
hard = [p for p in pairs if p[0].name.startswith("extra_")]
rest = [p for p in pairs if not p[0].name.startswith("extra_")]
random.shuffle(hard); random.shuffle(rest)
replay = hard[:N_REPLAY * 2 // 5] + rest[:N_REPLAY - min(len(hard), N_REPLAY * 2 // 5)]
print(f"replay: {len(replay)} images ({min(len(hard), N_REPLAY * 2 // 5)} cap/hat hard negatives)", flush=True)

CAPS = {"train": 2500, "val": 500}     # Colab's T4 trains ~3000 images per epoch in a few minutes at 960 px


def pick(subset):
    """Frames spread evenly over all clips (every clip counts the same, none dominates)."""
    by_clip = {}
    for img in sorted((FT / subset / "images").glob("*.jpg")):
        by_clip.setdefault(img.stem.rsplit("_", 1)[0], []).append(img)
    per_clip = max(1, -(-CAPS[subset] // max(1, len(by_clip))))
    chosen = []
    for frames in by_clip.values():
        step = max(1, len(frames) // per_clip)
        chosen += frames[::step][:per_clip]
    random.shuffle(chosen)
    print(f"{subset}: {len(chosen[:CAPS[subset]])} of {sum(len(v) for v in by_clip.values())} frames from {len(by_clip)} clips", flush=True)
    return chosen[:CAPS[subset]]


counts = {}
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_STORED) as z:
    for subset in ("train", "val"):
        n = 0
        for img in pick(subset):
            lab = FT / subset / "labels" / (img.stem + ".txt")
            if lab.is_file():
                im = cv2.imread(str(img))
                if im.shape[1] > 1280:     # labels are normalised, so a smaller picture keeps them valid; keeps the zip small
                    im = cv2.resize(im, (1280, round(im.shape[0] * 1280 / im.shape[1])), interpolation=cv2.INTER_AREA)
                z.writestr(f"cctv/{subset}/images/{img.name}", cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 88])[1].tobytes())
                z.write(lab, f"cctv/{subset}/labels/{lab.name}")
                n += 1
        counts[subset] = n
    for img, lab in replay:
        z.write(img, f"replay/images/{img.name}")
        z.write(lab, f"replay/labels/{lab.name}")
    z.writestr("data.yaml", "train: [cctv/train/images, replay/images]\nval: cctv/val/images\nnc: 2\nnames: [helmet, no_helmet]\n")
    z.writestr("README.txt",
               "CCTV frames: HELMET dataset of Myanmar traffic cameras (https://osf.io/4pwj8/, CC BY 4.0, please credit its authors); labels derived from its per-motorcycle ground truth.\n"
               "Classes: 0 = helmet, 1 = no_helmet (caps, hats and bare heads are no_helmet).\n"
               "Only heads on motorcycles are labelled; pedestrians and cyclists are left unlabelled on purpose.\n"
               "replay/ = general images from the project's earlier training set.\n")
print("cctv frames:", counts, "->", OUT, f"{OUT.stat().st_size / 1e6:.0f} MB", flush=True)

