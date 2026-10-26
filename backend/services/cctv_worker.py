"""CCTV monitor: reads an RTSP stream, tracks people and raises an alert (photo + Telegram) for each
person seen without a helmet.

Two ways to run (set in backend/.env or with flags):
  Remote (a PC near the camera, the normal setup):  CCTV_SERVER_URL and CCTV_WORKER_KEY in .env, then
      python -m services.cctv_worker --camera-id 1
    The camera address comes from the server's Cameras page. Alerts are uploaded to the server, which saves
    them and sends the Telegram message; a heartbeat every minute lets the server warn when this PC is off.
    Alerts that cannot be uploaded (no internet) wait in storage/cctv/outbox and are sent later.
  Local (testing, needs the database and Telegram keys on this machine):
      python -m services.cctv_worker --local --camera-id 1      or      --local --url rtsp://... --name Cam
Stop with Ctrl+C.

One alert per tracked person. A person is flagged once the model has seen them without a helmet in at
least --min-hits frames and the no_helmet evidence outweighs the helmet evidence (same idea as the
video processor). Frames are read in a background thread and only the newest one is analysed, so the
worker never falls behind a live stream.
"""
import argparse
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import requests
from ultralytics import YOLO
from ultralytics.engine.results import Boxes
from ultralytics.trackers import BYTETracker
from ultralytics.utils import ROOT as ULTRA_ROOT, YAML, IterableSimpleNamespace

from config import MODEL_PATH, STORAGE_DIR

CCTV_DIR = STORAGE_DIR / "cctv"
OUTBOX = CCTV_DIR / "outbox"
HELMET, NO_HELMET = 0, 1
BICYCLE, MOTORCYCLE = 1, 3           # COCO class ids of the general vehicle model
VEHICLE_MODEL = MODEL_PATH.parent / "coco_yolov8s.pt"
CLASSIFIER_MODEL = MODEL_PATH.parent / "head_cls.pt"   # made by training/train_head_cls.py


class LatestFrame:
    """Reads the stream in a thread and keeps only the newest frame; reconnects when the stream drops."""

    def __init__(self, url: str):
        self.url, self.frame, self.stamp, self.stop = url, None, 0.0, False
        self._lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self.stop:
            cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print("stream not reachable, retrying in 5 s", flush=True)
                time.sleep(5)
                continue
            print("stream connected", flush=True)
            while not self.stop:
                ok, f = cap.read()
                if not ok:
                    break
                with self._lock:
                    self.frame, self.stamp = f, time.time()
            cap.release()
            print("stream lost, reconnecting", flush=True)
            time.sleep(2)

    def get(self):
        with self._lock:
            return self.frame, self.stamp


class Telegram:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not (self.token and self.chat):
            raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in backend/.env")

    def photo(self, path: Path, caption: str) -> bool:
        try:
            with open(path, "rb") as f:
                r = requests.post(f"https://api.telegram.org/bot{self.token}/sendPhoto",
                                  data={"chat_id": self.chat, "caption": caption}, files={"photo": f}, timeout=20)
            if not r.ok:
                print("telegram error", r.status_code, r.text[:200], flush=True)
            return r.ok
        except requests.RequestException as e:   # never include the URL: it contains the bot token
            print("telegram send failed:", type(e).__name__, flush=True)
            return False


