"""Task 04: pair CC + MLO per breast, attach labels, and make the patient-wise splits. No images are opened.

Run after 03_tompei_labels.py and 03_tompei_masks.py.

Decisions applied here (see docs/master_plan_summary.md):
  - Stage 1 sample = one breast (its CC + MLO pair). Label = CMMD benign / malignant (the biopsy result),
    with TOMPEI's left/right corrections. Breasts TOMPEI recommends excluding are dropped.
  - Breasts with no CMMD label are left out, and counted.
  - Splits are per PATIENT. Each patient is assigned to train / val / test ONCE; the Stage 1 and Stage 2 split
    files are both cut from that one assignment, so a Stage 2 test patient is never a Stage 1 training patient.
  - E0 only: an image-wise split of the Stage 2 images, copying the baseline paper on purpose.

Writes:
    data/index/pairs.csv                      one row per breast (all 2,601), with labels and extra columns
    data/splits/stage1.csv                    Stage 1 breasts + split
    data/splits/stage2.csv                    Stage 2 breasts + split (same patients -> same split as Stage 1)
    data/splits/stage2_e0_imagewise.csv       Stage 2 images, split image by image (E0 only)
    reports/04_data_flow.md                   the exclusion flow and all counts

Usage:
    python scripts/04_pairs_splits.py --config config.yaml
"""
import argparse, sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

SUBTYPES = ["Luminal A", "Luminal B", "HER2-enriched", "triple negative"]
SPLITS = ["train", "val", "test"]
DENSE = ["heterogeneous dense", "extremely dense"]
# source images known to be damaged or odd (found during QC in task 02); kept, but marked
QC_NOTES = {("D1-0951", "R"): "MLO source image damaged: black holes inside the tissue, upper strip cut off"}
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def split_70_15_15(ids, strata, seed):
    """Split a list of ids into train / val / test = 70 / 15 / 15, keeping each stratum's share equal."""
    train, rest, _, rest_strata = train_test_split(ids, strata, test_size=0.30, stratify=strata, random_state=seed)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest_strata, random_state=seed)
    out = {i: "train" for i in train}
    out.update({i: "val" for i in val})
    out.update({i: "test" for i in test})
    return out


