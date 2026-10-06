"""Load config.yaml and resolve paths. Every script uses this, so paths live in one place."""
from pathlib import Path
import yaml


def load_config(path="config.yaml"):
    # utf-8-sig = UTF-8 that also tolerates the invisible "BOM" Windows editors sometimes add
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    raw = Path(cfg["raw_root"])
    cfg["dicom_root"] = raw / cfg.get("dicom_dir", "cmmd")
    cfg["metadata_root"] = raw / cfg.get("metadata_dir", "metadata")
    work = Path(cfg.get("work_root", "data"))
    cfg["work_root"] = work
    cfg["index_dir"] = work / "index"
    cfg["png_dir"] = work / f"png{cfg.get('png_height', 1024)}"
    for d in (cfg["index_dir"], cfg["png_dir"], Path("reports")):
        d.mkdir(parents=True, exist_ok=True)
    return cfg
