"""Writes training/finetune_cctv_colab.ipynb (run: python -I training/make_finetune_notebook.py)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "finetune_cctv_colab.ipynb"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.strip("\n").splitlines(True)}


cells = [
    md("""
# Helmet detection: fine-tune on CCTV images and videos

Teaches the helmet model what CCTV footage looks like (small heads, caps and hats that must count as **no_helmet**).

**You need in Google Drive** (folder `MyDrive/helmet/`):
1. `helmet_finetune_colab.zip` : CCTV frames with labels + a replay set of the old data (so the model does not forget).
2. `best.pt` : the model currently on the server (`backend/models/best.pt`).
3. *(optional)* `helmet_finetune_india.zip` : photos from Indian roads with head labels (the notebook finds it by itself).
4. *(optional)* your own CCTV videos in `MyDrive/helmet/videos/` and/or images in `MyDrive/helmet/images/`.

Use a **GPU runtime**: Runtime > Change runtime type > T4 GPU. Then run the cells from top to bottom.
"""),
    md("## 1. Setup"),
    code("""
!pip -q install ultralytics
from google.colab import drive
drive.mount('/content/drive')
import os, shutil, zipfile, random, glob
from pathlib import Path
DRIVE = Path('/content/drive/MyDrive/helmet')
WORK = Path('/content/work'); WORK.mkdir(exist_ok=True)
print(sorted(p.name for p in DRIVE.iterdir()))
"""),
    md("## 2. Unpack the dataset"),
    code("""
DATA = WORK / 'data'
if DATA.exists(): shutil.rmtree(DATA)
with zipfile.ZipFile(DRIVE / 'helmet_finetune_colab.zip') as z:
    z.extractall(DATA)
NIGHT_ZIP = DRIVE / 'helmet_finetune_night.zip'      # optional: made-night copies of CCTV frames (see FINETUNE_STEPS.md)
HAS_NIGHT = NIGHT_ZIP.exists()
if HAS_NIGHT:
    with zipfile.ZipFile(NIGHT_ZIP) as z:
        z.extractall(DATA)
INDIA_ZIP = DRIVE / 'helmet_finetune_india.zip'      # optional: Indian road images (Kaggle master_traffic_violation), see FINETUNE_STEPS.md
HAS_INDIA = INDIA_ZIP.exists()
if HAS_INDIA:
    with zipfile.ZipFile(INDIA_ZIP) as z:
        z.extractall(DATA)
for sub in ['cctv/train', 'cctv/val', 'replay'] + (['night/train', 'night/val_night', 'night/val_day'] if HAS_NIGHT else []) + (['india/train', 'india/val'] if HAS_INDIA else []):
    n = len(list((DATA / sub / 'images').glob('*.jpg')))
    print(sub, n, 'images')
"""),
    md("""
## 3. (Optional) Add your own videos and images

Frames are cut out of each video (one every `EVERY_SECONDS`) and **pre-labelled by the current model**.
Pre-labels are only a draft: open the folder `work/data/mine/` (images + labels) in a labelling tool
(Roboflow, CVAT, LabelImg), fix the classes (**0 = helmet, 1 = no_helmet; caps, hats, scarves, bare heads = 1**),
delete wrong boxes, and put the corrected `.txt` files back before training. Skip this cell if you have nothing to add.
"""),
    code("""
from ultralytics import YOLO
import cv2
EVERY_SECONDS = 1.0       # one frame per second of video
CONF = 0.35               # low on purpose: it is easier to delete a wrong box than to draw a missing one
MINE = DATA / 'mine'; (MINE / 'images').mkdir(parents=True, exist_ok=True); (MINE / 'labels').mkdir(parents=True, exist_ok=True)
draft = YOLO(str(DRIVE / 'best.pt'))

def prelabel(img, name):
    cv2.imwrite(str(MINE / 'images' / f'{name}.jpg'), img)
    r = draft.predict(img, imgsz=1280, conf=CONF, verbose=False)[0]
    h, w = img.shape[:2]
    rows = [f'{int(c)} {(b[0]+b[2])/2/w:.6f} {(b[1]+b[3])/2/h:.6f} {(b[2]-b[0])/w:.6f} {(b[3]-b[1])/h:.6f}'
            for b, c in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist())]
    (MINE / 'labels' / f'{name}.txt').write_text('\\n'.join(rows) + ('\\n' if rows else ''))

count = 0
for v in sorted((DRIVE / 'videos').glob('*')) if (DRIVE / 'videos').exists() else []:
    cap = cv2.VideoCapture(str(v)); fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(1, int(fps * EVERY_SECONDS)); i = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if i % step == 0:
            prelabel(frame, f'{v.stem}_{i}'); count += 1
        i += 1
    cap.release()
for p in sorted((DRIVE / 'images').glob('*')) if (DRIVE / 'images').exists() else []:
    img = cv2.imread(str(p))
    if img is not None:
        prelabel(img, p.stem); count += 1
