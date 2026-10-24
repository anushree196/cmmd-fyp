"""Task 06: compare Stage 1 v1 and v2 on the SAME test breasts from their saved test predictions.

No model is run and nothing is re-scored: this only reads the two test_predictions.csv files that the two
(logged) test evaluations already wrote.

Paired bootstrap: draw test patients with replacement, compute AUC(v2) - AUC(v1) on the same draw, repeat
2,000 times. If the 95% interval of the difference contains 0, the improvement is not distinguishable from noise.

Usage:
    python scripts/06_compare_stage1.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

v1 = pd.read_csv("reports/stage1/test_predictions.csv")[["patient_id", "side", "label", "prob"]]
v2 = pd.read_csv("reports/stage1_v2/test_predictions.csv")[["patient_id", "side", "label", "prob"]]
d = v1.merge(v2, on=["patient_id", "side", "label"], suffixes=("_v1", "_v2"))
assert len(d) == len(v1) == len(v2), "both files must hold the same test breasts"

rng = np.random.default_rng(42)
groups = {p: g for p, g in d.groupby("patient_id")}
ids = np.array(list(groups))
diffs = []
for _ in range(2000):
    s = pd.concat([groups[p] for p in rng.choice(ids, size=len(ids), replace=True)])
    if s["label"].nunique() == 2:
        diffs.append(roc_auc_score(s["label"], s["prob_v2"]) - roc_auc_score(s["label"], s["prob_v1"]))
auc1, auc2 = roc_auc_score(d["label"], d["prob_v1"]), roc_auc_score(d["label"], d["prob_v2"])
lo, hi = np.percentile(diffs, [2.5, 97.5])
out = {"n_test_breasts": len(d), "auc_v1": auc1, "auc_v2": auc2, "difference": auc2 - auc1,
       "difference_ci95": [float(lo), float(hi)], "share_of_draws_v2_better": float(np.mean(np.array(diffs) > 0)),
       "correlation_of_probabilities": float(np.corrcoef(d["prob_v1"], d["prob_v2"])[0, 1])}
Path("reports/stage1_v2/compare_v1_v2_test.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
