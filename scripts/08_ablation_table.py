"""Task 08: build reports/ablation_table.md from the saved results (no model is run here).

Inputs (copied from the Kaggle notebook outputs into reports/stage2/):
    reports/stage2/test/metrics_test.json + test_<experiment>.csv   the one-time test scoring
    reports/stage2/val/<experiment>/<seed or fold>/metrics_val.json   validation results of every run
    reports/stage1_v2/test_predictions.csv                            frozen Stage 1 test probabilities

Tables:
    1. the "leak ladder" (E0 runs, in Anu's order) with micro, macro and per-class AUC, next to the paper
    2. E1-E6 (+ E1-224): validation mean +- std over seeds, and test (seed-averaged model) with 95% CIs
    3. the chained Stage 1 -> Stage 2 5-class AUC (master doc 7.1, soft version decided in task 08 Q2)

Usage:
    python scripts/08_ablation_table.py
"""
import json, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.metrics_mc import summary_mc

REPO_URL = "https://github.com/serag-ai/Multimodal-BC-Classifier"
REPO_CHECKED = "2026-10-24"
PAPER = {"micro": 88.87, "Benign": 100, "LumA": 67, "LumB": 74, "HER2": 78, "TN": 78, "images_only_overall": 61.3}
R = Path("reports/stage2")
L = []
say = L.append


def ci(m, k):
    v, c = m.get(k), m.get(f"{k}_ci95")
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:.3f} ({c[0]:.2f}–{c[1]:.2f})" if c else f"{v:.3f}"


def val_stats(exp, keys):
    ms = [json.loads(f.read_text()) for f in sorted((R / "val" / exp).glob("*/metrics_val.json"))]
    return {k: (np.mean([m[k] for m in ms]), np.std([m[k] for m in ms], ddof=1) if len(ms) > 1 else 0.0) for k in keys}, len(ms)


