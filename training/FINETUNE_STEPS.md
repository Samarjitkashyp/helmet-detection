# Fine-tune steps (CCTV model)

Files you need (all in `E:\helmet_detection\`):

| File | What it is |
|---|---|
| `helmet_finetune_colab.zip` | CCTV frames with labels + replay images (general data incl. caps/hats) |
| `training\finetune_cctv_colab.ipynb` | The Colab notebook |
| `backend\models\best.pt` | The model currently used by the server and the CCTV worker |

## 1. Google Drive
1. Create the folder `MyDrive/helmet/`.
2. Upload `helmet_finetune_colab.zip` and `best.pt` into it.
3. Optional: your own CCTV videos in `MyDrive/helmet/videos/`, images in `MyDrive/helmet/images/`.

### Night (optional, recommended)
Also upload `helmet_finetune_night.zip` (273 MB) to the same Drive folder. The notebook finds it by itself and adds
the night-style training images; cell 5 then prints day and night scores for the old and the new model.
These images are daytime frames made dark / infrared-like (the dataset has no real night footage), so they are a stand-in.
Before training, the current model scored recall 0.76 on daylight frames but only 0.34 on the same frames made dark.
Real night video from your own cameras (cell 3) will help much more.

### Indian roads (optional, NOT recommended as built: tested 2026-10-27, did not hold up)
Result: a model trained with this zip beat the old one on its own source (Kaggle master_traffic_violation, night-like frames) but NOT on
datasets it never saw (`training/eval_heldout.py`): bare-head catch rate on driver_passenger_7class 73 % -> 57 %, uit_helmet_v8 91 % -> 88 %,
and false alarms on helmeted riders doubled on helmet_violations_roboflow (9 % -> 18 %) and mp_final (4 % -> 12 %). The old model was put back.
Likely cause: the head boxes were made by our own detector, so its mistakes were baked into the labels. Do not use this zip again unless
the head labels are checked by hand or come from real head-box datasets. Original instructions:

Also upload `helmet_finetune_india.zip` to the same Drive folder. The notebook finds it by itself, trains on it too, and cell 5 then
prints the old and the new model on held-out Indian photos next to the CCTV frames.
These are photos from Indian roads (Kaggle `master_traffic_violation`, Roboflow export: check its licence on the Kaggle page before sharing).
The dataset labels whole riders; the head boxes in the zip were made by our own detector inside each rider box and carry the rider's label,
so the model is taught on the cases it got wrong. Riders where no head was found were skipped. Before training, on held-out
Indian photos the current model caught about 59 % of bare-headed riders at confidence 0.40 (about 65 % at 0.25).
The photos are small (640 px), so heads are tiny: real Indian CCTV frames from your own cameras will still help more.

## 2. Colab
1. Open `finetune_cctv_colab.ipynb` in Google Colab (File > Upload notebook).
2. Runtime > Change runtime type > **T4 GPU**.
3. Run the cells from top to bottom. Training takes roughly 2 to 3 hours for 30 epochs at 960 px on a free T4
   (about 4500 images per epoch). For a bit more accuracy set `IMGSZ, BATCH = 1280, 4` in the training cell (slower).
4. Cell 3 (optional) cuts frames out of your videos and pre-labels them. These labels are only a draft:
   correct them (0 = helmet, 1 = no_helmet; caps, hats, scarves and bare heads are 1) in Roboflow / CVAT / LabelImg,
   put the corrected `.txt` files back and set `USE_MINE = True`.
5. Cell 5 prints precision/recall of the old and the new model on the same CCTV validation frames.
   Use the new model only if it is clearly better.

## 3. Put the new model into the project
1. Download `best.pt` and `live.onnx` (the last cell does it, copies are also in Drive).
2. Copy the old `backend\models\best.pt` somewhere safe, then copy the new `best.pt` there.
3. Copy `live.onnx` into `backend\models\` (the phone app downloads it by itself; run `training\export_onnx.py`
   if you also need the matching `live.json`).
4. Server: `.\deploy\make_bundle.ps1`, upload `helmet_bundle.zip`, then on the server
   `unzip -o helmet_bundle.zip -d helmet_bundle && sudo bash helmet_bundle/deploy/update.sh`.
5. CCTV worker (PC): restart it so it loads the new model:
   `Stop-ScheduledTask HelmetCCTVWorker; Start-ScheduledTask HelmetCCTVWorker`.

## 4. Check with the test stream
```
.\deploy\pc\install_autostart.ps1 -CameraId 1 -TestStream
```
Watch Telegram / the CCTV events page for a few minutes. Remove the test stream when a real camera is connected:
`.\deploy\pc\install_autostart.ps1 -CameraId 1`.

## Notes
- Labels in the zip come from the Myanmar dataset's per-motorcycle ground truth (CC BY 4.0). Only heads on motorcycles
  are labelled; pedestrians and cyclists are intentionally left unlabelled.
- More CCTV videos from your own site will help much more than anything else: the model learns your camera angle, light and clothing.
- Night footage is not covered yet.
