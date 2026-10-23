"""Metrics: AUC, sensitivity, specificity, threshold choice, and bootstrap confidence intervals.

Bootstrap: draw patients at random WITH replacement (same number as in the set), recompute the metric, repeat
2,000 times; the 95% interval is the middle 95% of those values. Patients, not breasts, are drawn, because the
two breasts of one patient are not independent.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve


def auc(df):
    return float(roc_auc_score(df["label"], df["prob"]))


def sensitivity(df, thr):
    pos = df[df["label"] == 1]
    return float((pos["prob"] >= thr).mean())


def specificity(df, thr):
    neg = df[df["label"] == 0]
    return float((neg["prob"] < thr).mean())


def youden_threshold(df):
    """The threshold that maximises sensitivity + specificity - 1 (Youden's J). Chosen on VALIDATION only."""
    fpr, tpr, thr = roc_curve(df["label"], df["prob"])
    best = int(np.argmax(tpr - fpr))
    return float(min(thr[best], 1.0))  # roc_curve can return inf for the first point


def bootstrap_ci(df, fn, n=2000, seed=42):
    """95% interval of fn(df) by resampling patients. Draws that miss a class (AUC undefined) are skipped."""
    rng = np.random.default_rng(seed)
    groups = {p: g for p, g in df.groupby("patient_id")}
    ids = np.array(list(groups))
    values = []
    for _ in range(n):
        sample = pd.concat([groups[p] for p in rng.choice(ids, size=len(ids), replace=True)])
        if sample["label"].nunique() < 2 and fn is auc:
            continue
        v = fn(sample)
        if not np.isnan(v):  # e.g. sensitivity of a draw that happens to contain no cancer
            values.append(v)
    lo, hi = np.percentile(values, [2.5, 97.5])
    return float(lo), float(hi), len(values)


def summary(df, thr, n_boot=2000):
    """Everything we report for one set of predictions, at a fixed threshold."""
    out = {"n_breasts": len(df), "n_patients": int(df["patient_id"].nunique()),
           "n_malignant": int((df["label"] == 1).sum()), "n_benign": int((df["label"] == 0).sum()),
           "threshold": thr}
    if df["label"].nunique() == 2:
        lo, hi, k = bootstrap_ci(df, auc, n_boot)
        out.update(auc=auc(df), auc_ci95=[lo, hi], auc_boot_draws=k)
    if out["n_malignant"]:
        lo, hi, _ = bootstrap_ci(df, lambda d: sensitivity(d, thr) if (d["label"] == 1).any() else np.nan, n_boot)
        out.update(sensitivity=sensitivity(df, thr), sensitivity_ci95=[lo, hi])
    if out["n_benign"]:
        lo, hi, _ = bootstrap_ci(df, lambda d: specificity(d, thr) if (d["label"] == 0).any() else np.nan, n_boot)
        out.update(specificity=specificity(df, thr), specificity_ci95=[lo, hi])
    pred = (df["prob"] >= thr).astype(int)
    tn, fp, fn_, tp = confusion_matrix(df["label"], pred, labels=[0, 1]).ravel()
    out["confusion"] = {"true_benign": int(tn), "false_malignant": int(fp), "missed_cancer": int(fn_),
                        "found_cancer": int(tp)}
    return out
