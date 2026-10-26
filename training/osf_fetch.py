"""Download a large OSF file quickly: resume what exists, fetch the rest in parallel byte ranges, verify the checksum.

Usage: python -I training/osf_fetch.py <osf_download_guid> <dest_file> <expected_size> <md5>
Example: python -I training/osf_fetch.py 6h5ka data_helmet_myanmar/part_7.zip 1092842740 <md5>
A single connection to OSF storage is slow (~100 KB/s); several ranges at once are ~10x faster.
"""
import hashlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

guid, dest, size, md5 = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4].lower()
url = f"https://osf.io/download/{guid}/"
SEGMENT = 48 * 1024 * 1024
WORKERS = 4      # 8 parallel ranges worked for one 1 GB file, but OSF answered 502 when pulling several GB

have = dest.stat().st_size if dest.exists() else 0
have = min(have, size)
print(f"already have {have / 1e6:.0f} MB of {size / 1e6:.0f} MB", flush=True)

segments = []
pos = have
while pos < size:
    end = min(pos + SEGMENT, size) - 1
    segments.append((pos, end))
    pos = end + 1
tmp = dest.parent / (dest.name + ".segments")
tmp.mkdir(exist_ok=True)


def fetch(i_seg):
    i, (a, b) = i_seg
    out = tmp / f"{i:04d}.bin"
    if out.exists() and out.stat().st_size == b - a + 1:
        return i
    for attempt in range(6):
        r = subprocess.run(["curl.exe", "-L", "-s", "-f", "-r", f"{a}-{b}", "-o", str(out), url])
        if r.returncode == 0 and out.exists() and out.stat().st_size == b - a + 1:
            return i
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"segment {i} ({a}-{b}) failed")


t0 = time.time()
done = 0
with ThreadPoolExecutor(WORKERS) as pool:
    for _ in pool.map(fetch, list(enumerate(segments))):
        done += 1
        if done % 4 == 0 or done == len(segments):
            got = sum(p.stat().st_size for p in tmp.glob("*.bin"))
            print(f"{done}/{len(segments)} segments, {(have + got) / 1e6:.0f} MB, {got / 1e6 / (time.time() - t0):.2f} MB/s", flush=True)

with open(dest, "ab") as f:
    f.truncate(have)
    for i in range(len(segments)):
        f.write((tmp / f"{i:04d}.bin").read_bytes())
for p in tmp.glob("*.bin"):
    p.unlink()
tmp.rmdir()

assert dest.stat().st_size == size, f"size mismatch: {dest.stat().st_size} != {size}"
h = hashlib.md5()
with open(dest, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("md5 match:", h.hexdigest() == md5, flush=True)
sys.exit(0 if h.hexdigest() == md5 else 1)
