"""Export the trained weights to ONNX for the on-device live preview in the mobile app.

Usage: python -I training/export_onnx.py [imgsz] [out_dir]
Produces best_<imgsz>.onnx (float32) and best_<imgsz>_int8.onnx (dynamic int8, ~4x smaller).
"""
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
imgsz = int(sys.argv[1]) if len(sys.argv) > 1 else 416
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "training" / "_exp"
out_dir.mkdir(parents=True, exist_ok=True)

exported = Path(YOLO(str(ROOT / "backend" / "models" / "best.pt")).export(
    format="onnx", imgsz=imgsz, opset=12, simplify=True, dynamic=False, half=False))
fp32 = out_dir / f"best_{imgsz}.onnx"
shutil.move(str(exported), fp32)   # ultralytics writes next to best.pt; keep backend/models tidy
print("float32:", fp32, f"{fp32.stat().st_size / 1e6:.1f} MB")

from onnxruntime.quantization import QuantType, quantize_dynamic  # noqa: E402

int8 = out_dir / f"best_{imgsz}_int8.onnx"
quantize_dynamic(str(fp32), str(int8), weight_type=QuantType.QUInt8)
print("int8   :", int8, f"{int8.stat().st_size / 1e6:.1f} MB")

# The mobile app downloads this model from the server (GET /app/live-model) for its live detection boxes.
import json  # noqa: E402

live = ROOT / "backend" / "models" / "live.onnx"
shutil.copy2(fp32, live)
(live.with_suffix(".json")).write_text(json.dumps({"imgsz": imgsz, "classes": ["helmet", "no_helmet"]}))
print("served to the app:", live)