class RemoteSink:
    """Talks to the helmet server (see api/routes_cctv.py)."""

    def __init__(self, base: str, key: str):
        self.base = base.rstrip("/")
        self.http = requests.Session()
        self.http.headers["X-Worker-Key"] = key

    def camera(self, cam_id: int) -> dict:
        """Waits until the server answers; a PC that boots before the network is up just keeps trying."""
        while True:
            try:
                r = self.http.get(f"{self.base}/api/cctv/cameras/{cam_id}", timeout=20)
                if r.status_code in (401, 404):
                    raise SystemExit(f"Server refused the camera request ({r.status_code}): check CCTV_WORKER_KEY and the camera id")
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                print("server not reachable, retrying in 15 s:", type(e).__name__, flush=True)
                time.sleep(15)

    def heartbeat(self, name: str, stream_ok: bool) -> None:
        try:
            self.http.post(f"{self.base}/api/cctv/heartbeat", json={"camera_name": name, "stream_ok": stream_ok}, timeout=15)
        except requests.RequestException:
            pass    # the server notices missing heartbeats itself

    def event(self, jpeg: bytes, camera_id, name: str, track_id: int, conf: float, people: int) -> bool:
        data = {"camera_name": name, "track_id": track_id, "confidence": conf, "people": people}
        if camera_id:
            data["camera_id"] = camera_id
        try:
            r = self.http.post(f"{self.base}/api/cctv/event", data=data, timeout=60,
                               files={"photo": ("alert.jpg", jpeg, "image/jpeg")})
            return r.ok
        except requests.RequestException as e:
            print("upload failed:", type(e).__name__, flush=True)
            return False

    def flush_outbox(self) -> None:
        """Send alerts that could not be uploaded earlier (oldest first)."""
        for meta in sorted(OUTBOX.glob("*.json")):
            jpg = meta.with_suffix(".jpg")
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
                ok = jpg.is_file() and self.event(jpg.read_bytes(), m["camera_id"], m["name"], m["track_id"], m["conf"], m["people"])
            except (OSError, ValueError, KeyError):
                ok = True    # unreadable leftovers are dropped
            if not ok:
                return       # still offline: try again at the next heartbeat
            meta.unlink(missing_ok=True)
            jpg.unlink(missing_ok=True)


def start_heartbeat(sink: RemoteSink, src: "LatestFrame", name: str):
    def loop():
        while not src.stop:
            _, stamp = src.get()
            sink.heartbeat(name, stream_ok=time.time() - stamp < 30)
            sink.flush_outbox()
            time.sleep(60)
    threading.Thread(target=loop, daemon=True, name="heartbeat").start()


