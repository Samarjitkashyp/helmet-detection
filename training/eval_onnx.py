"""Compare the PyTorch model with the ONNX exports (the on-device live preview) on held-out test images.

The pre/post-processing here is exactly what the Flutter app implements (letterbox 114, /255, NMS 0.45),
so these numbers show what the phone will see.

Usage: python -I training/eval_onnx.py
"""
import random
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "data_merged" / "test"
EXP = ROOT / "training" / "_exp"
CONF, NMS_IOU, MATCH_IOU = 0.4, 0.45, 0.5


def letterbox(img, size):
    h, w = img.shape[:2]
    r = size / max(h, w)
    nh, nw = round(h * r), round(w * r)
    top, left = (size - nh) // 2, (size - nw) // 2
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    return canvas, r, left, top


def onnx_detect(sess, img, size):
    canvas, r, left, top = letterbox(img, size)
    x = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]      # (6, N)
    boxes, scores = out[:4].T, out[4:].T
    cls = scores.argmax(1)
    conf = scores.max(1)
    keep = conf >= CONF
    boxes, cls, conf = boxes[keep], cls[keep], conf[keep]
    if not len(boxes):
        return []
    xywh = [[float(cx - w / 2), float(cy - h / 2), float(w), float(h)] for cx, cy, w, h in boxes]
    idx = cv2.dnn.NMSBoxes(xywh, conf.tolist(), CONF, NMS_IOU)
    res = []
    for i in np.array(idx).flatten():
        cx, cy, w, h = boxes[i]
        res.append((int(cls[i]), float(conf[i]),
                    ((cx - w / 2 - left) / r, (cy - h / 2 - top) / r, (cx + w / 2 - left) / r, (cy + h / 2 - top) / r)))
    return res


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def load_gt(label_path, w, h):
    gt = []
    for line in label_path.read_text().splitlines():
        p = line.split()
        if len(p) != 5:
            continue
        c, cx, cy, bw, bh = int(p[0]), *map(float, p[1:])
        gt.append((c, ((cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h)))
    return gt


def score(detector, files):
    tp, fp, fn = [0, 0], [0, 0], [0, 0]
    t = 0.0
    for p in files:
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        gt = load_gt(TEST / "labels" / (p.stem + ".txt"), w, h)
        t0 = time.perf_counter()
        det = detector(img)
        t += time.perf_counter() - t0
        used = set()
        for c, _conf, box in sorted(det, key=lambda d: -d[1]):
            best, bj = 0, None
            for j, (gc, gb) in enumerate(gt):
                if gc == c and j not in used:
                    v = iou(box, gb)
                    if v > best:
                        best, bj = v, j
            if best >= MATCH_IOU:
                tp[c] += 1; used.add(bj)
            else:
                fp[c] += 1
        for j, (gc, _) in enumerate(gt):
            if j not in used:
                fn[gc] += 1
    out = []
    for c, name in enumerate(["helmet", "no_helmet"]):
        p_ = tp[c] / max(1, tp[c] + fp[c]); r_ = tp[c] / max(1, tp[c] + fn[c])
        out.append(f"{name} P={p_:.2f} R={r_:.2f}")
    return " | ".join(out), 1000 * t / len(files)


imgs = sorted((TEST / "images").iterdir())
extra = [p for p in imgs if p.name.startswith("extra_")]
orig = random.Random(11).sample([p for p in imgs if not p.name.startswith("extra_")], 200)
sets = {"riders/people (200 imgs)": orig, f"caps/hats ({len(extra)} imgs)": extra}

pt = YOLO(str(ROOT / "backend" / "models" / "best.pt"))
def pt_detect(img):
    r = pt.predict(img, imgsz=640, conf=CONF, iou=NMS_IOU, verbose=False)[0]
    return [(int(c), float(s), tuple(b)) for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]

models = {"PyTorch @640 (server)": pt_detect}
for size in (416,):
    for tag, fname in (("fp32", f"best_{size}.onnx"), ("int8", f"best_{size}_int8.onnx")):
        path = EXP / fname
        if path.exists():
            so = ort.SessionOptions(); so.intra_op_num_threads = 4
            sess = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
            models[f"ONNX {tag} @{size}"] = (lambda s, z: (lambda img: onnx_detect(s, img, z)))(sess, size)

for set_name, files in sets.items():
    print(f"\n### {set_name}")
    for name, det in models.items():
        res, ms = score(det, files)
        print(f"{name:24} {res}  ({ms:.0f} ms/img on this PC)", flush=True)
print("\nDONE")
