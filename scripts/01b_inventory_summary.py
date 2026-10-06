"""Task 01 (part b): turn data/index/dicom_index.csv into the counts for the report.

Reads only the index CSV and the clinical xlsx (no DICOMs). Prints the summary and saves the same text to
reports/01_inventory_summary.md.

Usage:
    python scripts/01b_inventory_summary.py --config config.yaml
"""
import argparse, sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

lines = []  # everything we print is also collected here and written to the report


def say(text=""):
    print(text)
    lines.append(text)


def table(title, series):
    """Print a value_counts-style Series as a small markdown table."""
    say(f"\n**{title}**\n")
    say("| value | count |")
    say("|---|---|")
    for k, v in series.items():
        say(f"| {k} | {v} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)

    df = pd.read_csv(cfg["index_dir"] / "dicom_index.csv")
    clin = pd.read_excel(cfg["clinical_xlsx"])
    df["labelled"] = df["clinical_match"] == "both"  # True if this image's breast has a clinical row

    say("# Task 01 — inventory summary")
    say(f"\nImages: {len(df)}  |  patients: {df['patient_id'].nunique()}"
        f"  |  D1 patients: {df.loc[df['patient_id'].str.startswith('D1'), 'patient_id'].nunique()}"
        f"  |  D2 patients: {df.loc[df['patient_id'].str.startswith('D2'), 'patient_id'].nunique()}")

    # ---- 1. which DICOM tags are filled (decides where side and view come from)
    say("\n## 1. DICOM tags for side and view")
    tags = ["image_laterality", "laterality", "view_position", "view_code_meaning", "series_description"]
    say("\n| tag | filled | values |")
    say("|---|---|---|")
    for t in tags:
        say(f"| {t} | {df[t].notna().sum()} / {len(df)} | {df[t].value_counts().head(4).to_dict()} |")
    both = df["image_laterality"].notna() & df["laterality"].notna()
    say(f"\nImageLaterality and Laterality both filled on {both.sum()} images; "
        f"they disagree on {(df.loc[both, 'image_laterality'] != df.loc[both, 'laterality']).sum()}.")
    say(f"Images with no side: {df['side'].isna().sum()}  |  no view: {df['view'].isna().sum()}")
    say(f"Folder name differs from PatientID tag: {(df['folder_patient'] != df['patient_id']).sum()}"
        f"  |  duplicate SOP UIDs: {df['sop_uid'].duplicated().sum()}")

    # ---- 2. image format (matters for the conversion in task 02)
    say("\n## 2. Image format")
    table("bits_stored", df["bits_stored"].value_counts())
    odd = df[df["bits_stored"] != 8]
    say(f"\nNon-8-bit files: {odd[['patient_id', 'side', 'view']].to_dict('records')}")
    table("manufacturer", df["manufacturer"].value_counts(dropna=False))
    say(f"\nAll images are {df['rows'].iloc[0]} x {df['cols'].iloc[0]} (rows x cols): "
        f"{((df['rows'] == df['rows'].iloc[0]) & (df['cols'] == df['cols'].iloc[0])).all()}")

    # ---- 3. the clinical sheet on its own
    say("\n## 3. Clinical sheet")
    say(f"\nColumns: {clin.columns.tolist()}")
    say(f"Rows: {len(clin)} (one row per labelled breast)  |  patients: {clin['ID1'].nunique()}")
    say(f"Duplicate (ID1, LeftRight) rows: {clin.duplicated(['ID1', 'LeftRight']).sum()}")
    rows_per_patient = clin.groupby("ID1").size()
    table("labelled breasts per patient", rows_per_patient.value_counts().sort_index())
    say(f"\nPatients in the sheet but with no DICOMs: {len(set(clin['ID1']) - set(df['patient_id']))}"
        f"  |  patients with DICOMs but not in the sheet: {len(set(df['patient_id']) - set(clin['ID1']))}")
    say(f"Age: min {clin['Age'].min()}, max {clin['Age'].max()}, mean {clin['Age'].mean():.1f}, "
        f"median {clin['Age'].median():.0f}, missing {clin['Age'].isna().sum()}")
    say(f"Patients whose two rows give different ages: {(clin.groupby('ID1')['Age'].nunique() > 1).sum()}")
    mixed = clin.groupby("ID1")["classification"].nunique() > 1
    say(f"Patients with one benign breast and one malignant breast: {mixed.sum()}")
    say(f"Patients whose two breasts have different subtypes: {(clin.groupby('ID1')['subtype'].nunique() > 1).sum()}")
    say(f"Malignant rows with no subtype: {((clin['classification'] == 'Malignant') & clin['subtype'].isna()).sum()}"
        f"  |  benign rows WITH a subtype: {((clin['classification'] == 'Benign') & clin['subtype'].notna()).sum()}")
    clin["cohort"] = clin["ID1"].str[:2]
    say("\n**classification by cohort (rows = breasts)**\n")
    say(pd.crosstab(clin["cohort"], clin["classification"]).to_markdown())
    say("\n**subtype by cohort (rows = breasts)**\n")
    say(pd.crosstab(clin["cohort"], clin["subtype"].fillna("(none)")).to_markdown())

    # ---- 4. images with no clinical row
    say("\n## 4. Images without a clinical label")
    say(f"\nLabelled images: {df['labelled'].sum()}  |  unlabelled images: {(~df['labelled']).sum()}")
    labelled_patients = set(df.loc[df["labelled"], "patient_id"])
    unl = df[~df["labelled"]]
    say(f"Unlabelled images belonging to a patient who has NO labelled image at all: "
        f"{(~unl['patient_id'].isin(labelled_patients)).sum()}")
    say(f"Patients with at least one unlabelled (other-side) breast: {unl['patient_id'].nunique()}")
    table("unlabelled images by cohort", unl["patient_id"].str[:2].value_counts())

    # ---- 5. views per breast (a breast = patient + side)
    say("\n## 5. Images per patient and views per breast")
    table("images per patient", df.groupby("patient_id").size().value_counts().sort_index())
    table("images per (patient, side, view)", df.groupby(["patient_id", "side", "view"]).size().value_counts())
    breast = df.groupby(["patient_id", "side"]).agg(
        n_images=("path", "size"), has_cc=("view", lambda v: "CC" in set(v)),
        has_mlo=("view", lambda v: "MLO" in set(v)), labelled=("labelled", "all")).reset_index()
    breast["both_views"] = breast["has_cc"] & breast["has_mlo"]
    say(f"\nBreasts (patient + side): {len(breast)}  |  with both CC and MLO: {breast['both_views'].sum()}")
    lab = breast[breast["labelled"]]
    say(f"Labelled breasts: {len(lab)}  |  with both CC and MLO: {lab['both_views'].sum()}")

    # ---- 6. class counts per image, per breast and per patient
    say("\n## 6. Class counts")
    L = df[df["labelled"]]
    table("classification, per image (labelled images only)", L["classification"].value_counts())
    table("classification, per breast", clin["classification"].value_counts())
    # patient-level label: malignant if ANY labelled breast is malignant
    pat = clin.groupby("ID1").agg(
        malignant=("classification", lambda c: (c == "Malignant").any()),
        subtype=("subtype", lambda s: s.dropna().iloc[0] if s.notna().any() else None))
    table("classification, per patient (malignant if any breast is malignant)",
          pat["malignant"].map({True: "Malignant", False: "Benign"}).value_counts())
    table("subtype, per image", L["subtype"].value_counts())
    table("subtype, per breast", clin["subtype"].value_counts())
    table("subtype, per patient", pat["subtype"].value_counts())
    say(f"\nPatients with a subtype label: {pat['subtype'].notna().sum()}")
    table("abnormality, per breast", clin["abnormality"].value_counts())

    out = Path("reports") / "01_inventory_summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
