"""Merge Roboflow YOLOv8 datasets into one with classes: 0=helmet, 1=no_helmet.

Class ids are translated by class NAME (read from each dataset's data.yaml), so any dataset can be added:
  * put its extracted folder in E:\\helmet_detection\\data_extracted\\ (name it extra_<something> to be auto-included)
  * head coverings that are NOT helmets (cap, hat, turban, hijab, ...) count as 'no_helmet' (hard negatives)
  * classes that are not in NAME_MAP (person, plate, motorcycle, ...) are dropped

Usage: python -I training/merge_datasets.py
"""
import hashlib
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(r"E:\helmet_detection")
SRC = ROOT / "data_extracted"
OUT = ROOT / "data_merged"
CLASSES = ["helmet", "no_helmet"]

HELMET, NO_HELMET = 0, 1
NAME_MAP = {
    # helmets
    "helmet": HELMET, "with helmet": HELMET, "withhelmet": HELMET, "with_helmet": HELMET, "hard hat": HELMET,
    # no helmet
    "no-helmet": NO_HELMET, "no_helmet": NO_HELMET, "no helmet": NO_HELMET, "without helmet": NO_HELMET,
    "withouthelmet": NO_HELMET, "without_helmet": NO_HELMET, "not-wearing-helmet": NO_HELMET,
    # head coverings that are not helmets: hard negatives, a cap must NOT be called a helmet
    "cap": NO_HELMET, "hat": NO_HELMET, "baseball-cap": NO_HELMET, "beanie": NO_HELMET, "beret": NO_HELMET,
    "cowboy-hat": NO_HELMET, "headband": NO_HELMET, "headscarf": NO_HELMET, "hijab": NO_HELMET,
    "hijab_niqab": NO_HELMET, "turban": NO_HELMET, "bare head": NO_HELMET,
    "kepka": NO_HELMET, "character-hat": NO_HELMET,
}
# Per-dataset overrides where the generic names are ambiguous.
OVERRIDES = {
    "hat": {"head": NO_HELMET, "helmet": HELMET},   # YOLOV8 hat detection: head = uncovered head
}

# Roboflow augmentation makes several copies per photo; keep one per original photo.
DEDUP_AUGMENTED = {"plate"}
TRAIN_CAP = {"plate": 6000, "extra_cap": 2000}   # keep hard negatives from swamping the real helmet data
BASE_DATASETS = ["rider", "learning", "plate"]   # `hat` / `nohelmetriders` are opt-in via OVERRIDES / extra_*
SEED = 42


def base_name(stem: str) -> str:
    return re.split(r"\.rf\.|_jpg|_png", stem)[0]


def file_hash(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def class_mapping(name: str) -> dict[int, int]:
    cfg = yaml.safe_load((SRC / name / "data.yaml").read_text())
    names = cfg["names"]
    names = list(names.values()) if isinstance(names, dict) else list(names)
    table = {**NAME_MAP, **OVERRIDES.get(name, {})}
    return {i: table[n.strip().lower()] for i, n in enumerate(names) if n.strip().lower() in table}


def convert_labels(label_path: Path, mapping: dict) -> list[str]:
    out = []
    for line in label_path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 5:  # segmentation polygons / malformed rows are skipped
            continue
        cid = int(parts[0])
        if cid in mapping:
            out.append(" ".join([str(mapping[cid])] + parts[1:]))
    return out


def main():
    rng = random.Random(SEED)
    datasets = list(BASE_DATASETS) + sorted(p.name for p in SRC.glob("extra_*") if (p / "data.yaml").exists())
    mappings = {n: class_mapping(n) for n in datasets}
    for n, m in mappings.items():
        print(f"{n}: class map {m}")

    if OUT.exists():
        shutil.rmtree(OUT)
    for s in ("train", "valid", "test"):
        (OUT / s / "images").mkdir(parents=True)
        (OUT / s / "labels").mkdir(parents=True)

    seen_hashes: set[str] = set()
    stats: dict[tuple, Counter] = {}

    # valid/test first so any cross-dataset duplicate is dropped from train, not from eval
    for split in ("valid", "test", "train"):
        for name in datasets:
            mapping = mappings[name]
            img_dir = SRC / name / split / "images"
            lbl_dir = SRC / name / split / "labels"
            if not img_dir.exists():
                continue
            imgs = sorted(p for p in img_dir.iterdir() if p.is_file())

            if split == "train" and (name in DEDUP_AUGMENTED or name.startswith("extra_")):
                groups = {}
                for p in imgs:
                    groups.setdefault(base_name(p.stem), p)
                imgs = list(groups.values())
            if split == "train" and name in TRAIN_CAP and len(imgs) > TRAIN_CAP[name]:
                imgs = rng.sample(imgs, TRAIN_CAP[name])

            c = Counter()
            for p in imgs:
                lbl = lbl_dir / (p.stem + ".txt")
                if not lbl.exists():
                    c["skipped_no_label"] += 1
                    continue
                lines = convert_labels(lbl, mapping)
                if not lines:
                    c["skipped_no_kept_class"] += 1
                    continue
                h = file_hash(p)
                if h in seen_hashes:
                    c["skipped_duplicate"] += 1
                    continue
                seen_hashes.add(h)
                new_stem = f"{name}_{p.stem}"
                shutil.copy2(p, OUT / split / "images" / (new_stem + p.suffix))
                (OUT / split / "labels" / (new_stem + ".txt")).write_text("\n".join(lines) + "\n")
                c["images"] += 1
                for ln in lines:
                    c[CLASSES[int(ln.split()[0])]] += 1
            stats[(split, name)] = c

    yaml_text = (
        f"path: {OUT.as_posix()}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n"
        f"nc: {len(CLASSES)}\nnames: {CLASSES}\n"
    )
    (OUT / "data.yaml").write_text(yaml_text)

    for (split, name), c in stats.items():
        print(f"{split:6} {name:16} {dict(c)}")
    for split in ("train", "valid", "test"):
        n = len(list((OUT / split / "images").iterdir()))
        print(f"TOTAL {split}: {n} images")


if __name__ == "__main__":
    main()
