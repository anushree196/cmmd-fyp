"""Task 01: scan every DICOM header (no pixels) into data/index/dicom_index.csv and join clinical labels.

Usage:
    python scripts/01_inventory.py --config config.yaml --limit 50   # quick look
    python scripts/01_inventory.py --config config.yaml              # full scan
"""
import argparse, sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pydicom
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config


def get(ds, name):
    v = getattr(ds, name, None)
    return None if v in (None, "") else str(v)


def read_header(path):
    """One row of facts about a DICOM file, read without loading pixels."""
    try:
        ds = pydicom.dcmread(path, stop_before_pixels=True)
    except Exception as e:  # unreadable file: record it instead of crashing the whole scan
        return {"path": str(path), "error": repr(e)}
    view_code = None
    if "ViewCodeSequence" in ds and len(ds.ViewCodeSequence):
        view_code = get(ds.ViewCodeSequence[0], "CodeMeaning")
    return {
        "path": str(path),
        "folder_patient": Path(path).parts[-4] if len(Path(path).parts) >= 4 else None,
        "patient_id": get(ds, "PatientID"),
        "study_uid": get(ds, "StudyInstanceUID"),
        "series_uid": get(ds, "SeriesInstanceUID"),
        "sop_uid": get(ds, "SOPInstanceUID"),
        # several tags can hold side and view; keep all, decide in PROGRESS.md which one is reliable
        "image_laterality": get(ds, "ImageLaterality"),
        "laterality": get(ds, "Laterality"),
        "view_position": get(ds, "ViewPosition"),
        "view_code_meaning": view_code,
        "series_description": get(ds, "SeriesDescription"),
        "rows": get(ds, "Rows"),
        "cols": get(ds, "Columns"),
        "bits_stored": get(ds, "BitsStored"),
        "photometric": get(ds, "PhotometricInterpretation"),
        "has_voi_lut": ("VOILUTSequence" in ds) or ("WindowCenter" in ds),
        "manufacturer": get(ds, "Manufacturer"),
        "error": None,
    }


def normalise_view(row):
    text = " ".join(str(row[c] or "") for c in
                    ["view_position", "view_code_meaning", "series_description"]).upper()
    if "MLO" in text or "MEDIO-LATERAL OBLIQUE" in text or "MEDIOLATERAL OBLIQUE" in text:
        return "MLO"
    if "CC" in text or "CRANIO-CAUDAL" in text or "CRANIOCAUDAL" in text:
        return "CC"
    return None


def find_col(df, *names):
    low = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
    for n in names:
        if n in low:
            return low[n]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--limit", type=int, default=0, help="only scan the first N files (testing)")
    args = ap.parse_args()
    cfg = load_config(args.config)

    files = sorted(cfg["dicom_root"].rglob("*.dcm"))
    if args.limit:
        files = files[: args.limit]
    print(f"Scanning {len(files)} DICOM headers with {cfg['num_workers']} workers ...")
    with Pool(cfg["num_workers"]) as pool:
        rows = list(tqdm(pool.imap(read_header, files, chunksize=32), total=len(files)))
    df = pd.DataFrame(rows)

    errors = df[df["error"].notna()]
    df = df[df["error"].isna()].drop(columns="error")
    df["side"] = df["image_laterality"].fillna(df["laterality"])
    df["view"] = df.apply(normalise_view, axis=1)

    # ---- join clinical labels (patient + side). Column names are detected, then printed for checking.
    xlsx = Path(cfg.get("clinical_xlsx", ""))
    if xlsx.is_file():
        clin = pd.read_excel(xlsx)
        print("\nClinical columns:", clin.columns.tolist())
        id_col = find_col(clin, "id1", "id", "patientid")
        side_col = find_col(clin, "leftright", "side", "laterality")
        for c in clin.columns:
            if clin[c].nunique() <= 10:
                print(f"  {c}: {clin[c].value_counts(dropna=False).to_dict()}")
        if id_col and side_col:
            clin = clin.rename(columns={id_col: "patient_id", side_col: "side"})
            clin["patient_id"] = clin["patient_id"].astype(str).str.strip()
            clin["side"] = clin["side"].astype(str).str.strip().str.upper().str[0]
            df = df.merge(clin, on=["patient_id", "side"], how="left", indicator="clinical_match")
            print("\nClinical join:", df["clinical_match"].value_counts().to_dict())
        else:
            print("\nPROBLEM: could not find patient-id / side columns; fix find_col() names and rerun.")
    else:
        print(f"\nClinical xlsx not found at {xlsx}; index saved without labels.")

    out = cfg["index_dir"] / "dicom_index.csv"
    df.to_csv(out, index=False)
    if len(errors):
        errors.to_csv(cfg["index_dir"] / "inventory_errors.csv", index=False)

    # ---- short summary (this is what Claude Code should read, not the CSV)
    print(f"\nSaved {out}  ({len(df)} rows, {len(errors)} unreadable)")
    print("patients:", df["patient_id"].nunique(),
          "| D1:", df["patient_id"].str.startswith("D1").sum(),
          "images | D2:", df["patient_id"].str.startswith("D2").sum(), "images")
    print("side:", df["side"].value_counts(dropna=False).to_dict())
    print("view:", df["view"].value_counts(dropna=False).to_dict())
    print("photometric:", df["photometric"].value_counts(dropna=False).to_dict())
    print("bits_stored:", df["bits_stored"].value_counts(dropna=False).to_dict())
    print("size (rows x cols):", (df["rows"] + "x" + df["cols"]).value_counts().head(5).to_dict())
    print("has VOI LUT/window:", df["has_voi_lut"].value_counts().to_dict())
    print("images per patient:", df.groupby("patient_id").size().describe()[["min", "mean", "max"]].to_dict())


if __name__ == "__main__":
    main()