class FrameAnalyzer:
    """Everything between 'a frame arrives' and 'these people are newly confirmed without a helmet'.

    Every rider head in the frame is tracked on its own (ByteTrack), so a frame with several helmeted and
    several bare-headed riders gives one track and one verdict per person, never one verdict per frame.
    A person is flagged once, after args.min_hits sightings without helmet whose confidence outweighs the
    sightings with helmet."""

    def __init__(self, args):
        self.args = args
        self.model = YOLO(str(MODEL_PATH))
        self.vmodel = None
        if not args.all_heads:
            if not VEHICLE_MODEL.is_file():
                raise SystemExit(f"Vehicle model missing: {VEHICLE_MODEL} (a COCO YOLOv8s file), or use --all-heads")
            self.vmodel = YOLO(str(VEHICLE_MODEL))
        self.cmodel = None
        if not args.no_classifier and CLASSIFIER_MODEL.is_file():
            self.cmodel = YOLO(str(CLASSIFIER_MODEL))
        elif not args.no_classifier:
            print("head classifier not found, running without it", flush=True)
        self.tracker = (SimpleTracker(gate=getattr(args, "tracker_gate", 3.0)) if getattr(args, "tracker", "simple") == "simple" else
                        BYTETracker(IterableSimpleNamespace(**YAML.load(ULTRA_ROOT / "cfg/trackers/bytetrack.yaml"))))
        self.recent = []    # (time, fresh) of the latest alerts, for de-duplication
        self.stats = {}     # track id -> {"bad": n, "ok": n, "bad_conf": sum, "ok_conf": sum, "alerted": bool}
        self.alerts = 0      # people confirmed without helmet (including repeats that were suppressed)
        self.alerts_sent = 0 # alerts really raised
        self.frame_no = 0
        self.memory = {}     # alerted track id -> where that head was last seen and how fast it moved
        self.clock = time.time   # replaced by a simulated clock when replaying recorded frames

    def _is_repeat(self, box, tid, visible):
        """Is this 'new' person really somebody alerted a moment ago whose track id was lost?

        A lost track is expected a little further along its path (position + speed), about as big, and it
        cannot be a head that is in view right now under its own id (two heads in one frame are two people)."""
        cx, cy, size = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, max(box[2] - box[0], box[3] - box[1], 1)
        for mtid, m in self.memory.items():
            gap = self.frame_no - m["frame"]
            if mtid == tid or mtid in visible or not 1 <= gap <= getattr(self.args, "dedup_gap", 6):
                continue
            px, py = m["cx"] + m["vx"] * gap, m["cy"] + m["vy"] * gap
            dist = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5 / max(size, m["size"])
            if dist <= getattr(self.args, "dedup_dist", 2.5) and 0.6 <= size / m["size"] <= 1.7:
                return True
        return False

    def analyze(self, frame):
        """Returns (shown, fresh): every rider head in view as (box, cls), and the people newly flagged as (box, track, conf)."""
        return self.decide(frame, *self.detect(frame))

    def detect(self, frame):
        """The slow, model-driven part: motorcycles in view and every head with its helmet verdict."""
        a = self.args
        vehicles = []
        if self.vmodel is not None:
            vr = self.vmodel.predict(frame, imgsz=a.vehicle_imgsz, conf=0.25, classes=[BICYCLE, MOTORCYCLE], verbose=False)[0]
            vehicles = list(zip(vr.boxes.cls.int().tolist(), vr.boxes.xyxy.tolist()))
        self.n_detect = getattr(self, "n_detect", -1) + 1
        every = max(1, getattr(a, "crop_every", 1))    # the costly look at every motorcycle only on every Nth frame
        heads = find_heads(self.model, frame, vehicles, a, use_crops=self.n_detect % every == 0)
        if self.cmodel is not None:
            heads = refine_heads(self.cmodel, frame, heads, a.cls_threshold)
        return vehicles, heads

    def decide(self, frame, vehicles, heads):
        """The fast part: tracking, per-person verdicts, repeat filter."""
        a = self.args
        shown, fresh = [], []
        self.frame_no += 1
        tracked = self.tracker.update(heads) if isinstance(self.tracker, SimpleTracker) else track_heads(self.tracker, heads, frame)
        tracked = [t for t in tracked
                   if min(t[0][2] - t[0][0], t[0][3] - t[0][1]) >= a.min_box
                   and (self.vmodel is None or is_rider_head(t[0], vehicles))]    # pedestrians and cyclists have no helmet rule
        visible = {t[1] for t in tracked}
        for box, tid, cls, conf in tracked:
            m = self.memory.get(tid)
            if m:    # an alerted person is in view again: remember where, and how fast they move
                gap = max(1, self.frame_no - m["frame"])
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                m.update(vx=(cx - m["cx"]) / gap, vy=(cy - m["cy"]) / gap, cx=cx, cy=cy,
                         size=max(box[2] - box[0], box[3] - box[1], 1), frame=self.frame_no)
            shown.append((box, cls))
            s = self.stats.setdefault(tid, {"bad": 0, "ok": 0, "bad_conf": 0.0, "ok_conf": 0.0, "alerted": False})
            key = "bad" if cls == NO_HELMET else "ok"
            s[key] += 1
            s[key + "_conf"] += conf
            confirmed = s["bad"] >= a.min_hits or (cls == NO_HELMET and conf >= a.single_conf)   # one very sure sighting is enough
            if not s["alerted"] and confirmed and s["bad_conf"] > s["ok_conf"]:
                s["alerted"] = True
                self.alerts += 1
                self.memory[tid] = dict(cx=(box[0] + box[2]) / 2, cy=(box[1] + box[3]) / 2, vx=0.0, vy=0.0,
                                        size=max(box[2] - box[0], box[3] - box[1], 1), frame=self.frame_no)
                if not (recently_alerted(box, self.recent, now=self.clock()) or self._is_repeat(box, tid, visible)):
                    fresh.append((box, tid, conf))
        self.alerts_sent += len(fresh)
        if fresh:
            self.recent.append((self.clock(), fresh))
        for old in [k for k, m in self.memory.items() if self.frame_no - m["frame"] > 10]:
            del self.memory[old]
        if len(self.stats) > 5000:    # a 24/7 worker must not grow without bound: forget the oldest tracks
            for old in sorted(self.stats)[:2500]:
                del self.stats[old]
        return shown, fresh


