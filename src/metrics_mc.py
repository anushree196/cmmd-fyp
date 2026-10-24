"""Metrics for the multi-class models (E0 family: 5 classes; E1-E6: 4 subtypes).

Per class: one-vs-rest AUC (that class against all the others).
macro AUC: the plain average of the per-class AUCs (every class counts the same).
micro AUC: all (sample, class) pairs pooled into one big binary problem. This is what Keras' AUC() reports
           for one-hot labels, i.e. what the baseline paper's 88.87% is. Easy, frequent classes pull it up.
ACC / precision / recall / F1: from the arg-max class; precision, recall and F1 are given as macro (every class
           counts the same) and weighted (classes weighted by their size), like sklearn's classification_report.
95% confidence intervals: bootstrap, drawing PATIENTS with replacement (their images or breasts stay together).
"""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score


def auc_set(y, P, classes):
    """Per-class, macro and micro AUC. y: (n,) class index, P: (n, k) probabilities."""
    out = {}
    onehot = np.eye(len(classes))[y]
    for i, c in enumerate(classes):
        out[f"auc_{c}"] = float(roc_auc_score(onehot[:, i], P[:, i])) if 0 < onehot[:, i].sum() < len(y) else np.nan
    per = [out[f"auc_{c}"] for c in classes]
    out["auc_macro"] = float(np.nanmean(per))
    out["auc_micro"] = float(roc_auc_score(onehot.ravel(), P.ravel()))
    return out


def label_metrics(y, P, classes):
    pred = P.argmax(1)
    out = {"accuracy": float(accuracy_score(y, pred))}
    for avg in ("macro", "weighted"):
        p, r, f, _ = precision_recall_fscore_support(y, pred, labels=range(len(classes)), average=avg, zero_division=0)
        out.update({f"precision_{avg}": float(p), f"recall_{avg}": float(r), f"f1_{avg}": float(f)})
    p, r, f, n = precision_recall_fscore_support(y, pred, labels=range(len(classes)), average=None, zero_division=0)
    out["per_class"] = {c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "n": int(n[i])}
                        for i, c in enumerate(classes)}
    out["confusion"] = pd.crosstab(pd.Series(y, name="true"), pd.Series(pred, name="pred")).reindex(
        index=range(len(classes)), columns=range(len(classes)), fill_value=0).values.tolist()
    return out


def summary_mc(df, classes, n_boot=2000, seed=42):
    """df: one row per sample with columns patient_id, y (class index) and p_<class> probabilities."""
    y = df["y"].to_numpy()
    P = df[[f"p_{c}" for c in classes]].to_numpy()
    out = {"n_samples": len(df), "n_patients": int(df["patient_id"].nunique()),
           "n_per_class": {c: int((y == i).sum()) for i, c in enumerate(classes)}}
    out.update(label_metrics(y, P, classes))
    point = auc_set(y, P, classes)
    out.update(point)
    # bootstrap by patient
    rng = np.random.default_rng(seed)
    rows = df.groupby("patient_id").indices
    ids = np.array(list(rows))
    draws = {k: [] for k in point}
    draws["accuracy"] = []
    for _ in range(n_boot):
        idx = np.concatenate([rows[p] for p in rng.choice(ids, size=len(ids), replace=True)])
        yb, Pb = y[idx], P[idx]
        if len(np.unique(yb)) < 2:
            continue
        for k, v in auc_set(yb, Pb, classes).items():
            if not np.isnan(v):
                draws[k].append(v)
        draws["accuracy"].append(float((Pb.argmax(1) == yb).mean()))
    for k, v in draws.items():
        if v:
            out[f"{k}_ci95"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    return out
