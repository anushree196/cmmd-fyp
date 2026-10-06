"""Task 05: build the two folders that get uploaded to Kaggle as private datasets.

    data/kaggle_upload/   -> dataset "cmmd-png1024": png1024/, masks1024/, index/, splits/, manifest.json
    data/kaggle_code/     -> dataset "cmmd-code":    src/, requirements-train.txt
                             (so Kaggle notebooks can import our code without a GitHub token)

Each folder also gets the `dataset-metadata.json` that the Kaggle CLI needs. Nothing is uploaded by this
script; the upload is one CLI command, printed at the end. Re-running only copies files that changed.

Usage:
    python scripts/05_package.py --config config.yaml
"""
import argparse, json, shutil, subprocess, sys
from datetime import date
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

SKIP_INDEX = {"png_index_test.csv"}  # left over from the 20-image trial run of task 02


def copy_folder(src, dst, pattern):
    """Copy matching files from src to dst, skipping files that are already there with the same size."""
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.glob(pattern) if p.is_file())
    for p in tqdm(files, desc=f"{src.name}", leave=False):
        out = dst / p.name
        if not (out.exists() and out.stat().st_size == p.stat().st_size):
            shutil.copy2(p, out)
    # remove anything in dst that no longer exists in src, so the upload matches the source exactly
    keep = {p.name for p in files}
    for old in dst.iterdir():
        if old.is_file() and old.name not in keep:
            old.unlink()
    return len(files), sum(p.stat().st_size for p in files)


def write_metadata(folder, username, slug, description):
    """The small JSON file the Kaggle CLI reads. Datasets are private unless created with --public."""
    meta = {"title": slug, "id": f"{username}/{slug}", "licenses": [{"name": "unknown"}],
            "subtitle": description}
    (folder / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)
    user = cfg["kaggle_username"]
    work, h = cfg["work_root"], cfg.get("png_height", 1024)
    repo = Path(__file__).resolve().parent.parent

    # ---- dataset 1: the prepared data
    up = work / "kaggle_upload"
    n_png, b_png = copy_folder(cfg["png_dir"], up / f"png{h}", "*.png")
    n_mask, b_mask = copy_folder(work / f"masks{h}", up / f"masks{h}", "*.png")
    index_files = [p for p in sorted(cfg["index_dir"].glob("*.csv")) if p.name not in SKIP_INDEX]
    (up / "index").mkdir(exist_ok=True)
    for old in (up / "index").iterdir():
        old.unlink()
    for p in index_files:
        shutil.copy2(p, up / "index" / p.name)
    n_split, _ = copy_folder(work / "splits", up / "splits", "*.csv")

    # manifest: the counts a notebook should find, so the upload can be verified on the other side
    s1, s2 = pd.read_csv(work / "splits" / "stage1.csv"), pd.read_csv(work / "splits" / "stage2.csv")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=repo).stdout.strip()
    manifest = {
        "built": str(date.today()), "git_commit": commit, "png_height": h,
        "n_png": n_png, "n_masks": n_mask, "n_index_files": len(index_files), "n_split_files": n_split,
        "pairs_rows": len(pd.read_csv(cfg["index_dir"] / "pairs.csv")),
        "stage1_breasts": len(s1), "stage1_patients": int(s1["patient_id"].nunique()),
        "stage1_per_split": s1["split"].value_counts().to_dict(),
        "stage2_patients": len(s2), "stage2_per_split": s2["split"].value_counts().to_dict(),
        "stage2_has_box_only": int(s2["has_box_only"].sum()),
        "e0_images": len(pd.read_csv(work / "splits" / "stage2_e0_imagewise.csv")),
    }
    (up / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_metadata(up, user, f"cmmd-png{h}", "CMMD mammograms as 1024 px PNGs, TOMPEI lesion masks, index and splits")

    # ---- dataset 2: our code
    code = work / "kaggle_code"
    n_src, _ = copy_folder(repo / "src", code / "src", "*.py")
    shutil.copy2(repo / "requirements-train.txt", code / "requirements-train.txt")
    write_metadata(code, user, "cmmd-code", "Project code (src/) and training requirements for the CMMD notebooks")

    print(f"\n{up}:")
    print(f"  png{h}/    {n_png} files, {b_png / 1e9:.2f} GB")
    print(f"  masks{h}/  {n_mask} files, {b_mask / 1e6:.1f} MB")
    print(f"  index/      {len(index_files)} files: {[p.name for p in index_files]}")
    print(f"  splits/     {n_split} files")
    print(f"  manifest.json: {manifest}")
    print(f"{code}:\n  src/ {n_src} files + requirements-train.txt")
    print("\nUpload (first time):")
    print(f"  kaggle datasets create -p {up} --dir-mode zip")
    print(f"  kaggle datasets create -p {code} --dir-mode zip")
    print('Later updates: kaggle datasets version -p <folder> --dir-mode zip -m "what changed"')


if __name__ == "__main__":
    main()
