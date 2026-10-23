"""5-fold cross-validation folds over the TRAIN + VAL patients (the test patients are never in any fold).

Same rules as the main split (scripts/04_pairs_splits.py): folds are per PATIENT, stratified so every fold has
the same mix of patient groups: Stage 2 patients by subtype; benign-only patients with / without a visible
lesion; other malignant patients with a visible / invisible cancer; patients with one benign and one malignant
breast. Fixed seed, so every notebook computes exactly the same folds.
"""
import pandas as pd
from sklearn.model_selection import StratifiedKFold


def patient_strata(df):
    """One stratum name per patient, from a stage1.csv-style table (one row per breast)."""
    g = df.groupby("patient_id")
    pat = pd.DataFrame({
        "any_mal": g["label"].max(), "any_ben": g["label"].min(),
        "t_benign": g["t_class"].agg(lambda c: (c == "Benign").any()),
        "t_malignant": g["t_class"].agg(lambda c: (c == "Malignant").any()),
        "stage2_subtype": g.apply(lambda d: d.loc[d["in_stage2"].astype(bool), "subtype"].dropna().max(), include_groups=False),
    })
    strata = pd.Series("malignant, " + pat["t_malignant"].map({True: "visible", False: "invisible"}), index=pat.index)
    benign_only = pat["any_mal"] == 0
    strata[benign_only] = "benign only, " + pat.loc[benign_only, "t_benign"].map({True: "visible", False: "not visible"})
    strata[(pat["any_mal"] == 1) & (pat["any_ben"] == 0)] = "one benign + one malignant"
    has_sub = pat["stage2_subtype"].notna()
    strata[has_sub] = "Stage 2: " + pat.loc[has_sub, "stage2_subtype"]
    return strata


def make_folds(df, n_folds=5, seed=42):
    """{patient_id: fold number 0..n_folds-1} for the patients in df (pass train + val rows only)."""
    strata = patient_strata(df)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    folds = {}
    for k, (_, idx) in enumerate(skf.split(strata.index, strata.values)):
        for p in strata.index[idx]:
            folds[p] = k
    return folds