def main():
    test = json.loads((R / "test" / "metrics_test.json").read_text())
    say("# Task 08 — Stage 2 ablation (E0–E6)")
    say("")
    say(f"Baseline: Ben Rabah et al., *Diagnostics* 2025, 15, 995. Their code: {REPO_URL} "
        f"(public; checked {REPO_CHECKED}; read for the method, no code copied — it has no licence).")
    say(f"Test scored once for all experiments at {test['scored_at']} (forced re-run: {test['forced_rerun']}). "
        f"All numbers below are TEST unless marked validation. 95% CIs: bootstrap over patients.")

    # ---- 1. leak ladder
    say("")
    say("## 1. The leak ladder (E0 runs, 5 classes, test; average of 3 seeds)")
    say("")
    cls = ["Benign", "LumA", "LumB", "HER2", "TN"]
    say("| run | what changes | test images | micro AUC | macro AUC | " + " | ".join(cls) + " | ACC | F1 (macro) |")
    say("|---|---|---|---|---|" + "---|" * len(cls) + "---|---|")
    say(f"| *paper (published)* | their protocol, full data | 406 | *{PAPER['micro']/100:.3f}* | *≈{np.mean([PAPER[c] for c in cls])/100:.3f}* | "
        + " | ".join(f"*{PAPER[c]/100:.2f}*" for c in cls) + " | *0.638* | *0.52* |")
    ladder = [("E0-paperdata", "their full protocol: per-patient labels (4,040 img), leaky metadata, image-wise split"),
              ("E0", "our correct per-breast labels (2,590 img); still their leaky metadata and image-wise split"),
              ("E0-truemeta", "+ real lesion types for benign (metadata leak removed)"),
              ("E0-patient", "E0 on our patient-wise split (leaky metadata kept)")]
    for name, what in ladder:
        a = test["e0"].get(name, {}).get("averaged")
        if not a:
            say(f"| {name} | {what} | – | missing |")
            continue
        say(f"| **{name}** | {what} | {a['n_samples']} | {ci(a, 'auc_micro')} | {ci(a, 'auc_macro')} | "
            + " | ".join(f"{a[f'auc_{c}']:.3f}" for c in cls) + f" | {a['accuracy']:.3f} | {a['f1_macro']:.3f} |")
    say("")
    say("Controls (same test parts):")
    say("")
    say("| run | micro AUC | macro AUC | Benign | ACC | F1 (macro) | precision (macro) | recall (macro) |")
    say("|---|---|---|---|---|---|---|---|")
    say(f"| *paper, images only* | *{PAPER['images_only_overall']/100:.3f}* | | | *0.318* | *0.26* | *0.26* | *0.29* |")
    for name in ["E0-images", "E0-meta", "E0-meta-true"]:
        a = test["e0"].get(name, {}).get("averaged")
        if a:
            say(f"| {name} | {ci(a, 'auc_micro')} | {ci(a, 'auc_macro')} | {a['auc_Benign']:.3f} | {a['accuracy']:.3f} | "
                f"{a['f1_macro']:.3f} | {a['precision_macro']:.3f} | {a['recall_macro']:.3f} |")
    say("")
    say("Full metric set for every E0 run (test; ACC, precision / recall / F1 macro and weighted):")
    say("")
    say("| run | ACC | P macro | R macro | F1 macro | P weighted | R weighted | F1 weighted |")
    say("|---|---|---|---|---|---|---|---|")
    for name, m in test["e0"].items():
        a = m["averaged"]
        say(f"| {name} | {a['accuracy']:.3f} | {a['precision_macro']:.3f} | {a['recall_macro']:.3f} | {a['f1_macro']:.3f} | "
            f"{a['precision_weighted']:.3f} | {a['recall_weighted']:.3f} | {a['f1_weighted']:.3f} |")

    # ---- 2. E1-E6
    say("")
    say("## 2. Stage 2 ablation E1–E6 (4 subtypes, same 671 patients, test = the same 101 patients)")
    say("")
    sub = ["LumA", "LumB", "HER2", "TN"]
    say("| exp | adds | val macro AUC (mean ± std) | **test macro AUC** | test micro AUC | " + " | ".join(f"test {c}" for c in sub) + " |")
    say("|---|---|---|---|---|" + "---|" * len(sub))
    adds = {"E1-224": "E1 at 224 px (bridge to E0)", "E1": "EfficientNet-B3, MLO, patient split, 512 px",
            "E2": "+ CC with View Attention", "E3": "+ MLO lesion crop", "E4": "+ radiomics (20 + box flag)",
            "E5": "Gated Fusion", "E6": "E5 as 5-fold CV ensemble"}
    for name in ["E1-224", "E1", "E2", "E3", "E4", "E5", "E6"]:
        if name not in test["stage2"]:
            continue
        a = test["stage2"][name]["averaged"]
        v, n = val_stats(name, ["auc_macro"])
        say(f"| {name} | {adds[name]} | {v['auc_macro'][0]:.3f} ± {v['auc_macro'][1]:.3f} (n={n}) | **{ci(a, 'auc_macro')}** | "
            f"{ci(a, 'auc_micro')} | " + " | ".join(ci(a, f"auc_{c}") for c in sub) + " |")
    say(f"| *paper (5-class model)* | | | | | *{PAPER['LumA']/100:.2f}* | *{PAPER['LumB']/100:.2f}* | *{PAPER['HER2']/100:.2f}* | *{PAPER['TN']/100:.2f}* |")
    say("")
    say("Test class sizes: LumA 21, LumB 51, HER2 19, TN 10 patients — per-class CIs are wide, TN especially.")
    v_best = max((n for n in test["stage2"] if n != "E1-224"), key=lambda n: val_stats(n, ["auc_macro"])[0]["auc_macro"][0])
    t_best = max((n for n in test["stage2"] if n != "E1-224"), key=lambda n: test["stage2"][n]["averaged"]["auc_macro"])
    say("")
    say(f"Reading: best on validation is {v_best}, best on test is {t_best}; the validation and test rankings do not "
        "agree, and every E1–E6 test interval overlaps the others. On 101 test patients no single component is shown "
        "to help or hurt. The paper's per-class numbers come from its 5-class model under the leaky protocol "
        "(benign included as negatives), so they are not directly comparable with these 4-class AUCs.")

    # ---- 3. chained 5-class
    s1 = pd.read_csv("reports/stage1_v2/test_predictions.csv")
    s2 = pd.read_csv(R / "test" / "test_E6.csv")
    ben = s1[s1["label"] == 0][["patient_id", "side", "prob"]].assign(y=0)
    mal = s2[["patient_id", "side", "y"] + [f"p_{c}" for c in sub]].merge(s1[["patient_id", "side", "prob"]], on=["patient_id", "side"])
    mal["y"] = mal["y"] + 1  # 0 Benign, 1 LumA, 2 LumB, 3 HER2, 4 TN
    for c in sub:
        ben[f"p_{c}"] = 0.25  # no lesion -> no subtype evidence (task 08 Q2)
    both = pd.concat([ben, mal], ignore_index=True)
    five = pd.DataFrame({"patient_id": both["patient_id"], "y": both["y"], "p_Benign": 1 - both["prob"]})
    for c in sub:
        five[f"p_{c}"] = both["prob"] * both[f"p_{c}"]
    m5 = summary_mc(five, ["Benign"] + sub)
    say("")
    say("## 3. Chained Stage 1 → Stage 2, one 5-class probability per breast (test)")
    say("")
    say("Stage 1 = the frozen v2 ensemble (task 06); Stage 2 = E6. Soft chaining for every breast: P(benign) = "
        "1 − p(malignant); P(subtype) = p(malignant) × Stage 2's subtype probability (master doc §7.1 without the "
        "hard gate, as decided). Benign breasts have no lesion mask, so their subtype probabilities are 1/4 each.")
    say(f"Set: {int((five.y == 0).sum())} benign test breasts + {int((five.y > 0).sum())} subtyped test patients. "
        f"The other {279 - len(five)} Stage 1 test breasts (malignant with no subtype or no mask) cannot be given a "
        f"5-class label and are left out.")
    say("")
    say("| | micro AUC | macro AUC | " + " | ".join(["Benign"] + sub) + " |")
    say("|---|---|---|" + "---|" * 5)
    say(f"| **ours, chained (test)** | {ci(m5, 'auc_micro')} | {ci(m5, 'auc_macro')} | " + " | ".join(ci(m5, f"auc_{c}") for c in ["Benign"] + sub) + " |")
    say(f"| *paper (leaky protocol)* | *{PAPER['micro']/100:.3f}* | *≈{np.mean([PAPER[c] for c in cls])/100:.3f}* | " + " | ".join(f"*{PAPER[c]/100:.2f}*" for c in cls) + " |")
    say("")
    say("Caution: in this 5-class setting the 82 benign breasts are negatives for every subtype, and Stage 1 already "
        "pushes most of them down, so the chained subtype AUCs are higher than the 4-class ones in section 2 (same "
        "Stage 2 model). Compare like with like: section 2 against section 2, this table against the paper's "
        "5-class numbers — which also benefit from the metadata leak (section 1).")
    five.to_csv(R / "test" / "chained_5class.csv", index=False)
    (R / "test" / "chained_5class_metrics.json").write_text(json.dumps(m5, indent=2))
    Path("reports/ablation_table.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