def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    ap = argparse.ArgumentParser()
    ap.add_argument("--camera-id", type=int, help="camera saved in the admin panel (Cameras page)")
    ap.add_argument("--url", help="RTSP URL, instead of --camera-id")
    ap.add_argument("--name", default="Camera 1")
    ap.add_argument("--imgsz", type=int, default=768, help="whole-frame size; 768 is 2x faster than 960 with the same coverage (training/eval_replay.py)")
    ap.add_argument("--conf", type=float, default=0.5, help="0.5 gave the best precision/recall balance on CCTV clips")
    ap.add_argument("--min-hits", type=int, default=2, help="frames a person must be seen without helmet")
    ap.add_argument("--dedup-dist", type=float, default=1.2,
                    help="a 'new' head within this many head-widths of where an alerted one should be now counts as the same person")
    ap.add_argument("--dedup-gap", type=int, default=3, help="...if that person was last seen at most this many analysed frames ago")
    ap.add_argument("--single-conf", type=float, default=0.55,
                    help="a person seen once without helmet at this confidence or more is flagged at once (2.0 = never)")
    ap.add_argument("--tracker", choices=["simple", "bytetrack"], default="simple")
    ap.add_argument("--tracker-gate", type=float, default=1.5, help="simple tracker: largest move between frames, in head widths")
    ap.add_argument("--min-box", type=int, default=16, help="ignore heads smaller than this many pixels")
    ap.add_argument("--max-fps", type=float, default=3.0)
    ap.add_argument("--vehicle-imgsz", type=int, default=640)
    ap.add_argument("--crop-every", type=int, default=5,
                    help="look closely at every motorcycle only on every Nth analysed frame (the cheap frames in between run ~5x faster)")
    ap.add_argument("--crop-imgsz", type=int, default=512)
    ap.add_argument("--no-classifier", action="store_true", help="skip the head-crop classifier second opinion")
    ap.add_argument("--cls-threshold", type=float, default=0.85, help="how sure the classifier must be to overrule the detector")
    ap.add_argument("--no-crops", action="store_true", help="skip the extra look at every motorcycle (faster)")
    ap.add_argument("--all-heads", action="store_true",
                    help="alert for any head without helmet (pedestrians and cyclists too); default: motorcycle riders only")
    ap.add_argument("--no-telegram", action="store_true", help="local mode only: save events, do not send")
    ap.add_argument("--local", action="store_true", help="use this machine's database and Telegram keys (testing)")
    args = ap.parse_args()

    sink = tg = None
    args.local = args.local or not os.getenv("CCTV_SERVER_URL")
    if args.local:
        from db.database import SessionLocal
        from db.models import Camera
        if args.camera_id:
            with SessionLocal() as db:
                cam = db.get(Camera, args.camera_id)
            if not cam:
                raise SystemExit(f"No camera with id {args.camera_id}")
            if not cam.is_active:
                raise SystemExit(f"Camera '{cam.name}' is paused in the admin panel")
            args.url, args.name = cam.rtsp_url, cam.name
        elif not args.url:
            raise SystemExit("Give --camera-id or --url")
        tg = None if args.no_telegram else Telegram()
    else:
        key = os.getenv("CCTV_WORKER_KEY", "").strip()
        if not key or not args.camera_id:
            raise SystemExit("Remote mode needs CCTV_WORKER_KEY in .env and --camera-id")
        sink = RemoteSink(os.environ["CCTV_SERVER_URL"], key)
        while True:
            cam = sink.camera(args.camera_id)
            if cam["is_active"]:
                break
            print(f"camera '{cam['name']}' is paused in the admin panel, checking again in 60 s", flush=True)
            time.sleep(60)
        args.url, args.name = cam["rtsp_url"], cam["name"]
    args.sink = sink

    CCTV_DIR.mkdir(parents=True, exist_ok=True)
    analyzer = FrameAnalyzer(args)
    src = LatestFrame(args.url)
    if sink:
        start_heartbeat(sink, src, args.name)
    last_stamp, count, t_report = 0.0, 0, time.time()
    print(f"monitoring '{args.name}' ({'remote' if sink else 'local'} mode, imgsz {args.imgsz}); Ctrl+C to stop", flush=True)

    try:
        while True:
            frame, stamp = src.get()
            if frame is None or stamp == last_stamp:
                time.sleep(0.05)
                continue
            last_stamp = stamp
            t0 = time.time()
            shown, fresh = analyzer.analyze(frame)
            if fresh:
                alert(frame, shown, fresh, args, tg)
            count += 1
            if time.time() - t_report > 30:
                print(f"{count} frames analysed, {analyzer.alerts_sent} alerts sent so far", flush=True)
                t_report = time.time()
            time.sleep(max(0.0, 1.0 / args.max_fps - (time.time() - t0)))
    except KeyboardInterrupt:
        print("stopped", flush=True)
    finally:
        src.stop = True


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def find_heads(model, frame, vehicles, args, use_crops=True):
    """Helmet-model detections as (cls, conf, box). Besides the whole frame, the model also looks at an
    enlarged crop around every motorcycle, where riders' heads are much bigger. On the Myanmar test clips
    this raised the share of no-helmet riders caught from 0.69 to 0.86 (training/eval_pipeline.py)."""
    h, w = frame.shape[:2]
    r = model.predict(frame, imgsz=args.imgsz, conf=args.conf, verbose=False)[0]
    dets = [(int(c), float(s), tuple(b)) for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
    if use_crops and not args.no_crops:
        crops, origins = [], []
        for vcls, v in vehicles:
            if vcls != MOTORCYCLE:
                continue
            bw, bh = v[2] - v[0], v[3] - v[1]
            x1, y1 = max(0, int(v[0] - 0.5 * bw)), max(0, int(v[1] - 2.5 * bh))
            x2, y2 = min(w, int(v[2] + 0.5 * bw)), min(h, int(v[3] + 0.3 * bh))
            if x2 - x1 < 20 or y2 - y1 < 20:
                continue
            if getattr(args, "adaptive_crops", False):    # the whole-frame pass already found a head on this bike: no second look
                cx0, cx1, cy0, cy1 = v[0] - 0.25 * bw, v[2] + 0.25 * bw, v[1] - 2.2 * bh, v[1] + 0.6 * bh
                if any(cx0 <= (d[2][0] + d[2][2]) / 2 <= cx1 and cy0 <= (d[2][1] + d[2][3]) / 2 <= cy1 for d in dets):
                    continue
            crops.append(frame[y1:y2, x1:x2])
            origins.append((x1, y1))
        if crops:    # one batched call is cheaper than one call per motorcycle
            for cr, (x1, y1) in zip(model.predict(crops, imgsz=args.crop_imgsz, conf=args.conf, verbose=False), origins):
                for b, c, s in zip(cr.boxes.xyxy.tolist(), cr.boxes.cls.tolist(), cr.boxes.conf.tolist()):
                    dets.append((int(c), float(s), (b[0] + x1, b[1] + y1, b[2] + x1, b[3] + y1)))
    keep = []
    for d in sorted(dets, key=lambda d: -d[1]):      # same head seen twice: keep the more confident
        if all(_iou(d[2], k[2]) < 0.5 for k in keep):
            keep.append(d)
    return keep


def refine_heads(cmodel, frame, heads, threshold):
    """Second opinion on every head from the crop classifier (it learned CCTV caps/hats/helmets): a 'helmet' the
    classifier is sure is not one becomes no_helmet, and a 'no_helmet' it is sure is a helmet becomes helmet.
    On 299 Myanmar test bikes: recall 0.71 -> 0.74, false alarms 25 -> 23, precision 0.89 -> 0.91 (training/eval_cls.py)."""
    crops, idx = [], []
    for i, (_, _, b) in enumerate(heads):
        x1, y1, x2, y2 = (int(v) for v in b)
        m = int(0.15 * max(x2 - x1, y2 - y1))
        crop = frame[max(0, y1 - m):y2 + m, max(0, x1 - m):x2 + m]
        if crop.size:
            crops.append(crop)
            idx.append(i)
    if not crops:
        return heads
    no_idx = [k for k, v in cmodel.names.items() if v == "no_helmet"][0]
    out = list(heads)
    for i, r in zip(idx, cmodel.predict(crops, imgsz=96, verbose=False)):
        p_no = float(r.probs.data[no_idx])
        cls, conf, box = heads[i]
        if cls == HELMET and p_no >= threshold:
            out[i] = (NO_HELMET, p_no, box)
        elif cls == NO_HELMET and p_no <= 1 - threshold:
            out[i] = (HELMET, 1 - p_no, box)
    return out


def track_heads(tracker, heads, frame):
    """Give each head a stable id with ByteTrack. Yields (box, track_id, cls, conf)."""
    if heads:
        data = np.array([[*b, s, c] for c, s, b in heads], dtype=np.float32)
    else:
        data = np.zeros((0, 6), dtype=np.float32)
    out = tracker.update(Boxes(data, frame.shape[:2]), frame)
    seen = set()
    for row in out:
        seen.add(int(row[4]))
        yield [float(v) for v in row[:4]], int(row[4]), int(row[6]), float(row[5])
    # ByteTrack keeps a head it has just met "tentative" and only reports it after a second match. At one analysed
    # frame per second fast riders often never get that second match and would be invisible, so report them now.
    for st in tracker.tracked_stracks:
        if not st.is_activated and st.frame_id == tracker.frame_id and st.track_id not in seen:
            yield [float(v) for v in st.xyxy], int(st.track_id), int(st.cls), float(st.score)


class SimpleTracker:
    """Head tracker for a few analysed frames per second.

    ByteTrack matches by box overlap, which is zero when a rider moved several head-widths between two
    frames; the same person then gets a new id each time and is reported again and again. This tracker matches
    by distance in head-widths (with the speed seen last time), so fast riders keep their id. Every detection
    is reported at once, a new one under a new id."""

    def __init__(self, gate=3.0, max_missed=3):
        self.gate, self.max_missed, self.next_id, self.tracks = gate, max_missed, 1, {}

    def update(self, heads):
        dets = []
        for cls, conf, b in heads:
            w, h = b[2] - b[0], b[3] - b[1]
            dets.append((cls, conf, b, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(w, h)))
        pairs = []
        for tid, t in self.tracks.items():
            px, py = t["cx"] + t["vx"], t["cy"] + t["vy"]
            for i, (cls, conf, b, cx, cy, size) in enumerate(dets):
                ratio = size / max(t["size"], 1)
                if not 0.5 <= ratio <= 2.0:
                    continue
                dist = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5 / max(size, t["size"])
                dist = min(dist, ((cx - t["cx"]) ** 2 + (cy - t["cy"]) ** 2) ** 0.5 / max(size, t["size"]))
                if dist <= self.gate:
                    pairs.append((dist, tid, i))
        pairs.sort()
        existing = list(self.tracks)
        used_t, used_d, out = set(), set(), []
        for dist, tid, i in pairs:
            if tid in used_t or i in used_d:
                continue
            used_t.add(tid); used_d.add(i)
            cls, conf, b, cx, cy, size = dets[i]
            t = self.tracks[tid]
            t.update(vx=cx - t["cx"], vy=cy - t["cy"], cx=cx, cy=cy, size=size, missed=0)
            out.append((list(b), tid, cls, conf))
        for i, (cls, conf, b, cx, cy, size) in enumerate(dets):
            if i in used_d:
                continue
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = dict(cx=cx, cy=cy, vx=0.0, vy=0.0, size=size, missed=0)
            out.append((list(b), tid, cls, conf))
        for tid in existing:             # tracks not seen this time age; forget them after max_missed frames
            if tid not in used_t:
                self.tracks[tid]["missed"] += 1
                if self.tracks[tid]["missed"] > self.max_missed:
                    del self.tracks[tid]
        return out


def nearest_vehicle(head, vehicles):
    """Which vehicle is this head riding? Returns BICYCLE, MOTORCYCLE or None.

    A rider's head sits above the vehicle box (up to ~2 vehicle heights over its top edge) and roughly
    within its width. Of the vehicles that fit, the one whose top-centre is closest to the head wins,
    so a cyclist next to a motorcycle is not mistaken for a motorcycle rider.
    """
    cx, cy = (head[0] + head[2]) / 2, (head[1] + head[3]) / 2
    best, best_d = None, None
    for cls, v in vehicles:
        bw, bh = max(v[2] - v[0], 1), max(v[3] - v[1], 1)
        if not (v[0] - 0.25 * bw <= cx <= v[2] + 0.25 * bw and v[1] - 2.2 * bh <= cy <= v[1] + 0.6 * bh):
            continue
        d = (((cx - (v[0] + v[2]) / 2) / bw) ** 2 + ((cy - v[1]) / bh) ** 2) ** 0.5
        if best_d is None or d < best_d:
            best, best_d = (cls, v), d
    return best


def is_rider_head(head, vehicles):
    """True for a head that sits on a motorcycle and has a believable size. Enlarged crops of far bikes
    sometimes make the model box a whole rider+bike as one giant 'head' (a false alarm); those are rejected.
    On the Myanmar clips this size check cut stray detections from 158 to 6 (training/eval_pipeline.py)."""
    near = nearest_vehicle(head, vehicles)
    if near is None or near[0] != MOTORCYCLE:
        return False
    v = near[1]
    hw, hh = head[2] - head[0], head[3] - head[1]
    return hh <= 0.6 * (v[3] - v[1]) and hw <= 0.7 * (v[2] - v[0]) and 0.6 <= hh / max(hw, 1) <= 2.2


def recently_alerted(box, recent, seconds=4.0, now=None):
    """True if the very same head was alerted a moment ago (the tracker may have given it a new id).
    Deliberately tight (under 0.6 head widths apart): a rider and the passenger behind them sit only 1-2 head
    widths apart and must each get their own alert."""
    now = time.time() if now is None else now
    recent[:] = [(t, f) for t, f in recent if now - t < seconds]
    cx, cy, w = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, max(box[2] - box[0], 1)
    for _, fresh in recent:
        for b, _, _ in fresh:
            if abs((b[0] + b[2]) / 2 - cx) < 0.6 * w and abs((b[1] + b[3]) / 2 - cy) < 0.6 * w:
                return True
    return False


def alert(frame, shown, fresh, args, tg):
    """One photo + one message per frame: every rider head is drawn (red = no helmet, green = helmet) and
    the newly confirmed people get a thicker box."""
    now = datetime.now()
    img = frame.copy()
    for box, cls in shown:
        x1, y1, x2, y2 = (int(v) for v in box)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255) if cls == NO_HELMET else (0, 180, 0), 2)
    for box, _, _ in fresh:
        x1, y1, x2, y2 = (int(v) for v in box)
        cv2.rectangle(img, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (0, 0, 255), 5)
    tid, conf = fresh[0][1], max(c for _, _, c in fresh)
    n = len(fresh)
    in_view = sum(1 for _, c in shown if c == NO_HELMET)
    label = f"{n} new without helmet | in view: {in_view} no helmet, {len(shown) - in_view} helmet"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
    cv2.rectangle(img, (0, img.shape[0] - th - 24), (tw + 20, img.shape[0]), (0, 0, 0), -1)
    cv2.putText(img, label, (10, img.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    jpeg = buf.tobytes()
    if args.sink:    # remote mode: the server saves it and sends the Telegram message
        sent = args.sink.event(jpeg, args.camera_id, args.name, tid, conf, n)
        if not sent:   # no internet / server down: keep it and retry from the heartbeat thread
            OUTBOX.mkdir(parents=True, exist_ok=True)
            stem = OUTBOX / f"{now:%Y%m%d_%H%M%S}_{tid}"
            stem.with_suffix(".jpg").write_bytes(jpeg)
            stem.with_suffix(".json").write_text(json.dumps(
                {"camera_id": args.camera_id, "name": args.name, "track_id": tid, "conf": conf, "people": n}), encoding="utf-8")
        print(f"ALERT {n} people, conf {conf:.2f} uploaded={sent}", flush=True)
        return
    from db.database import SessionLocal
    from db.models import CctvEvent
    path = CCTV_DIR / f"{now:%Y%m%d_%H%M%S}_{tid}.jpg"
    path.write_bytes(jpeg)
    caption = (f"{n} {'person' if n == 1 else 'people'} without helmet\nCamera: {args.name}\n"
               f"Time: {now:%d %b %Y %H:%M:%S}\nConfidence: {conf:.0%}")
    sent = tg.photo(path, caption) if tg else False
    try:
        with SessionLocal() as db:
            db.add(CctvEvent(camera_id=args.camera_id, camera_name=args.name, track_id=tid, confidence=conf,
                             photo=path.name, telegram_sent=sent))
            db.commit()
    except Exception as e:   # keep monitoring even if the database is briefly down; the photo is still on disk
        print("could not save event to database:", type(e).__name__, flush=True)
    print(f"ALERT {n} people, conf {conf:.2f} sent={sent} -> {path.name}", flush=True)


if __name__ == "__main__":
    main()




