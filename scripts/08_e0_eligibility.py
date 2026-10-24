"""Task 08: how many images are eligible for E0, compared with the baseline paper's 4,056, and why they differ.

Reads only our tables and the CMMD sheet. Writes reports/08_e0_eligibility.md.

Usage:
    python scripts/08_e0_eligibility.py --config config.yaml
"""
import argparse, sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config
from src.e0 import CLASSES, build_table, imagewise_split


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)
    work = cfg["work_root"]
    cmmd = pd.read_excel(cfg["clinical_xlsx"])
    img = pd.read_csv(cfg["index_dir"] / "dicom_index.csv")   # one row per DICOM, CMMD joined on patient + DICOM side
    L = []
    say = L.append

    # A. our rule
    rows = build_table(work)
    rows["split_image"] = imagewise_split(rows)
    per = rows["y"].map(dict(enumerate(CLASSES))).value_counts().reindex(CLASSES)
    # B. breast-level with the original CMMD labels, nothing dropped
    lab = img[img["clinical_match"] == "both"]
    b = lab[(lab["classification"] == "Benign") | lab["subtype"].notna()]
    # C. patient-level: every image of a patient carries that patient's label
    pat = cmmd.groupby("ID1").agg(sub=("subtype", lambda s: s.dropna().iloc[0] if s.notna().any() else None),
                                  mal=("classification", lambda c: (c == "Malignant").any()))
    img["sub"], img["mal"] = img["patient_id"].map(pat["sub"]), img["patient_id"].map(pat["mal"])
    c = img[img["sub"].notna() | ~img["mal"]]
    c_unlabelled = c[c["clinical_match"] != "both"]

    say("# Task 08 — E0: eligible images vs the baseline paper's 4,056")
    say("")
    say("| rule | images | note |")
    say("|---|---|---|")
    say(f"| **A. ours**: each breast labelled by its own CMMD row (TOMPEI side corrections), benign or with a subtype, TOMPEI exclusions dropped | **{len(rows)}** | {rows['patient_id'].nunique()} patients; used for E0 |")
    say(f"| B. same with the original CMMD labels, nothing dropped | {len(b)} | |")
    say(f"| **C. patient level**: every image of a subtyped patient gets the subtype, every image of a benign-only patient is benign | **{len(c)}** | closest to the paper's 4,056 (difference {4056 - len(c)}) |")
    say("")
    say(f"Under rule C, {len(c_unlabelled)} images are of a breast with **no** CMMD label of its own (the other breast "
        f"of a subtyped patient) but are still trained and tested as a subtype. The paper's folder-building step is "
        f"not in its published code, so rule C is our best explanation, not a certainty; the last {4056 - len(c)} "
        f"images are not explained.")
    say("")
    say("Rule A per class (images): " + ", ".join(f"{k} {v}" for k, v in per.items()))
    say(f"Rule C per class (images): " + str(c["sub"].fillna("Benign").value_counts().to_dict()))
    say("")
    say("## E0 image-wise split (the paper's procedure: 72%, then 64.28% / 35.72%, stratified by class, seed 42)")
    say("")
    say(pd.crosstab(rows["y"].map(dict(enumerate(CLASSES))), rows["split_image"]).reindex(index=CLASSES, columns=["train", "val", "test"]).to_markdown())
    lk = rows.groupby("patient_id")["split_image"].nunique()
    te = rows[rows["split_image"] == "test"]
    say("")
    say(f"Paper: 2,920 / 730 / 406. Ours: {(rows.split_image == 'train').sum()} / {(rows.split_image == 'val').sum()} / {len(te)}.")
    say(f"Leakage of the image-wise split: {int((lk > 1).sum())} of {len(lk)} patients have images in more than one part; "
        f"{int(te['patient_id'].isin(set(rows.loc[rows.split_image == 'train', 'patient_id'])).sum())} of {len(te)} test images "
        f"belong to a patient who also has an image in train.")
    say("")
    say("## The paper's metadata encoding (from its public code, `data_split_publish.ipynb`)")
    say("")
    say("Tumour class is set from the folder each image is read from: every image in the Benign folder gets 0 "
        "(\"None\"), malignant images get 1 mass / 2 calcification / 3 both. In CMMD, benign breasts have a real "
        "lesion type too:")
    say("")
    say("| | tumour class 0 | 1 mass | 2 calcification | 3 both |")
    say("|---|---|---|---|---|")
    for enc in ["paper", "true"]:
        vc = rows.loc[rows["y"] == 0, f"tumour_{enc}"].value_counts()
        say(f"| benign images, {enc} encoding | {int(vc.get(0.0, 0))} | {int(vc.get(1.0, 0))} | {int(vc.get(2.0, 0))} | {int(vc.get(3.0, 0))} |")
    mal0 = int((rows.loc[rows["y"] > 0, "tumour_paper"] == 0).sum())
    say("")
    say(f"With the paper's encoding, tumour class 0 occurs for {int((rows.tumour_paper == 0).sum())} images, all benign "
        f"({mal0} malignant): the metadata input reveals the benign label. This explains the paper's benign AUC of "
        f"100% and much of the jump from 61.3% (images only) to 88.87% (with metadata).")
    say("")
    say("Also from the code: the reported 88.87% is Keras' `AUC()` on one-hot labels, i.e. a **micro** average; the "
        "model used is the last of 10 epochs (early stopping has patience 20 and never triggers).")
    Path("reports/08_e0_eligibility.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
