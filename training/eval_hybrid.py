"""Hybrid: every frame gets the cheap whole-frame pass, every Nth frame also gets the motorcycle crops.
Built from the two cached variants (same frames), scored with eval_replay's run(). Usage: python -I training/eval_hybrid.py"""
import pickle
import sys
from pathlib import Path

sys.argv = [sys.argv[0], "fast"]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_replay as er

full = er.det                                                          # whole frame + crops (variant fast)
cheap = pickle.load(open(er.ROOT / "training" / "_exp" / "replay_cache_fastnocrops.pkl", "rb"))   # whole frame only

for n in (1, 2, 3, 4, 6, 10 ** 6):
    combined = {}
    for clip in er.clips:
        keys = sorted(k for k in full if k[0] == clip)
        for i, k in enumerate(keys):
            combined[k] = full[k] if i % n == 0 else cheap[k]
    er.det = combined
    label = "crops on every frame" if n == 1 else ("never" if n > 1000 else f"crops on every {n}th frame")
    er.show(f"{label:28} (frames 0.5 s apart)", 5, single_conf=0.55, dedup_dist=1.2, dedup_gap=3)
print("DONE", flush=True)
