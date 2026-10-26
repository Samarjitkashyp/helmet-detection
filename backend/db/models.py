from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="user")  # user | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    videos: Mapped[list["Video"]] = relationship(back_populates="user")

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_path: Mapped[str] = mapped_column(Text)
    annotated_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing | done | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="videos")
    detections: Mapped[list["Detection"]] = relationship(back_populates="video", cascade="all, delete-orphan")

    def __str__(self):
        return f"#{self.id} {self.filename}"


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    frame_number: Mapped[int] = mapped_column(Integer)
    timestamp_seconds: Mapped[float] = mapped_column(Float)
    label: Mapped[str] = mapped_column(String(20))  # helmet | no_helmet
    confidence: Mapped[float] = mapped_column(Float)
    bbox_x1: Mapped[float] = mapped_column(Float)
    bbox_y1: Mapped[float] = mapped_column(Float)
    bbox_x2: Mapped[float] = mapped_column(Float)
    bbox_y2: Mapped[float] = mapped_column(Float)
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    video: Mapped[Video] = relationship(back_populates="detections")

    def __str__(self):
        return f"#{self.id} {self.label}"


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    rtsp_url: Mapped[str] = mapped_column(Text)   # may contain camera credentials: admin-only, never shown in full
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __str__(self):
        return self.name


class CctvEvent(Base):
    __tablename__ = "cctv_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    camera_name: Mapped[str] = mapped_column(String(100))
    track_id: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    photo: Mapped[str | None] = mapped_column(String(200), nullable=True)   # file name inside storage/cctv
    telegram_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    camera: Mapped[Camera | None] = relationship()

    def __str__(self):
        return f"#{self.id} {self.camera_name}"


class PushDevice(Base):
    """A phone that asked for push notifications about CCTV events (FCM registration token)."""
    __tablename__ = "push_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(300), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))

    def __str__(self):
        return self.key


DEFAULT_SETTINGS = {
    "confidence_threshold": "0.4",  # measured on held-out images: best F1 balance for no_helmet (see training/eval_settings.py)
    "frame_skip": "2",
    "max_video_seconds": "120",
    "min_box_px": "40",        # ignore people whose box is shorter than this (too far to judge)
    "min_track_hits": "3",     # a person must be seen in at least this many checked frames
    "infer_imgsz": "640",      # YOLO input size; larger sees smaller/farther heads but is slower
}
