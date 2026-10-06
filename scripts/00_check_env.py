"""Task 00: check Python, packages, data paths and free disk. Prints OK / PROBLEM lines only."""
import argparse, importlib, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="config.yaml")
cfg = load_config(ap.parse_args().config)

def say(ok, msg):
    print(("OK      " if ok else "PROBLEM ") + msg)

v = sys.version_info
say(v >= (3, 10), f"Python {v.major}.{v.minor}.{v.micro} (3.10 or 3.11 recommended)")
for pkg in ["pydicom", "numpy", "pandas", "openpyxl", "PIL", "cv2", "tqdm", "yaml"]:
    try:
        importlib.import_module(pkg)
        say(True, f"package {pkg}")
    except ImportError:
        say(False, f"package {pkg} missing -> pip install -r requirements-local.txt")

say(cfg["dicom_root"].is_dir(), f"DICOM folder: {cfg['dicom_root']}")
if cfg["dicom_root"].is_dir():
    n = sum(1 for _ in cfg["dicom_root"].rglob("*.dcm"))
    say(n > 5000, f"{n} .dcm files found (expected about 5,203)")
    pats = [p.name for p in cfg["dicom_root"].iterdir() if p.is_dir()]
    print(f"        patient folders: {len(pats)}  D1-*: {sum(p.startswith('D1') for p in pats)}"
          f"  D2-*: {sum(p.startswith('D2') for p in pats)}")
say(cfg["metadata_root"].is_dir(), f"metadata folder: {cfg['metadata_root']}")
if cfg["metadata_root"].is_dir():
    print("        contains:", [p.name for p in cfg["metadata_root"].iterdir()][:10])
x = Path(cfg.get("clinical_xlsx", ""))
say(x.is_file(), f"clinical xlsx: {x}")

free_gb = shutil.disk_usage(Path(".").resolve().anchor).free / 1e9
say(free_gb > 15, f"free disk on this drive: {free_gb:.1f} GB (need > 15 GB)")
