"""Build a looping CCTV-style test video from the extracted Myanmar HELMET clips (JPG sequences).

Usage: python -I training/make_test_loop.py
Reads data_helmet_myanmar/clips/<clip>/<n>.jpg, writes data_helmet_myanmar/video/test_loop.mp4 (10 fps, H.264).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "data_helmet_myanmar" / "clips"
OUT = ROOT / "data_helmet_myanmar" / "video"
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
OUT.mkdir(parents=True, exist_ok=True)

MAX_CLIPS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
all_clips = sorted((p for p in CLIPS.iterdir() if p.is_dir()), key=lambda p: int(re.sub(r"\D", "", p.name)))
step = max(1, len(all_clips) // MAX_CLIPS)
parts = []
for clip in all_clips[::step][:MAX_CLIPS]:     # an even spread over the whole dataset
    frames = sorted(clip.glob("*.jpg"), key=lambda p: int(re.sub(r"\D", "", p.stem)))
    lst = OUT / f"{clip.name}.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration 0.1\n" for f in frames), encoding="utf-8")
    mp4 = OUT / f"{clip.name}.mp4"
    subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", "fps=10,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-g", "20", str(mp4)], check=True)
    parts.append(mp4)
    print(clip.name, len(frames), "frames", flush=True)

big = OUT / "list.txt"
big.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(big),
                "-c", "copy", str(OUT / "test_loop.mp4")], check=True)
print("wrote", OUT / "test_loop.mp4")
