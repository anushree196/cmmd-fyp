"""Task 03 (part 1): read TOMPEI-CMMD's corrected labels and compare them with the original CMMD labels.

Run this BEFORE 03_tompei_masks.py. It reads only spreadsheets and our own index (no images).

Writes:
    data/index/image_sides.csv     one row per image: DICOM side tag, side seen in the pixels, corrected side
    data/index/breast_labels.csv   one row per breast (TOMPEI's 2,601): TOMPEI class + CMMD label and subtype
    reports/03_tompei_labels.md    the comparison counts

Usage:
    python scripts/03_tompei_labels.py --config config.yaml
"""
import argparse, sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

lines = []


def say(text=""):
    print(text)
    lines.append(text)


def other(side):
    return "R" if side == "L" else "L"


def read_tompei_sheets(xlsx):
    """One row per breast from TOMPEI's two sheets (both have 2 or 3 header rows, so columns go by position)."""
    img = pd.read_excel(xlsx, sheet_name="Imaging Diagnosis Details Sheet", header=None, skiprows=2)
    img = img.iloc[:, [0, 1, 2, 3, 4, 5, 21]]
    img.columns = ["patient_id", "side", "t_age", "t_class", "exclusion_reason", "density", "birads"]
    les = pd.read_excel(xlsx, sheet_name="Lesion Details Sheet", header=None, skiprows=3)
    les = les[les[0].notna()].iloc[:, [0, 1, 3, 18]]  # the last row of the sheet is a totals row with no ID
    les.columns = ["patient_id", "side", "n_lesions", "t_note"]
    les["n_lesions"] = les["n_lesions"].astype(int)
    return img.merge(les, on=["patient_id", "side"], how="left")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)
    tompei_dir = Path(cfg["tompei_dir"])
    xlsx = next(tompei_dir.glob("*.xlsx"))

    t = read_tompei_sheets(xlsx)
    clin = pd.read_excel(cfg["clinical_xlsx"]).rename(columns={"ID1": "patient_id", "LeftRight": "side"})
    idx = pd.read_csv(cfg["index_dir"] / "png_index.csv")

    say("# Task 03 — TOMPEI-CMMD labels compared with CMMD")
    say(f"\nTOMPEI sheet: {xlsx.name}")
    say(f"TOMPEI rows (breasts): {len(t)}  |  patients: {t['patient_id'].nunique()}")
    say("\n## 1. TOMPEI classes (per breast)\n")
    say("| class | breasts | meaning (from TOMPEI's README) |")
    say("|---|---|---|")
    meaning = {"Malignant": "confirmed malignant lesion, located on the image",
               "Normal": "normal, OR benign with no identifiable lesion on the image",
               "Benign": "only benign lesions, located on the image",
               "Invisible": "malignant, but the lesion cannot be located on the image",
               "Exclusion": "TOMPEI recommends excluding the breast (reason given)"}
    for k, v in t["t_class"].value_counts().items():
        say(f"| {k} | {v} | {meaning.get(k, '')} |")
    say(f"\nExclusion reasons: {t.loc[t['t_class'] == 'Exclusion', 'exclusion_reason'].value_counts().to_dict()}")
    say(f"Breasts with at least one outlined lesion: {(t['n_lesions'] > 0).sum()}"
        f"  |  outlined lesions in total: {t['n_lesions'].sum()}")

    # ---- 2. which side does each IMAGE really show?
    # side      = the DICOM tag (task 01)
    # side_px   = where the breast sits in the pixels (task 02): right half -> R, left half -> L
    img_sides = idx[["path", "png", "patient_id", "view", "side", "flipped"]].copy()
    img_sides["side_px"] = img_sides["flipped"].map({True: "R", False: "L"})
    img_sides["side_corrected"] = img_sides["side"]
    img_sides["side_fix"] = ""
    disagree = img_sides["side"] != img_sides["side_px"]
    # rule A: a patient has two images of the same view and BOTH tags disagree with the pixels -> tags swapped
    n_bad = img_sides[disagree].groupby(["patient_id", "view"]).size()
    for (pid, view), n in n_bad.items():
        if n == 2:
            m = (img_sides["patient_id"] == pid) & (img_sides["view"] == view)
            img_sides.loc[m, "side_corrected"] = img_sides.loc[m, "side_px"]
            img_sides.loc[m, "side_fix"] = "tags of the two images swapped (pixels)"
    # rule B: TOMPEI lists this patient under a different side than the DICOM tags ("Reversed left and right")
    tag_sides = img_sides.groupby("patient_id")["side"].agg(set)
    tompei_sides = t.groupby("patient_id")["side"].agg(set)
    for pid in tag_sides.index[tag_sides != tompei_sides]:
        if len(tompei_sides[pid]) == 1:
            m = img_sides["patient_id"] == pid
            img_sides.loc[m, "side_corrected"] = next(iter(tompei_sides[pid]))
            img_sides.loc[m, "side_fix"] = "TOMPEI: reversed left and right"
    changed = img_sides[img_sides["side_fix"] != ""]
    left_alone = img_sides[disagree & (img_sides["side_fix"] == "")]
    say("\n## 2. Image sides\n")
    say(f"Images whose DICOM side tag disagrees with the pixels: {disagree.sum()}")
    say(f"Images whose side was corrected: {len(changed)} ({changed['patient_id'].nunique()} patients)")
    say("\n| patient | view | DICOM tag | corrected | why |")
    say("|---|---|---|---|---|")
    for _, r in changed.sort_values(["patient_id", "view", "side"]).iterrows():
        say(f"| {r['patient_id']} | {r['view']} | {r['side']} | {r['side_corrected']} | {r['side_fix']} |")
    say(f"\nTag disagrees with pixels but left unchanged (image looks stored mirrored; tag kept): "
        f"{(left_alone['patient_id'] + ' ' + left_alone['side'] + ' ' + left_alone['view']).tolist()}")
    dup = img_sides.duplicated(["patient_id", "side_corrected", "view"]).sum()
    ours = set(map(tuple, img_sides[["patient_id", "side_corrected"]].drop_duplicates().values))
    theirs = set(map(tuple, t[["patient_id", "side"]].values))
    say(f"After correction: duplicate (patient, side, view) = {dup}  |  our breasts = {len(ours)}, "
        f"TOMPEI breasts = {len(theirs)}, in both = {len(ours & theirs)}")
    img_sides.drop(columns="flipped").to_csv(cfg["index_dir"] / "image_sides.csv", index=False)

    # ---- 3. which BREAST does each CMMD label belong to?
    # CMMD has one row per labelled breast. TOMPEI found a few rows attached to the wrong side. A CMMD row is
    # moved to the other breast when TOMPEI has no such side for the patient, or when TOMPEI calls that side
    # Normal, the patient has only this one CMMD row, and TOMPEI found something on the other side.
    t_class = t.set_index(["patient_id", "side"])["t_class"]
    rows_per_patient = clin.groupby("patient_id").size()
    label_side, moved = [], []
    for _, r in clin.iterrows():
        here = t_class.get((r["patient_id"], r["side"]))
        there = t_class.get((r["patient_id"], other(r["side"])))
        move = here is None or (here == "Normal" and rows_per_patient[r["patient_id"]] == 1
                                and there is not None and there != "Normal")
        label_side.append(other(r["side"]) if move else r["side"])
        if move:
            moved.append((r["patient_id"], r["side"], other(r["side"]), r["classification"],
                          r["subtype"] if pd.notna(r["subtype"]) else "-", here or "(no such side)", there))
    clin["label_side"] = label_side
    say("\n## 3. CMMD labels that belong to the other breast\n")
    say(f"CMMD rows moved to the other side: {len(moved)}")
    say("\n| patient | CMMD side | corrected side | CMMD class | subtype | TOMPEI on CMMD side | TOMPEI on other side |")
    say("|---|---|---|---|---|---|---|")
    for m in moved:
        say("| " + " | ".join(str(v) for v in m) + " |")

    cm = clin.rename(columns={"side": "cmmd_side_original", "label_side": "side", "classification": "cmmd_class",
                              "Age": "cmmd_age"})[["patient_id", "side", "cmmd_side_original", "cmmd_class",
                                                   "subtype", "abnormality", "cmmd_age"]]
    b = t.merge(cm, on=["patient_id", "side"], how="left")
    # age is per patient: take TOMPEI's where given, else CMMD's (unlabelled breasts have none in either sheet)
    patient_age = pd.concat([b["t_age"], b["cmmd_age"]], axis=1).bfill(axis=1).iloc[:, 0]
    b["age"] = patient_age.groupby(b["patient_id"]).transform("first")
    age_diff = b[b["t_age"].notna() & b["cmmd_age"].notna() & (b["t_age"] != b["cmmd_age"])]
    b["has_cmmd_row"] = b["cmmd_class"].notna()
    b["has_outline"] = b["n_lesions"] > 0

    say("\n## 4. CMMD class against TOMPEI class (per breast, after moving those rows)\n")
    say(pd.crosstab(b["cmmd_class"].fillna("(no CMMD row)"), b["t_class"], margins=True).to_markdown())
    say("\nSubtype against TOMPEI class (per breast):\n")
    say(pd.crosstab(b["subtype"].fillna("(no subtype)"), b["t_class"], margins=True).to_markdown())
    say(f"\nAge differs between TOMPEI and CMMD on {len(age_diff)} breasts: "
        f"{[(r['patient_id'], int(r['cmmd_age']), int(r['t_age'])) for _, r in age_diff.iterrows()]} "
        f"(patient, CMMD, TOMPEI). TOMPEI's age is used.")
    say(f"Breasts with no age in either sheet after filling per patient: {b['age'].isna().sum()}")
    no_row = b[~b["has_cmmd_row"]]
    say(f"\nBreasts with no CMMD row: {len(no_row)}  |  TOMPEI class of these: {no_row['t_class'].value_counts().to_dict()}")
    say("\nBreast density (TOMPEI): " + str(b["density"].value_counts(dropna=False).to_dict()))
    say("BI-RADS category (TOMPEI): " + str(b["birads"].value_counts(dropna=False).sort_index().to_dict()))

    b.drop(columns=["t_age", "cmmd_age"]).to_csv(cfg["index_dir"] / "breast_labels.csv", index=False)
    Path("reports/03_tompei_labels.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nSaved data/index/image_sides.csv, data/index/breast_labels.csv, reports/03_tompei_labels.md")


if __name__ == "__main__":
    main()
