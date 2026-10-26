"""How much does the current model lose on night-looking frames? Same 200 validation frames, in daylight and made-night.
Usage: python -I training/eval_night_baseline.py [model.pt]"""
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
N = ROOT / "training" / "_exp" / "finetune_night"
model = YOLO(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "backend" / "models" / "best.pt"))
for name in ("val_day", "val_night"):
    yaml = N / f"{name}.yaml"
    yaml.write_text(f"train: {N / 'train' / 'images'}\nval: {N / name / 'images'}\nnc: 2\nnames: [helmet, no_helmet]\n")
    r = model.val(data=str(yaml), imgsz=960, conf=0.5, verbose=False, plots=False, project=str(N / "runs"), name=name, exist_ok=True)
    print(f"{name:10} precision {r.box.mp:.3f}  recall {r.box.mr:.3f}  mAP50 {r.box.map50:.3f}", flush=True)
