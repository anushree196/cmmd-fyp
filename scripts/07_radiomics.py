"""Task 07: radiomics features of every Stage 2 lesion (MLO + real TOMPEI mask), then feature selection on the
TRAINING split only.

Runs on the laptop (pyradiomics installs here from the pinned GitHub commit 8ed579383, same as on Kaggle).

Writes:
    data/features/radiomics_features.csv      one row per Stage 2 breast: all features (box-only shapes empty)
    data/features/radiomics_selected.json     the 20 kept features, settings, versions, fill-in medians
    reports/radiomics/selection_table.csv     every feature and why it was kept or dropped
    reports/radiomics/summary.md              counts and checks

Usage:
    python scripts/07_radiomics.py --config config.yaml --limit 20   # quick test
    python scripts/07_radiomics.py --config config.yaml
"""
import argparse, json, sys
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config
from src import radiomics_features as rf

_extractor = None


def work(rec, png_dir, mask_dir):
    """One lesion (runs in a worker process; each worker builds its own extractor once)."""
    global _extractor
    if _extractor is None:
        _extractor = rf.make_extractor()
    try:
        img = cv2.imread(str(png_dir / rec["png_mlo"]), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mask_dir / rec["mask"]), cv2.IMREAD_GRAYSCALE)
        feats = rf.extract_one(img, mask, rec["scale"], _extractor)
        return {"patient_id": rec["patient_id"], "side": rec["side"], **feats, "error": None}
    except Exception as e:
        return {"patient_id": rec["patient_id"], "side": rec["side"], "error": repr(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cfg = load_config(args.config)
    h = cfg.get("png_height", 1024)
    png_dir, mask_dir = cfg["png_dir"], cfg["work_root"] / f"masks{h}"
    out_dir = cfg["work_root"] / "features"
    rep_dir = Path("reports/radiomics")
    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    s2 = pd.read_csv(cfg["work_root"] / "splits" / "stage2.csv")
    scale = pd.read_csv(cfg["index_dir"] / "png_index.csv").set_index("png")["scale"]
    s2["scale"] = s2["png_mlo"].map(scale)
    if args.limit:
        s2 = s2.sample(args.limit, random_state=cfg["seed"])
    out_csv = out_dir / ("radiomics_features_test.csv" if args.limit else "radiomics_features.csv")

    # ---- 1. extraction (resumable: breasts already in the output file are skipped)
    done = pd.read_csv(out_csv) if out_csv.exists() else pd.DataFrame(columns=["patient_id", "side"])
    todo = s2[~s2.set_index(["patient_id", "side"]).index.isin(done.set_index(["patient_id", "side"]).index)]
    print(f"Stage 2 breasts: {len(s2)} | already extracted: {len(s2) - len(todo)} | to do: {len(todo)}")
    if len(todo):
        with Pool(cfg["num_workers"]) as pool:
            rows = list(tqdm(pool.imap(partial(work, png_dir=png_dir, mask_dir=mask_dir),
                                       todo.to_dict("records"), chunksize=4), total=len(todo)))
        new = pd.DataFrame(rows)
        bad = new[new["error"].notna()]
        if len(bad):
            bad.to_csv(out_dir / "radiomics_errors.csv", index=False)
            print(f"FAILED on {len(bad)} breasts -> {out_dir / 'radiomics_errors.csv'}")
        done = pd.concat([done, new[new["error"].isna()]], ignore_index=True)
    feats = done.drop(columns="error", errors="ignore")
    feat_cols = [c for c in feats.columns if any(c.startswith(k + "_") for k in rf.CLASSES)]

    # box-only lesions: shape features describe the rectangle, not the lesion -> empty
    feats = feats.merge(s2[["patient_id", "side", "split", "subtype", "has_box_only"]], on=["patient_id", "side"])
    feats.loc[feats["has_box_only"], rf.shape_columns(feats)] = np.nan
    feats.to_csv(out_csv, index=False)
    print(f"saved {out_csv}: {len(feats)} breasts x {len(feat_cols)} features")

    # ---- 2. the "Done when" check: shape features must differ between patients (else the mask is wrong)
    real = feats[~feats["has_box_only"]]
    for c in ["shape2D_Perimeter", "shape2D_Sphericity", "shape2D_PixelSurface"]:
        print(f"  {c}: std {real[c].std():.4f} | min {real[c].min():.3f} | median {real[c].median():.3f} | max {real[c].max():.3f}")
        assert real[c].std() > 0, f"{c} is the same for every lesion: the mask is not being used"
    if args.limit:
        return

    # ---- 3. feature selection on TRAIN only
    train_mask = feats["split"] == "train"
    filled, medians = rf.fill_box_only_shapes(feats, train_mask)
    kept, table = rf.select_features(filled[train_mask], feat_cols, "subtype")
    table.to_csv(rep_dir / "selection_table.csv", index=False)
    import radiomics, SimpleITK
    meta = {"selected": kept, "settings": rf.SETTINGS, "classes": rf.CLASSES, "margin_px": rf.MARGIN_PX,
            "detector_mm": rf.DETECTOR_MM, "common_mm": rf.COMMON_MM, "pyradiomics": radiomics.__version__,
            "simpleitk": SimpleITK.Version_VersionString(), "n_features_extracted": len(feat_cols),
            "selection": "train split only: drop near-constant (top value > 95% of rows), rank by mutual "
                         "information with subtype, drop |Spearman r| > 0.9 with a better-ranked feature, keep top 20",
            "box_only_shape_fill_medians_from_train": medians}
    (out_dir / "radiomics_selected.json").write_text(json.dumps(meta, indent=2))
    (rep_dir / "radiomics_selected.json").write_text(json.dumps(meta, indent=2))

    # ---- 4. short report
    lines = ["# Task 07 — radiomics summary", "",
             f"Stage 2 breasts: {len(feats)} (train {int(train_mask.sum())}) | features extracted: {len(feat_cols)} "
             f"| box-only (no shape features): {int(feats['has_box_only'].sum())}", "",
             f"Pixel size before resampling: {feats['pixel_mm'].min():.3f}-{feats['pixel_mm'].max():.3f} mm; all resampled to {rf.COMMON_MM} mm.", "",
             "Lesion size (traced outlines only, mm²): " + str(real["shape2D_PixelSurface"].describe()[["min", "25%", "50%", "75%", "max"]].round(1).to_dict()), "",
             "Decisions on the training split: " + str(table["decision"].str.split(":").str[0].str.split(" \\(").str[0].value_counts().to_dict()), "",
             "| rank | feature | mutual information with subtype (train) |", "|---|---|---|"]
    for i, c in enumerate(kept, 1):
        lines.append(f"| {i} | {c} | {float(table.loc[table['feature'] == c, 'mi'].iloc[0]):.4f} |")
    (rep_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
