"""Builds helmet_finetune_india.zip for training/finetune_cctv_colab.ipynb (the notebook adds it by itself when it is in Drive):
  india/train/{images,labels}   Indian road photos with head labels (make_indian_labels.py)
  india/val/{images,labels}     held-out Indian photos for the old-vs-new check in cell 5
Usage: python -I training/build_india_zip.py   -> E:\\helmet_detection\\helmet_finetune_india.zip
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "training" / "_exp" / "finetune_india"
OUT = ROOT / "helmet_finetune_india.zip"
counts = {}
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_STORED) as z:
    for split in ("train", "val"):
        n = 0
        for img in sorted((SRC / split / "images").glob("*.jpg")):
            lab = SRC / split / "labels" / (img.stem + ".txt")
            if lab.is_file():
                z.write(img, f"india/{split}/images/{img.name}")
                z.write(lab, f"india/{split}/labels/{lab.name}")
                n += 1
        counts[split] = n
    z.writestr("INDIA_README.txt",
               "Photos: Kaggle 'master_traffic_violation_dataset' (Indian roads, Roboflow export; check the licence on its Kaggle page before sharing).\n"
               "Labels: head boxes made by our detector inside the dataset's rider boxes, each given the rider's label: 0 = helmet, 1 = no_helmet.\n"
               "Riders without a believable head were skipped. val = the dataset's valid + test splits; never trained on.\n")
print(counts, "->", OUT, f"{OUT.stat().st_size / 1e6:.0f} MB")