def count_table(df, by, title):
    """Markdown table: rows = values of `by`, columns = splits, plus each split's share."""
    say(f"\n**{title}**\n")
    tab = pd.crosstab(df[by], df["split"]).reindex(columns=SPLITS, fill_value=0)
    tab["all"] = tab.sum(axis=1)
    share = (tab / tab.sum()).round(3)
    out = tab.astype(str) + " (" + (share * 100).round(1).astype(str) + "%)"
    out.loc["total"] = tab.sum().astype(str)
    say(out.to_markdown())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)
    idx_dir, png_dir, seed = cfg["index_dir"], cfg["png_dir"], cfg["seed"]
    mask_dir = cfg["work_root"] / f"masks{cfg.get('png_height', 1024)}"
    split_dir = cfg["work_root"] / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    png = pd.read_csv(idx_dir / "png_index.csv").merge(
        pd.read_csv(idx_dir / "image_sides.csv")[["png", "side_corrected"]], on="png")
    breasts = pd.read_csv(idx_dir / "breast_labels.csv")
    masks = pd.read_csv(idx_dir / "mask_index.csv")[["patient_id", "side", "mask", "lesion_labels"]]
    stage2_ids = set(pd.read_csv(idx_dir / "stage2_patients.csv")["patient_id"])

    # ---- 1. one row per breast with one CC and one MLO (side = corrected side)
    per_view = png.groupby(["patient_id", "side_corrected", "view"]).size()
    n_dup = int((per_view > 1).sum())
    # fixed rule if a breast ever had several images of one view: keep the first by SOP UID
    first = png.sort_values("sop_uid").drop_duplicates(["patient_id", "side_corrected", "view"])
    wide = first.pivot(index=["patient_id", "side_corrected"], columns="view", values="png").reset_index()
    wide = wide.rename(columns={"side_corrected": "side", "CC": "png_cc", "MLO": "png_mlo"})
    n_missing_view = int(wide[["png_cc", "png_mlo"]].isna().any(axis=1).sum())
    wide = wide.dropna(subset=["png_cc", "png_mlo"])

    # ---- 2. labels and extra columns
    pairs = wide.merge(breasts, on=["patient_id", "side"], how="left").merge(masks, on=["patient_id", "side"], how="left")
    pairs["cohort"] = pairs["patient_id"].str[:2]
    pairs["label"] = pairs["cmmd_class"].map({"Benign": 0, "Malignant": 1})      # empty if no CMMD row
    # True / False, and empty where TOMPEI gives no density ("boolean" is the pandas type that allows empty)
    pairs["dense"] = pairs["density"].isin(DENSE).astype("boolean").mask(pairs["density"].isna())
    pairs["qc_note"] = [QC_NOTES.get(k, "") for k in zip(pairs["patient_id"], pairs["side"])]
    pairs["stage1_status"] = "in Stage 1"
    pairs.loc[pairs["t_class"] == "Exclusion", "stage1_status"] = "excluded: TOMPEI exclusion"
    pairs.loc[pairs["cmmd_class"].isna(), "stage1_status"] = "excluded: no CMMD label"
    pairs["in_stage1"] = pairs["stage1_status"] == "in Stage 1"
    pairs["in_stage2"] = pairs["patient_id"].isin(stage2_ids) & pairs["subtype"].notna() & pairs["mask"].notna()

    # ---- 3. ONE split per patient, over all Stage 1 patients
    s1 = pairs[pairs["in_stage1"]]
    pat = s1.groupby("patient_id").agg(n_breasts=("label", "size"), any_mal=("label", "max"), any_ben=("label", "min"))
    pat["stratum"] = "malignant, not in Stage 2"
    pat.loc[pat["any_mal"] == 0, "stratum"] = "benign only"
    pat.loc[(pat["any_mal"] == 1) & (pat["any_ben"] == 0), "stratum"] = "one benign + one malignant breast"
    s2_sub = pairs[pairs["in_stage2"]].set_index("patient_id")["subtype"]
    pat.loc[s2_sub.index, "stratum"] = "Stage 2: " + s2_sub        # Stage 2 patients are stratified by subtype
    assignment = split_70_15_15(pat.index.tolist(), pat["stratum"].tolist(), seed)
    pat["split"] = pat.index.map(assignment)
    pairs["split"] = pairs["patient_id"].map(assignment)           # empty for patients with no Stage 1 breast

    cols = ["patient_id", "side", "split", "label", "cmmd_class", "subtype", "age", "abnormality", "png_cc",
            "png_mlo", "mask", "t_class", "density", "dense", "birads", "n_lesions", "lesion_labels", "cohort",
            "exclusion_reason", "cmmd_side_original", "qc_note", "in_stage1", "in_stage2", "stage1_status"]
    pairs = pairs[cols]
    pairs.to_csv(idx_dir / "pairs.csv", index=False)
    stage1 = pairs[pairs["in_stage1"]].drop(columns=["in_stage1", "stage1_status"])
    stage2 = pairs[pairs["in_stage2"]].drop(columns=["in_stage1", "stage1_status", "in_stage2"])
    stage1.to_csv(split_dir / "stage1.csv", index=False)
    stage2.to_csv(split_dir / "stage2.csv", index=False)

    # ---- 4. E0: image-wise 72 / 18 / 10 on the Stage 2 images (copies the baseline paper; leaks by design)
    e0 = pd.concat([stage2.assign(view="CC", png=stage2["png_cc"]), stage2.assign(view="MLO", png=stage2["png_mlo"])])
    e0 = e0[["png", "patient_id", "side", "view", "subtype", "age", "abnormality", "t_class", "density", "birads"]]
    e0 = e0.reset_index(drop=True)  # one clean row number per image
    tr, rest = train_test_split(e0, test_size=0.28, stratify=e0["subtype"], random_state=seed)
    va, te = train_test_split(rest, test_size=10 / 28, stratify=rest["subtype"], random_state=seed)
    e0 = pd.concat([tr.assign(split="train"), va.assign(split="val"), te.assign(split="test")]).sort_values("png")
    e0.to_csv(split_dir / "stage2_e0_imagewise.csv", index=False)

    # ---- 5. sanity checks: these stop the script if anything is wrong
    assert n_missing_view == 0 and n_dup == 0, "unexpected missing or duplicate views"
    assert len(pairs) == 2601 and not pairs.duplicated(["patient_id", "side"]).any()
    for name, d in [("stage1", stage1), ("stage2", stage2)]:
        assert d["split"].notna().all(), f"{name}: a row has no split"
        assert (d.groupby("patient_id")["split"].nunique() == 1).all(), f"{name}: a patient is in two splits"
    assert stage2["patient_id"].is_unique, "Stage 2 must have one breast per patient"
    # the same patient has the same split in both files
    both = stage1[["patient_id", "split"]].drop_duplicates().merge(stage2[["patient_id", "split"]], on="patient_id")
    assert (both["split_x"] == both["split_y"]).all() and len(both) == len(stage2)
    # class shares in every split are within 3 percentage points of the overall share
    for s in SPLITS:
        gap = abs(stage1.loc[stage1["split"] == s, "label"].mean() - stage1["label"].mean())
        assert gap < 0.03, f"stage1 {s}: malignant share off by {gap:.3f}"
        for sub in SUBTYPES:
            gap = abs((stage2.loc[stage2["split"] == s, "subtype"] == sub).mean() - (stage2["subtype"] == sub).mean())
            assert gap < 0.03, f"stage2 {s} {sub}: share off by {gap:.3f}"
            gap = abs((e0.loc[e0["split"] == s, "subtype"] == sub).mean() - (e0["subtype"] == sub).mean())
            assert gap < 0.03, f"e0 {s} {sub}: share off by {gap:.3f}"
    # every file the tables point to exists
    for f in pd.concat([pairs["png_cc"], pairs["png_mlo"]]):
        assert (png_dir / f).is_file(), f"missing PNG {f}"
    for f in pairs["mask"].dropna():
        assert (mask_dir / f).is_file(), f"missing mask {f}"
    assert stage2["mask"].notna().all() and stage1["label"].notna().all() and stage1["age"].notna().all()
    assert set(e0["png"]) == set(stage2["png_cc"]) | set(stage2["png_mlo"]) and e0["png"].is_unique
    print("All sanity checks passed.")

    # ---- 6. the data-flow report
    n_img = len(png)
    no_label = pairs[pairs["stage1_status"] == "excluded: no CMMD label"]
    excl = pairs[pairs["stage1_status"] == "excluded: TOMPEI exclusion"]
    sub_all = pairs[pairs["subtype"].notna()]
    say("# Task 04 — data flow, pairs and splits")
    say("\n## 1. Exclusion flow\n")
    say("| step | breasts | images | patients | what happened |")
    say("|---|---|---|---|---|")
    say(f"| All CMMD mammograms | {n_img // 2} | {n_img} | {png['patient_id'].nunique()} | everything downloaded and converted |")
    say(f"| Paired (one CC + one MLO per breast) | {len(pairs)} | {2 * len(pairs)} | {pairs['patient_id'].nunique()} | "
        f"{n_missing_view} breasts lost for a missing view; {n_dup} had more than one image of a view |")
    say(f"| − no CMMD label | −{len(no_label)} | −{2 * len(no_label)} | | the other breast of {no_label['patient_id'].nunique()} "
        f"D2 patients; not labelled benign or malignant |")
    say(f"| − TOMPEI recommends exclusion | −{len(excl)} | −{2 * len(excl)} | | "
        f"{excl['exclusion_reason'].value_counts().to_dict()} |")
    say(f"| **Stage 1 set** | **{len(stage1)}** | **{2 * len(stage1)}** | **{stage1['patient_id'].nunique()}** | "
        f"benign {(stage1['label'] == 0).sum()} / malignant {(stage1['label'] == 1).sum()} breasts |")
    say(f"| Malignant with a subtype label | {len(sub_all)} | {2 * len(sub_all)} | {sub_all['patient_id'].nunique()} | "
        f"one breast per patient |")
    lost = sub_all[~sub_all["in_stage2"]]
    say(f"| − no lesion mask | −{len(lost)} | −{2 * len(lost)} | −{lost['patient_id'].nunique()} | "
        f"TOMPEI class: {lost['t_class'].value_counts().to_dict()} |")
    say(f"| **Stage 2 set** | **{len(stage2)}** | **{2 * len(stage2)}** | **{stage2['patient_id'].nunique()}** | "
        + " / ".join(f"{s} {(stage2['subtype'] == s).sum()}" for s in SUBTYPES) + " |")
    say(f"\nTOMPEI class of the {len(no_label)} unlabelled breasts (left out): {no_label['t_class'].value_counts().to_dict()}")
    say(f"Patients with no breast in Stage 1 at all: {pairs.groupby('patient_id')['in_stage1'].any().eq(False).sum()}")

    say("\n## 2. Stage 1 set (per breast)\n")
    say(pd.crosstab(stage1["cmmd_class"], stage1["t_class"], margins=True).to_markdown())
    say(f"\nPatients: {stage1['patient_id'].nunique()}  |  with two breasts in the set: "
        f"{(stage1.groupby('patient_id').size() == 2).sum()}  |  with one benign and one malignant breast: "
        f"{(stage1.groupby('patient_id')['label'].nunique() == 2).sum()}")
    say(f"Cohort: {stage1['cohort'].value_counts().to_dict()}  |  age {stage1['age'].min():.0f}–{stage1['age'].max():.0f}, "
        f"mean {stage1['age'].mean():.1f}")
    say(f"Abnormality: {stage1['abnormality'].value_counts().to_dict()}")
    say(f"Breasts with a lesion mask (MLO): {stage1['mask'].notna().sum()}")
    flagged = pairs.loc[pairs["qc_note"] != "", ["patient_id", "side", "stage1_status", "exclusion_reason", "qc_note"]]
    say(f"QC-flagged breasts (all 2,601 checked): {flagged.to_dict('records')}")

    say("\n## 3. Splits (70 / 15 / 15, per patient, seed 42)\n")
    say("Every patient is assigned once. Strata used for the assignment (patients):\n")
    say(pd.crosstab(pat["stratum"], pat["split"]).reindex(columns=SPLITS).assign(all=lambda d: d.sum(axis=1)).to_markdown())
    count_table(stage1, "cmmd_class", "Stage 1, breasts per split")
    say(f"\nStage 1 patients per split: {stage1.groupby('split')['patient_id'].nunique().reindex(SPLITS).to_dict()}")
    count_table(stage2, "subtype", "Stage 2, patients per split")
    say("\nSubgroups for later reporting (Stage 1 breasts):\n")
    sg = pd.DataFrame({
        "malignant, TOMPEI Invisible": stage1[stage1["t_class"] == "Invisible"].groupby("split").size(),
        "malignant, TOMPEI Malignant": stage1[stage1["t_class"] == "Malignant"].groupby("split").size(),
        "benign, TOMPEI Normal (no visible lesion)": stage1[(stage1["label"] == 0) & (stage1["t_class"] == "Normal")].groupby("split").size(),
        "benign, TOMPEI Benign": stage1[stage1["t_class"] == "Benign"].groupby("split").size(),
        "dense breast": stage1[stage1["dense"].fillna(False)].groupby("split").size(),
        "not dense": stage1[~stage1["dense"].fillna(True)].groupby("split").size(),
        "density missing": stage1[stage1["dense"].isna()].groupby("split").size(),
    }).T.reindex(columns=SPLITS).fillna(0).astype(int)
    sg["all"] = sg.sum(axis=1)
    say(sg.to_markdown())
    say("\nStage 2 patients by density and split:\n")
    say(pd.crosstab(stage2["density"].fillna("(missing)"), stage2["split"]).reindex(columns=SPLITS).to_markdown())

    say("\n## 4. E0 split (image-wise 72 / 18 / 10, Stage 2 images, copies the baseline paper)\n")
    count_table(e0, "subtype", "E0, images per split")
    leak = e0.groupby("patient_id")["split"].nunique()
    say(f"\nPatients whose two images fall in different splits (leakage, by design in E0 only): "
        f"{(leak > 1).sum()} of {len(leak)}")
    te_pat = set(e0.loc[e0["split"] == "test", "patient_id"])
    say(f"E0 test images whose patient also has an image in E0 train: "
        f"{e0[(e0['split'] == 'test') & e0['patient_id'].isin(set(e0.loc[e0['split'] == 'train', 'patient_id']))].shape[0]}"
        f" of {(e0['split'] == 'test').sum()}")

    Path("reports/04_data_flow.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved {idx_dir / 'pairs.csv'}, {split_dir}/stage1.csv, stage2.csv, stage2_e0_imagewise.csv, reports/04_data_flow.md")


if __name__ == "__main__":
    main()