print(count, 'frames pre-labelled in', MINE)
"""),
    code("""
# After you have corrected the labels (or if you trust them), use them for training:
USE_MINE = False     # True = add work/data/mine to the training set
"""),
    md("## 4. Train"),
    code("""
IMGSZ, BATCH, EPOCHS = 960, 8, 30      # ~4500 images per epoch: about 5-8 minutes each on a T4. Use 1280 / batch 4 for a bit more accuracy (slower)
train = [str(DATA / 'cctv/train/images'), str(DATA / 'replay/images')]
if USE_MINE: train.append(str(DATA / 'mine/images'))
if HAS_NIGHT: train.append(str(DATA / 'night/train/images'))
if HAS_INDIA: train.append(str(DATA / 'india/train/images'))
val = [str(DATA / 'cctv/val/images')] + ([str(DATA / 'india/val/images')] if HAS_INDIA else [])
yaml = f\"\"\"train: {train}
val: {val}
nc: 2
names: [helmet, no_helmet]
\"\"\"
(WORK / 'data.yaml').write_text(yaml)
model = YOLO(str(DRIVE / 'best.pt'))
model.train(data=str(WORK / 'data.yaml'), epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, lr0=0.002, lrf=0.1, cos_lr=True,
            patience=15, close_mosaic=8, hsv_v=0.5, erasing=0.2, project=str(DRIVE / 'runs'), name='cctv', exist_ok=True)
"""),
    md("""
**If Colab disconnects while training:** reconnect, run cells 1 and 2 again (setup and unpack), the first lines of cell 4
(so `DRIVE`, `DATA`, `WORK` and `IMGSZ` exist), then run this cell. Progress is saved in Drive (`helmet/runs/cctv`), so it continues where it stopped.
"""),
    code("""
# only needed after a disconnect
from ultralytics import YOLO
YOLO(str(DRIVE / 'runs/cctv/weights/last.pt')).train(resume=True)
"""),
    md("## 5. Check the result (it must beat the old model on the CCTV validation images)"),
    code("""
del model
new = YOLO(str(DRIVE / 'runs/cctv/weights/best.pt'))
old = YOLO(str(DRIVE / 'best.pt'))
sets = [('day (held-out CCTV clips)', DATA / 'cctv/val/images')]
if HAS_INDIA:
    sets += [('Indian roads (held-out photos)', DATA / 'india/val/images')]
if HAS_NIGHT:
    sets += [('same frames, daylight', DATA / 'night/val_day/images'), ('same frames made to look like night', DATA / 'night/val_night/images')]
for label, folder in sets:
    (WORK / 'eval.yaml').write_text(f'train: {folder}\\nval: {folder}\\nnc: 2\\nnames: [helmet, no_helmet]\\n')
    for name, m in [('old model', old), ('new model', new)]:
        r = m.val(data=str(WORK / 'eval.yaml'), imgsz=IMGSZ, conf=0.5, verbose=False, plots=False)
        print(f'{label:38} {name}: precision {r.box.mp:.3f}  recall {r.box.mr:.3f}  mAP50 {r.box.map50:.3f}')
"""),
    code("""
# look at a few validation frames with the new model (red = no_helmet, green = helmet)
import matplotlib.pyplot as plt
files = random.sample(sorted((DATA / 'cctv/val/images').glob('*.jpg')), 4)
fig, ax = plt.subplots(2, 2, figsize=(16, 9))
for a, f in zip(ax.ravel(), files):
    a.imshow(new.predict(str(f), imgsz=IMGSZ, conf=0.5, verbose=False)[0].plot()[:, :, ::-1]); a.axis('off')
plt.tight_layout(); plt.show()
"""),
    md("""
## 6. Save the new model

If the new model is better, download `best.pt` and `live.onnx`. Then on your PC:
1. Put `best.pt` in `backend/models/` (keep the old one as a backup).
2. Put `live.onnx` and `live.json` in `backend/models/` (the phone app downloads it automatically).
3. Run `.\\deploy\\make_bundle.ps1`, upload the zip to the server and run `deploy/update.sh` (see `deploy/README_DEPLOY.md`).
4. Restart the CCTV worker on the PC (it reads `backend/models/best.pt`).
"""),
    code("""
best = DRIVE / 'runs/cctv/weights/best.pt'
shutil.copy(best, DRIVE / 'best_cctv.pt')
onnx_path = YOLO(str(best)).export(format='onnx', imgsz=416, opset=12, simplify=True)   # same settings as the app's live model
shutil.copy(onnx_path, DRIVE / 'live.onnx')
from google.colab import files as colab_files
colab_files.download(str(best)); colab_files.download(str(DRIVE / 'live.onnx'))
print('Saved best_cctv.pt and live.onnx in', DRIVE)
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT)



