# Helmet Detection

AI-powered helmet compliance checking. Record or upload a short video, and the system finds every person in it, decides **helmet / no helmet**, and returns photo evidence with timestamps. Includes a REST API, an admin dashboard, and a retraining loop driven by reviewer feedback.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-111F68)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-Android-02569B?logo=flutter&logoColor=white)

> **Mobile app:** [helmet-detection-mobile-app](https://github.com/Samarjitkashyp/helmet-detection-mobile-app) (Flutter, Android). This repository is the backend it talks to.

## Features

- **Video analysis** – YOLOv8 detection with ByteTrack tracking, so each person gets one verdict, not one per frame.
- **Hard-negative aware** – caps, hats, hijabs and turbans are treated as *no helmet*, not as helmets.
- **Evidence** – best frame per person (annotated and raw), confidence, and timestamp.
- **Admin dashboard** – stats, violation review, false-positive marking, user and video management, runtime tuning, CSV export.
- **Retraining loop** – export reviewed frames as a YOLO dataset and fine-tune on Colab.
- **App distribution** – upload the Android APK from the dashboard (Settings → Mobile app) with a live progress bar, then publish it; a "Download app" button appears in the dashboard and users install from the public `/app` page.
- **Production-ready backend** – JWT auth, role-based access, login rate limiting, optional admin IP allow-list, systemd/nginx deployment kit.
- **CCTV monitoring** – a worker reads a camera's RTSP stream, tracks every rider on its own and raises one alert per person without a helmet: photo, Telegram message, dashboard event, and an Alerts tab in the app. See [CCTV monitoring](#cctv-monitoring).
- **Quality hints** – warns when a video is too dark or the model is unsure.
- **Live preview model** – the server hands the mobile app an ONNX build of the model (`/app/live-model`) so the app can draw helmet / no-helmet boxes on the camera preview while framing a shot. A retrained model reaches phones without a new app release.

## How it works

```mermaid
flowchart LR
    A[Flutter app<br/>record / upload] -->|HTTPS + JWT| B[FastAPI]
    B --> C[(PostgreSQL)]
    B --> D[Background job<br/>OpenCV + YOLOv8 + ByteTrack]
    D --> C
    D --> E[Evidence photos]
    F[Admin dashboard] --> B
```

1. The client uploads a video (`POST /videos`); the API stores it and returns immediately.
2. A background worker samples every *N*th frame, runs YOLOv8, tracks people across frames, and picks one verdict per person.
3. Results (label, confidence, timestamp, photos) are stored and served to the app and the dashboard.

## CCTV monitoring

```mermaid
flowchart LR
    CAM[IP camera<br/>RTSP] --> W[CCTV worker<br/>PC near the camera]
    W -->|photo + heartbeat<br/>X-Worker-Key| S[FastAPI server]
    S --> T[Telegram]
    S --> D[Dashboard<br/>Cameras / CCTV events]
    S --> M[App: Alerts tab]
    S -.->|no heartbeat| T
```

The heavy model work runs in `services/cctv_worker.py` on a PC next to the camera; the server only stores events and sends messages, so a small shared server is enough. The worker sends a heartbeat every minute and the server warns on Telegram when it stops (PC off, camera stream down).

Per frame the worker finds motorcycles (a COCO YOLOv8s model), looks for heads on the whole frame and, on every 5th frame, on an enlarged crop around each motorcycle; a small crop classifier double-checks helmet / no helmet; only heads sitting on a motorcycle count (pedestrians and cyclists have no helmet rule). Every head is tracked separately, so a frame with several helmeted and bare-headed riders gives one verdict per person.

```bash
# server .env: CCTV_WORKER_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID    (add the camera in the dashboard: Cameras)
# PC backend/.env: CCTV_SERVER_URL, CCTV_WORKER_KEY
python -m services.cctv_worker --camera-id 1                  # run by hand
.\deploy\pc\install_autostart.ps1 -CameraId 1                 # or start at every login (add -TestStream for a fake looped camera)
```

**Measured** on the [HELMET dataset](https://osf.io/4pwj8/) (Myanmar traffic cameras, clips the model never saw during training), 12 of the busiest test clips with 170 bare-headed riders:

| Analysed frames per second | Riders that got an alert | Alerts on fully helmeted bikes |
|---|---|---|
| 1 | about 74 % | about 1 % |
| 2 | about 90 % | about 1 % |

A desktop i3 CPU analyses about 1.4 frames per second with the defaults; a faster CPU or a GPU raises the share of riders caught. On held-out CCTV frames, fine-tuning on this dataset (`training/finetune_cctv_colab.ipynb`) lifted recall from 0.62 to 0.79 and mAP@50 from 0.55 to 0.75. Night footage is not covered by real data yet; `training/make_night_data.py` makes dark, infrared-style copies of daytime frames as a stand-in (before training on them, recall was 0.76 in daylight and 0.34 on the same frames made dark).

The public write-up of this work lives at **[aiaxom.co.in/research/helmet-detection](https://aiaxom.co.in/research/helmet-detection/)** (how it works, results, CCTV setup, model card, FAQ). Its source is in `website/research/` (`python website/research/build_site.py` builds the static pages; `install_on_server.sh` and `axom-research.nginx.conf` publish them next to the main site).

## Model performance

The weights in `backend/models/best.pt` are the CCTV fine-tune of the model described here. The table below is the original model, YOLOv8s fine-tuned at 640 px on ~11.7k training images from seven public datasets (see [Credits](#datasets--credits)). Held-out test images, confidence threshold 0.4:

| Test set | Class | Precision | Recall |
|---|---|---|---|
| Riders / people (300 images) | helmet | 0.93 | 0.93 |
| | no_helmet | 0.95 | 0.84 |
| Caps / hats / hijabs (87 images) | helmet | 0.94 | 0.85 |
| | no_helmet | 0.87 | 0.88 |

mAP@50: **0.92** (riders/people), **0.91** (head coverings). Adding head-covering data raised `no_helmet` recall on caps and hats from 0.21 to 0.88 with no loss on the original set.

> These numbers come from the datasets' own test splits. Accuracy on your cameras will differ: use the review and retraining loop to adapt the model.

Inference runs on CPU at roughly 0.5 s per analysed frame (desktop i3). No GPU is required.

## Tech stack

| Layer | Technology |
|---|---|
| Detection | Ultralytics YOLOv8, ByteTrack, OpenCV, PyTorch (CPU) |
| API | FastAPI, SQLAlchemy 2, Pydantic |
| Database | PostgreSQL (SQLite works for trials) |
| Admin | Jinja2 + HTMX + Chart.js, SQLAdmin |
| Auth | JWT, bcrypt, role-based access |
| Mobile | Flutter (Android), see [helmet-detection-mobile-app](https://github.com/Samarjitkashyp/helmet-detection-mobile-app) |
| Deploy | systemd, nginx, certbot, Cloudflare-friendly |

## Repository structure

```
backend/
  main.py              app entry point
  config.py            environment-driven settings
  api/                 auth and video endpoints
  admin/               dashboard (Jinja2/HTMX) and SQLAdmin data editor
  services/            video processing (YOLO + tracking), cctv_worker.py, Telegram / push / heartbeat watchdog
  core/                security, rate limiting, dependencies
  db/                  models and session
  scripts/             create_admin.py, seed_demo.py
  models/best.pt       trained weights
deploy/                nginx, systemd, setup/update/backup scripts, README_DEPLOY.md
deploy/pc/             CCTV worker auto-start for Windows (Task Scheduler)
training/              dataset merge, Colab notebooks, model comparison, CCTV evaluation and fine-tuning tools (FINETUNE_STEPS.md)
```

## Quick start (local)

Requires Python 3.11+ and PostgreSQL (or use a SQLite URL to try it out).

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env    # then edit DATABASE_URL and SECRET_KEY
cd backend
python scripts/create_admin.py          # prompts for admin email and password
uvicorn main:app --reload
```

- Admin dashboard: <http://127.0.0.1:8000/panel>
- Interactive API docs (development only): <http://127.0.0.1:8000/docs>
- Optional demo data: `python scripts/seed_demo.py` (remove with `--clear`)

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Create account, get JWT |
| GET | `/auth/me` | Current user |
| POST | `/videos` | Upload a video (returns `202`, processes in background) |
| GET | `/videos` | List your videos with violation counts |
| GET | `/videos/{id}/status` | `processing` / `done` / `failed` |
| GET | `/videos/{id}/results` | Verdict per person, summary, quality warnings |
| GET | `/videos/{id}/detections/{det_id}/image` | Evidence photo |
| DELETE | `/videos/{id}` | Delete video and results |
| GET | `/health` | Liveness check |
| GET | `/app`, `/app/download` | Public install page and APK download (admins upload from the dashboard) |
| GET | `/app/live-model/info`, `/app/live-model` | Version and file of the on-device model (login required) |

## Configuration

Environment variables (`backend/.env`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | – | SQLAlchemy URL |
| `SECRET_KEY` | – | JWT/session signing (32+ chars in production) |
| `APP_ENV` | `development` | `production` enables hardening (secure cookies, docs off, config checks) |
| `MAX_UPLOAD_MB` | `300` | Upload size limit |
| `KEEP_ORIGINAL_VIDEOS` | `true` | `false` deletes each video after analysis |
| `ADMIN_ALLOWED_IPS` | – | Restrict `/panel` and `/admin` to these IPs |

Detection settings are editable at runtime in the dashboard: confidence threshold, frame skip, minimum person height, minimum frames per person, inference size, maximum video length.

## Training and retraining

```bash
python training/merge_datasets.py            # unify datasets into classes: helmet / no_helmet
python training/compare_models.py best.pt best_v2.pt   # compare two weights on held-out sets
python training/export_onnx.py 416           # build backend/models/live.onnx for the app's live preview
python training/eval_onnx.py                 # check the ONNX model against the PyTorch one
```

CCTV tools: `training/osf_fetch.py` (fast resumable download of the HELMET dataset), `eval_pipeline.py` / `eval_persons.py` / `eval_replay.py` (score the worker's logic against the per-motorcycle ground truth), `mine_head_crops.py` + `train_head_cls.py` (crop classifier), `build_finetune_zip.py` + `finetune_cctv_colab.ipynb` (detector fine-tune, steps in `training/FINETUNE_STEPS.md`).

`live.onnx` is generated (about 45 MB, git-ignored): run the export after every retraining and redeploy.

Fine-tune with `training/train_colab.ipynb` (free Colab GPU). In production, flag wrong detections in the dashboard and use **Export → Retrain set** to collect corrected frames for the next training round.

## Deployment

A complete kit for Ubuntu/Debian (nginx, systemd, PostgreSQL, HTTPS, nightly backups) is in [`deploy/`](deploy/README_DEPLOY.md).

## Security

JWT auth with role checks, bcrypt password hashing, login rate limiting, secure admin cookies, per-user access to videos and photos, optional admin IP allow-list, and a startup check that refuses weak secrets in production. Videos contain people's faces: restrict access, and consider `KEEP_ORIGINAL_VIDEOS=false`.

## Limitations

- Accuracy drops in darkness, at long range, and with heavily occluded heads. CCTV alerts catch about three in four bare-headed riders at one analysed frame per second on a desktop CPU; real night footage is not in the training data yet.
- Turbans (pagdi) are not yet covered by the training data.
- Counts are **sightings**, not unique people: tracking follows a person while they stay in view, but the same person who leaves and re-enters (for example after a camera cut in an edited clip) is counted again. Tracker tuning (ByteTrack vs BoT-SORT, frame skip, buffer) did not change this; unifying identities across shots would need a person re-identification model.
- Processing is CPU-bound: about one minute of video per several minutes of compute on a small server.
- Schema changes need migrations (Alembic is not set up yet).

## Datasets & credits

Trained on public Roboflow Universe datasets. Thanks to their authors:

| Dataset | License |
|---|---|
| [Helmet and no helmet rider detection](https://universe.roboflow.com/gw-khadatkar-and-sv-wasule/helmet-and-no-helmet-rider-detection) | CC BY 4.0 |
| [Helmet Detection_YOLOv8](https://universe.roboflow.com/learning-evidence/helmet-detection_yolov8) | CC BY 4.0 |
| [Helmet and Number Plate Detection for Motorbike Safety](https://universe.roboflow.com/helmet-and-number-plate-detection-project/helmet-and-number-plate-detection-for-motorbike-safety-iityz) | CC BY 4.0 |
| [Headware detection](https://universe.roboflow.com/atm/headware-detection) | CC BY 4.0 |
| [Cap](https://universe.roboflow.com/ny/cap-ghxtg) | CC BY 4.0 |
| [Hats and masks](https://universe.roboflow.com/krrrz/hats-and-masks) | CC BY 4.0 |
| [Head Accessories](https://universe.roboflow.com/theyearoflinux/head-accessories-9xdyg) | MIT |

The CCTV fine-tune also uses the [HELMET dataset](https://osf.io/4pwj8/) of Myanmar traffic-camera clips (CC BY 4.0). Please credit its authors if you reuse the models or the derived labels. Motorcycle detection uses the COCO-pretrained YOLOv8s from Ultralytics.

Built with [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (AGPL-3.0). Check its license terms before commercial use.

## License

The code in this repository is released under the [MIT License](LICENSE). Third-party components keep their own licenses: Ultralytics YOLOv8 is AGPL-3.0 and the training datasets are listed above. The trained weights are derived from both, so review those terms before commercial use.

## Author

[Samarjitkashyp](https://github.com/Samarjitkashyp)
