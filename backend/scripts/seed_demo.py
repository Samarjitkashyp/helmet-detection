"""Fill the database with FAKE demo data so the admin panel has something to show.

Demo rows use @demo.local emails and filenames starting with 'demo_'. Remove them with:
    python -I scripts/seed_demo.py --clear
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402

import config  # noqa: E402
from core.security import hash_password  # noqa: E402
from db.database import Base, SessionLocal, engine  # noqa: E402
from db.models import Detection, User, Video  # noqa: E402

DEMO_DIR = config.RESULTS_DIR / "demo"


def clear(db):
    ids = db.scalars(select(Video.id).where(Video.filename.like("demo\\_%", escape="\\"))).all()
    if ids:
        db.execute(delete(Detection).where(Detection.video_id.in_(ids)))
        db.execute(delete(Video).where(Video.id.in_(ids)))
    db.execute(delete(User).where(User.email.like("%@demo.local")))
    db.commit()


def placeholder(path: Path, label: str, conf: float):
    img = np.full((180, 288, 3), 60, dtype=np.uint8)
    color = (60, 60, 220) if label == "no_helmet" else (60, 180, 60)
    cv2.rectangle(img, (80, 30), (200, 150), color, 3)
    cv2.putText(img, f"{label} {conf:.2f}", (84, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(img, "DEMO", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.imwrite(str(path), img)


def main():
    rng = random.Random(7)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        clear(db)
        if "--clear" in sys.argv:
            print("Demo data removed.")
            return
        DEMO_DIR.mkdir(parents=True, exist_ok=True)
        users = []
        for i, name in enumerate(["Rahul", "Priya", "Amit", "Neha"], 1):
            u = User(name=name, email=f"{name.lower()}@demo.local", password_hash=hash_password("demo-not-a-login"),
                     role="user", is_active=(name != "Amit"))
            db.add(u)
            users.append(u)
        db.flush()
        n = 0
        for i in range(14):
            when = datetime.utcnow() - timedelta(days=rng.randint(0, 13), hours=rng.randint(0, 20))
            status = rng.choices(["done", "failed", "processing"], [10, 1, 1])[0]
            v = Video(user_id=rng.choice(users).id, filename=f"demo_video_{i + 1}.mp4", original_path="demo",
                      status=status, duration_seconds=rng.uniform(15, 110), uploaded_at=when,
                      processed_at=when + timedelta(minutes=3) if status == "done" else None,
                      error="demo: could not open video file" if status == "failed" else None)
            db.add(v)
            db.flush()
            if status != "done":
                continue
            for _ in range(rng.randint(2, 7)):
                label = rng.choices(["no_helmet", "helmet"], [6, 4])[0]
                conf = rng.uniform(0.5, 0.97)
                n += 1
                rel = f"demo/det_{n}.jpg"
                placeholder(config.RESULTS_DIR / rel, label, conf)
                db.add(Detection(video_id=v.id, frame_number=rng.randint(1, 3000),
                                 timestamp_seconds=rng.uniform(0, v.duration_seconds), label=label, confidence=conf,
                                 bbox_x1=80, bbox_y1=30, bbox_x2=200, bbox_y2=150, screenshot_path=rel,
                                 is_false_positive=rng.random() < 0.1, created_at=when))
        db.commit()
        print(f"Demo data added ({n} detections).")


if __name__ == "__main__":
    main()
