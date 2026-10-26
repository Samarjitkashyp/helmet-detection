"""Zip the made-night data for Colab: helmet_finetune_night.zip (night/train, night/val_night, night/val_day).
Run training/make_night_data.py first."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "training" / "_exp" / "finetune_night"
OUT = ROOT / "helmet_finetune_night.zip"
n = {}
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_STORED) as z:
    for sub in ("train", "val_night", "val_day"):
        for f in sorted((SRC / sub).rglob("*")):
            if f.is_file():
                z.write(f, f"night/{sub}/{f.relative_to(SRC / sub).as_posix()}")
                n[sub] = n.get(sub, 0) + (f.suffix == ".jpg")
    z.writestr("night/README.txt", "Night-looking copies (darkened, infrared-style, dusk) of daytime CCTV frames; labels are the same.\n"
                                   "A stand-in until real night footage from your own cameras is available.\n")
print(n, f"-> {OUT} {OUT.stat().st_size / 1e6:.0f} MB")
