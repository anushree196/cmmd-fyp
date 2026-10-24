"""Task 08b: synopsis tables (T1-T6) and figures (F1-F8) from SAVED results only. No model is run here.

Every number comes from a file listed under its table. Figures: 300 dpi PNG, white background, Times-style
serif font, readable in black and white (greys, hatching, line styles and markers instead of colour).

Usage:
    python scripts/08b_synopsis.py
"""
import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from sklearn.metrics import roc_curve

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.metrics_mc import summary_mc

OUT = Path("reports/synopsis")
OUT.mkdir(parents=True, exist_ok=True)
REPO_URL, REPO_CHECKED = "https://github.com/serag-ai/Multimodal-BC-Classifier", "2026-10-24"
# The paper's published numbers (docs/baseline_paper_notes.md, checked against the PDF by Anu)
PAPER = {"micro": 0.8887, "Benign": 1.00, "LumA": 0.67, "LumB": 0.74, "HER2": 0.78, "TN": 0.78,
         "acc": 0.6379, "pre": 0.46, "rec": 0.64, "f1": 0.52, "img_micro": 0.613, "img_acc": 0.3178,
         "img_f1": 0.26, "img_pre": 0.26, "img_rec": 0.29}
SUB = ["LumA", "LumB", "HER2", "TN"]
FIVE = ["Benign", "LumA", "LumB", "HER2", "TN"]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": 0.6,
    "axes.edgecolor": "black", "axes.facecolor": "white", "figure.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "grid.color": "0.85", "grid.linewidth": 0.5,
    "lines.linewidth": 1.2, "savefig.dpi": 300, "savefig.bbox": "tight"})
GREYS = ["0.15", "0.45", "0.7", "0.88"]
HATCH = ["", "//", "..", "xx", "\\\\"]
STYLES = ["-", "--", "-.", ":", (0, (5, 1, 1, 1))]
MARKERS = ["o", "s", "^", "D", "v"]

md = []          # tables.md
notes = []       # figure notes (skipped / partial)


def ci(v, c, d=3):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:.{d}f} ({c[0]:.{d-1}f}–{c[1]:.{d-1}f})" if c else f"{v:.{d}f}")


def table(name, title, df, sources, note=None):
    df.to_csv(OUT / f"{name}.csv", index=False)
    md.extend([f"## {name.split('_')[0].upper()}: {title}", "", df.to_markdown(index=False), ""])
    if note:
        md.extend([note, ""])
    md.extend(["Sources: " + "; ".join(f"`{s}`" for s in sources), ""])


def load(p):
    return json.loads(Path(p).read_text())


# ============================================================ data
s1 = pd.read_csv("data/splits/stage1.csv")
s1["label"] = s1["label"].astype(int)
s2 = pd.read_csv("data/splits/stage2.csv")
pairs = pd.read_csv("data/index/pairs.csv")
e0rows = pd.read_csv("reports/stage2/e0_rows.csv")
v1, v2 = load("reports/stage1/metrics_test.json"), load("reports/stage1_v2/metrics_test.json")
cmp12 = load("reports/stage1_v2/compare_v1_v2_test.json")
abl = load("reports/stage2/test/metrics_test.json")
clean_file = Path("reports/stage2/test_e0clean/metrics_test.json")
clean = load(clean_file)["e0"].get("E0-clean") if clean_file.exists() else None
chain = load("reports/stage2/test/chained_5class_metrics.json")
SPL = ["train", "val", "test"]

# ============================================================ T1 dataset by split and class
rows = []
for sp in SPL + ["total"]:
    d = s1 if sp == "total" else s1[s1["split"] == sp]
    for cls, dd in [("benign", d[d.label == 0]), ("malignant", d[d.label == 1]), ("all", d)]:
        rows.append({"set": "Stage 1 (benign vs malignant)", "split": sp, "class": cls,
                     "patients": dd["patient_id"].nunique(), "breasts": len(dd), "images": 2 * len(dd)})
    d2 = s2 if sp == "total" else s2[s2["split"] == sp]
    for full, short in zip(["Luminal A", "Luminal B", "HER2-enriched", "triple negative"], SUB):
        dd = d2[d2["subtype"] == full]
        rows.append({"set": "Stage 2 (subtype; E1–E6)", "split": sp, "class": short,
                     "patients": dd["patient_id"].nunique(), "breasts": len(dd), "images": 2 * len(dd)})
    rows.append({"set": "Stage 2 (subtype; E1–E6)", "split": sp, "class": "all",
                 "patients": d2["patient_id"].nunique(), "breasts": len(d2), "images": 2 * len(d2)})
    de = e0rows if sp == "total" else e0rows[e0rows["split_image"] == sp] if "split_image" in e0rows else None
    if de is not None:
        for k, c in enumerate(FIVE[:1] + ["HER2", "LumA", "LumB", "TN"]):
            pass
t1 = pd.DataFrame(rows)
# E0 (5 classes, image-wise split, as the paper): images per class and split
e0_names = {0: "Benign", 1: "HER2", 2: "LumA", 3: "LumB", 4: "TN"}
e0x = []
for sp in SPL + ["total"]:
    d = e0rows if sp == "total" else e0rows[e0rows["split_image"] == sp]
    for k in [0, 2, 3, 1, 4]:
        dd = d[d["y"] == k]
        e0x.append({"set": "E0 (5 classes, image-wise split)", "split": sp, "class": e0_names[k],
                    "patients": dd["patient_id"].nunique(), "breasts": dd[["patient_id", "side"]].drop_duplicates().shape[0], "images": len(dd)})
    e0x.append({"set": "E0 (5 classes, image-wise split)", "split": sp, "class": "all", "patients": d["patient_id"].nunique(),
                "breasts": d[["patient_id", "side"]].drop_duplicates().shape[0], "images": len(d)})
t1 = pd.concat([t1, pd.DataFrame(e0x)], ignore_index=True)
table("t1_dataset", "Dataset by split and class", t1,
      ["data/splits/stage1.csv", "data/splits/stage2.csv", "reports/stage2/e0_rows.csv", "cross-check: reports/04_data_flow.md"],
      "Stage 1 and Stage 2 use one patient-wise split (a patient's breasts are always in the same part). In the E0 "
      "image-wise split one patient's images can sit in different parts, so its patient counts add up to more than the total.")

# ============================================================ T2 Stage 1 test
def op(m, name):
    return m["operating_points"][name]


r = []
r.append(("Test AUC (95% CI)", ci(v1["auc"], v1["auc_ci95"]), ci(v2["auc"], v2["auc_ci95"])))
r.append(("Model", "single model (epoch 7)", "ensemble of 5 CV fold models (recipe R3)"))
r.append(("Thresholds chosen on", "validation (278 breasts)", "out-of-fold predictions (1,577 breasts)"))
for nm1, nm2, label in [("youden", "youden", "Youden"), ("val_sens90", "oof_sens90", "≥90% sensitivity")]:
    a, b = op(v1, nm1), op(v2, nm2)
    r.append((f"{label}: threshold", f"{a['threshold']:.3f}", f"{b['threshold']:.3f}"))
    r.append((f"{label}: sensitivity (95% CI)", ci(a["test"]["sensitivity"], a["test"]["sensitivity_ci95"]), ci(b["test"]["sensitivity"], b["test"]["sensitivity_ci95"])))
    r.append((f"{label}: specificity (95% CI)", ci(a["test"]["specificity"], a["test"]["specificity_ci95"]), ci(b["test"]["specificity"], b["test"]["specificity_ci95"])))
for g, label in [("dense_breasts", "Subgroup AUC: dense breasts"), ("non_dense_breasts", "Subgroup AUC: non-dense breasts"),
                 ("invisible_cancers_vs_all_benign", "Subgroup AUC: 'Invisible' cancers vs all benign"),
                 ("visible_cancers_vs_all_benign", "Subgroup AUC: visible cancers vs all benign")]:
    a, b = op(v1, "youden")["test_subgroups"][g], op(v2, "youden")["test_subgroups"][g]
    r.append((f"{label} (n={a['n_breasts']})", ci(a["auc"], a["auc_ci95"]), ci(b["auc"], b["auc_ci95"])))
r.append(("Paired difference v2 − v1 in test AUC (95% CI)", "", f"{cmp12['difference']:+.3f} ({cmp12['difference_ci95'][0]:+.3f} to {cmp12['difference_ci95'][1]:+.3f})"))
t2 = pd.DataFrame(r, columns=["measure", "v1", "v2 (final)"])
table("t2_stage1", "Stage 1 (benign vs malignant) test results, 279 breasts / 265 patients",
      t2,
      ["reports/stage1/metrics_test.json", "reports/stage1_v2/metrics_test.json", "reports/stage1_v2/compare_v1_v2_test.json"],
      "The test split was scored twice in total (v1, then v2 with the frozen recipe); the reason is logged in PROGRESS.md (task 06 v2).")

# ============================================================ T3 leak ladder
def e0m(name):
    if name == "E0-clean":
        return clean["averaged"] if clean else None
    return abl["e0"][name]["averaged"]


ladder = [("Paper (published)", "their protocol, their data", None),
          ("E0-paperdata", "their full protocol: per-patient labels (4,040 images), leaky metadata, image-wise split", "E0-paperdata"),
          ("E0", "our per-breast labels (2,590 images); their leaky metadata and image-wise split", "E0"),
          ("E0-meta", "E0's metadata only, no image", "E0-meta"),
          ("E0-truemeta", "E0 with real lesion types for benign (leak removed)", "E0-truemeta"),
          ("E0-patient", "E0 on our patient-wise split (leak kept)", "E0-patient"),
          ("E0-clean", "real lesion types AND patient-wise split (both fixes)", "E0-clean")]
r = []
for label, what, key in ladder:
    if key is None:
        r.append({"run": label, "what": what, "test images": 406, "micro AUC": f"{PAPER['micro']:.3f}",
                  "macro AUC": f"≈{np.mean([PAPER[c] for c in FIVE]):.3f}", **{c: f"{PAPER[c]:.2f}" for c in FIVE},
                  "ACC": f"{PAPER['acc']:.3f}", "precision": f"{PAPER['pre']:.2f}", "recall": f"{PAPER['rec']:.2f}", "F1": f"{PAPER['f1']:.2f}"})
        continue
    a = e0m(key)
    if a is None:
        r.append({"run": label, "what": what + " — NOT RUN", "test images": "–"})
        continue
    r.append({"run": label, "what": what, "test images": a["n_samples"], "micro AUC": ci(a["auc_micro"], a.get("auc_micro_ci95")),
              "macro AUC": ci(a["auc_macro"], a.get("auc_macro_ci95")), **{c: f"{a[f'auc_{c}']:.3f}" for c in FIVE},
              "ACC": f"{a['accuracy']:.3f}", "precision": f"{a['precision_macro']:.3f}", "recall": f"{a['recall_macro']:.3f}", "F1": f"{a['f1_macro']:.3f}"})
t3 = pd.DataFrame(r)
table("t3_leak_ladder", "The leak ladder (E0 family, 5 classes, test, average of 3 seeds)", t3,
      ["paper: docs/baseline_paper_notes.md", "reports/stage2/test/metrics_test.json", "E0-clean: reports/stage2/test_e0clean/metrics_test.json"],
      "Precision, recall and F1 are macro averages (our runs); the paper does not say which average it reports. The paper's "
      "macro AUC is our average of its five per-class AUCs. E0-paperdata, E0, E0-meta and E0-truemeta are tested on their own "
      "image-wise test parts; E0-patient and E0-clean on our patient-wise test patients (images).")

# ============================================================ E0-patient / E0-clean on 4 subtypes, 101 test patients
def four_subtype(csv, split_patients):
    """From saved per-image 5-class probabilities: keep the images of the given Stage 2 patients, drop the benign
    column and renormalise the 4 subtype probabilities, average CC and MLO per breast."""
    t = pd.read_csv(csv)
    t = t.merge(s2[["patient_id", "side", "subtype"]], on=["patient_id", "side"])
    t = t[t["patient_id"].isin(split_patients)]
    P = t[[f"p_{c}" for c in SUB]].to_numpy()
    P = P / P.sum(1, keepdims=True)
    t[[f"p_{c}" for c in SUB]] = P
    b = t.groupby(["patient_id", "side"]).agg({**{f"p_{c}": "mean" for c in SUB}, "subtype": "first"}).reset_index()
    b["y"] = b["subtype"].map({"Luminal A": 0, "Luminal B": 1, "HER2-enriched": 2, "triple negative": 3})
    return b


test101 = set(s2.loc[s2["split"] == "test", "patient_id"])
four = {}
for name, csv in [("E0-patient", "reports/stage2/test/test_E0-patient.csv"), ("E0-clean", "reports/stage2/test_e0clean/test_E0-clean.csv")]:
    if Path(csv).exists():
        b = four_subtype(csv, test101)
        four[name] = summary_mc(b, SUB)
        b.to_csv(OUT / f"four_subtype_test_{name}.csv", index=False)
four_val = {}
val101 = set(s2.loc[s2["split"] == "val", "patient_id"])
for name in ["E0-patient", "E0-clean"]:
    vals = []
    for f in sorted(Path(f"reports/stage2/val/{name}").glob("seed*/val_predictions.csv")):
        vals.append(summary_mc(four_subtype(f, val101), SUB, n_boot=0)["auc_macro"])
    if vals:
        four_val[name] = vals

# ============================================================ T4 ablation
def val_runs(exp):
    return [load(f)["auc_macro"] for f in sorted(Path(f"reports/stage2/val/{exp}").glob("*/metrics_val.json"))]


steps = [("E0-patient (4 subtypes)", "E0 (Xception, 224 px, leaky metadata) on the patient split, scored on 4 subtypes", "four:E0-patient"),
         ("E0-clean (4 subtypes)", "E0-clean (both fixes), scored on 4 subtypes", "four:E0-clean"),
         ("E1-224", "EfficientNet-B3, MLO only, 224 px, age + lesion type", "E1-224"),
         ("E1", "image size 224 → 512 px", "E1"),
         ("E2", "+ CC view with View Attention", "E2"),
         ("E3", "+ MLO lesion crop (TOMPEI mask)", "E3"),
         ("E4", "+ radiomics branch (20 features + box flag)", "E4"),
         ("E5", "concatenation → Gated Fusion", "E5"),
         ("E6", "E5 trained as a 5-fold CV ensemble", "E6")]
r = []
for label, what, key in steps:
    if key.startswith("four:"):
        n = key[5:]
        a, vv = four.get(n), four_val.get(n)
        if a is None:
            r.append({"experiment": label, "what changed": what + " — NOT RUN"})
            continue
    else:
        a, vv = abl["stage2"][key]["averaged"], val_runs(key)
    r.append({"experiment": label, "what changed": what,
              "val macro AUC (mean ± std)": f"{np.mean(vv):.3f} ± {np.std(vv, ddof=1):.3f} (n={len(vv)})" if vv else "–",
              "test macro AUC (95% CI)": ci(a["auc_macro"], a.get("auc_macro_ci95")),
              **{f"test {c}": f"{a[f'auc_{c}']:.3f}" for c in SUB}})
r.append({"experiment": "Paper (5-class model, leaky protocol)", "what changed": "for reference only — not comparable",
          "val macro AUC (mean ± std)": "", "test macro AUC (95% CI)": "", **{f"test {c}": f"{PAPER[c]:.2f}" for c in SUB}})
table("t4_ablation", "Stage 2 ablation, 4 subtypes, the same 101 test patients", pd.DataFrame(r),
      ["reports/stage2/test/metrics_test.json", "reports/stage2/val/<experiment>/*/metrics_val.json",
       "E0 rows: reports/stage2/test/test_E0-patient.csv, reports/stage2/test_e0clean/test_E0-clean.csv, reports/stage2/val/E0-*/seed*/val_predictions.csv (re-scored here: benign column dropped, subtypes renormalised, CC and MLO averaged per breast)"],
      "Test class sizes: LumA 21, LumB 51, HER2 19, TN 10 patients. Each row adds one change to the row above it (from E1-224 on).")

# ============================================================ T5 chained
r = [{"model": "Ours: Stage 1 v2 → E6, soft chaining (test)", "breasts": chain["n_samples"],
      "micro AUC": ci(chain["auc_micro"], chain["auc_micro_ci95"]), "macro AUC": ci(chain["auc_macro"], chain["auc_macro_ci95"]),
      **{c: ci(chain[f"auc_{c}"], chain[f"auc_{c}_ci95"]) for c in FIVE}},
     {"model": "Paper (leaky protocol)", "breasts": "406 images", "micro AUC": f"{PAPER['micro']:.3f}",
      "macro AUC": f"≈{np.mean([PAPER[c] for c in FIVE]):.3f}", **{c: f"{PAPER[c]:.2f}" for c in FIVE}}]
table("t5_chained", "Chained Stage 1 → Stage 2, one 5-class probability per breast", pd.DataFrame(r),
      ["reports/stage2/test/chained_5class_metrics.json", "reports/ablation_table.md §3"],
      "82 benign test breasts + 101 subtyped test patients; P(subtype) = p(malignant) × Stage 2 probability; benign breasts "
      "have no lesion mask, so 1/4 per subtype. Subtype AUCs here count benign breasts as negatives and are higher than T4's.")

# ============================================================ T6 ours vs paper
r = [("Data", "CMMD, 4,056 images (we reproduce 4,040 by labelling per patient)", "CMMD + TOMPEI-CMMD; Stage 1 3,712 images (1,856 breasts), Stage 2 671 patients, E0 2,590 images"),
     ("Labels", "per patient: both breasts get the patient's subtype (1,458 images of unlabelled breasts)", "per breast, CMMD rows with TOMPEI left/right corrections; 16 TOMPEI-excluded breasts dropped"),
     ("Split", "image-wise 72/18/10 (198 of 260 E0 test images have a sibling image in train)", "patient-wise 70/15/15, one assignment for both stages, stratified incl. TOMPEI class"),
     ("Metadata", "age ≥ 40, tumour class set from the image's folder: benign = 0 for every benign image", "age + real CMMD lesion type for every breast"),
     ("Lesion localisation", "none (whole image, 224 px)", "TOMPEI outline → MLO lesion crop and radiomics at a common 0.211 mm pixel size"),
     ("Benign class", "inside one 5-class model; AUC 1.00 (the metadata gives it away)", f"separate Stage 1 model: AUC {ci(v2['auc'], v2['auc_ci95'])}"),
     ("Headline metric", "micro-average AUC (Keras AUC on one-hot labels), last of 10 epochs", "macro and per-class AUC with patient bootstrap CIs; micro also reported"),
     ("Result", f"{PAPER['micro']:.3f} micro AUC (5 classes)",
      f"their protocol re-run (E0-paperdata) {e0m('E0-paperdata')['auc_micro']:.3f}; leak removed (E0-truemeta) {e0m('E0-truemeta')['auc_micro']:.3f}; "
      + (f"both fixes (E0-clean) {e0m('E0-clean')['auc_micro']:.3f}; " if e0m('E0-clean') else "")
      + f"our chained 5-class {chain['auc_micro']:.3f} micro / {chain['auc_macro']:.3f} macro; subtype-only (E1–E6) "
      f"{min(abl['stage2'][e]['averaged']['auc_macro'] for e in ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']):.2f}–{max(abl['stage2'][e]['averaged']['auc_macro'] for e in ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']):.2f} macro")]
table("t6_ours_vs_paper", "Our work compared with the baseline paper", pd.DataFrame(r, columns=["aspect", "paper (Ben Rabah et al. 2025)", "ours"]),
      ["docs/baseline_paper_notes.md", f"{REPO_URL} (checked {REPO_CHECKED})", "reports/08_e0_eligibility.md",
       "reports/ablation_table.md", "reports/stage1_v2/metrics_test.json", "PROGRESS.md (tasks 03, 04, 07, 08)"])


# ============================================================ figures
def save(fig, name):
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)


# ---- F1 flowchart
def box(ax, x, y, w, h, text, bold=False, fill="white"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.008,rounding_size=0.01",
                                fc=fill, ec="black", lw=0.8))
    ax.text(x, y, text, ha="center", va="center", fontsize=7.2, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8, lw=0.8, color="black"))


lab = pairs[pairs["cmmd_class"].notna()]
st1 = pairs[pairs["in_stage1"]]
excl = lab[lab["t_class"] == "Exclusion"]
sub_s1 = st1[st1["subtype"].notna()]
mal_nosub = st1[(st1["label"] == 1) & st1["subtype"].isna()]
st2 = pairs[pairs["in_stage2"]]
lost = sub_s1[~sub_s1["in_stage2"]]
fig, ax = plt.subplots(figsize=(7.2, 8.0))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
M, MW, SX, SW = 0.33, 0.52, 0.83, 0.32   # main column x and width, side column x and width
n_unl = int(pairs.cmmd_class.isna().sum())
n_e0 = int((st1.label == 0).sum()) + len(sub_s1)
sub_counts = " · ".join(f"{s} {(st2.subtype == f).sum()}" for s, f in zip(SUB, ["Luminal A", "Luminal B", "HER2-enriched", "triple negative"]))
box(ax, M, 0.95, MW, 0.055, f"CMMD: {2 * len(pairs):,} images\n{len(pairs):,} breasts · {pairs.patient_id.nunique():,} patients", True)
box(ax, M, 0.84, MW, 0.055, f"Paired CC + MLO per breast\n{len(pairs):,} breasts (0 missing a view)")
box(ax, SX, 0.775, SW, 0.06, f"Excluded: no CMMD label\n{n_unl} breasts · {2 * n_unl:,} images")
box(ax, M, 0.71, MW, 0.045, f"Labelled breasts: {len(lab):,}")
box(ax, SX, 0.645, SW, 0.06, f"Excluded: TOMPEI recommends\nexclusion: {len(excl)} breasts · {2 * len(excl)} images")
box(ax, M, 0.565, MW, 0.075, f"Stage 1 set\n{len(st1):,} breasts · {2 * len(st1):,} images · {st1.patient_id.nunique():,} patients\n"
                              f"benign {(st1.label == 0).sum():,} / malignant {(st1.label == 1).sum():,}", True, "0.92")
box(ax, 0.17, 0.36, 0.32, 0.10, f"E0 set (5 classes)\nbenign or with a subtype\n{n_e0:,} breasts · {2 * n_e0:,} images\n"
                                 f"(minus {len(mal_nosub)} malignant without subtype)", True, "0.92")
box(ax, 0.58, 0.39, 0.34, 0.05, f"Malignant with a subtype\n{len(sub_s1)} breasts")
box(ax, SX + 0.03, 0.255, 0.26, 0.06, f"Excluded: no lesion outline\n{len(lost)} breasts (TOMPEI 'Invisible')")
box(ax, 0.58, 0.12, 0.40, 0.09, f"Stage 2 set (E1–E6)\n{len(st2)} patients · {2 * len(st2):,} images\n{sub_counts}", True, "0.92")
for (x0, y0, x1, y1) in [(M, 0.922, M, 0.868), (M, 0.812, M, 0.733), (M, 0.687, M, 0.603), (M, 0.527, 0.17, 0.41),
                         (M, 0.527, 0.58, 0.415), (0.58, 0.365, 0.58, 0.165), (M, 0.775, SX - SW / 2, 0.775),
                         (M, 0.645, SX - SW / 2, 0.645), (0.58, 0.255, SX + 0.03 - 0.13, 0.255)]:
    arrow(ax, x0, y0, x1, y1)
save(fig, "f1_flowchart")

# ---- F2 class distribution per split
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1, 1.5]})
for ax, (title, groups, col) in zip(axes, [("Stage 1: breasts per split", ["benign", "malignant"], "Stage 1 (benign vs malignant)"),
                                           ("Stage 2: patients per split", SUB, "Stage 2 (subtype; E1–E6)")]):
    d = t1[(t1["set"] == col) & t1["split"].isin(SPL)]
    x = np.arange(len(SPL))
    w = 0.8 / len(groups)
    for i, g in enumerate(groups):
        vals = [int(d[(d.split == s) & (d["class"] == g)]["breasts"].iloc[0]) for s in SPL]
        bars = ax.bar(x + (i - (len(groups) - 1) / 2) * w, vals, w * 0.92, color=GREYS[i % 4], edgecolor="black",
                      linewidth=0.5, hatch=HATCH[i % 5], label=g)
        for b_, v in zip(bars, vals):
            ax.text(b_.get_x() + b_.get_width() / 2, v, str(v), ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(x, SPL)
    ax.set_title(title)
    ax.set_ylabel("count")
    ax.legend(frameon=False, ncol=2 if len(groups) > 2 else 1, loc="upper right")
fig.tight_layout()
save(fig, "f2_class_distribution")


# ---- F3 architecture diagrams
def arch(ax, title, blocks, arrows_, xlim=(0, 10), ylim=(0, 6)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
    for (x, y, w, h, t, fill) in blocks:
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc=fill, ec="black", lw=0.8))
        ax.text(x, y, t, ha="center", va="center", fontsize=7.2, linespacing=1.2)
    for (x0, y0, x1, y1) in arrows_:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8, lw=0.8, color="black"))


fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4), gridspec_kw={"height_ratios": [1, 1.35]})
W = "white"
G = "0.9"
arch(axes[0], "(a) Stage 1 — benign vs malignant (per breast)",
     [(0.9, 4.2, 1.5, 0.8, "CC view\n512 px", W), (0.9, 2.2, 1.5, 0.8, "MLO view\n512 px", W),
      (3.2, 3.2, 1.9, 1.4, "EfficientNet-B3\n(shared weights,\nImageNet)", G),
      (5.4, 3.2, 1.6, 1.2, "View Attention\nsoftmax weights\nCC / MLO", W), (0.9, 0.7, 1.5, 0.7, "Age", W),
      (3.2, 0.7, 1.9, 0.7, "MLP 1 → 32", W), (7.2, 2.2, 1.4, 1.0, "Concat\n1536 + 32", W),
      (9.0, 2.2, 1.6, 1.0, "Dropout\n→ 2 classes", G)],
     [(1.65, 4.2, 2.25, 3.5), (1.65, 2.2, 2.25, 2.9), (4.15, 3.2, 4.6, 3.2), (6.2, 3.0, 6.5, 2.4),
      (1.65, 0.7, 2.25, 0.7), (4.15, 0.7, 6.5, 2.0), (7.9, 2.2, 8.2, 2.2)], ylim=(0, 5))
arch(axes[1], "(b) Stage 2 — molecular subtype, E5 (E6 = 5-fold ensemble of E5)",
     [(0.9, 5.6, 1.5, 0.75, "CC view\n512 px", W), (0.9, 4.4, 1.5, 0.75, "MLO view\n512 px", W),
      (0.9, 3.1, 1.5, 0.9, "MLO lesion crop\n(TOMPEI mask\n+20 px) 224 px", W),
      (3.2, 4.4, 1.9, 2.6, "EfficientNet-B3\n(one shared\nencoder for all\nthree images)", G),
      (5.5, 5.0, 1.7, 0.9, "View Attention\nCC / MLO", W), (5.5, 3.6, 1.7, 0.8, "crop features", W),
      (7.3, 4.3, 1.3, 1.2, "Image\n2×1536 → 512", W),
      (0.9, 1.6, 1.5, 0.75, "Radiomics\n20 + box flag", W), (3.2, 1.6, 1.9, 0.75, "MLP 21 → 64", W),
      (0.9, 0.5, 1.5, 0.75, "Age + lesion\ntype (4)", W), (3.2, 0.5, 1.9, 0.75, "MLP 4 → 32", W),
      (7.3, 1.8, 1.3, 1.6, "Gated Fusion\none 0–1 gate\nper modality", G), (9.1, 1.8, 1.4, 1.0, "Dropout\n→ 4 subtypes", G)],
     [(1.65, 5.6, 2.25, 5.0), (1.65, 4.4, 2.25, 4.4), (1.65, 3.1, 2.25, 3.6), (4.15, 5.0, 4.65, 5.0),
      (4.15, 3.6, 4.65, 3.6), (6.35, 5.0, 6.65, 4.6), (6.35, 3.6, 6.65, 4.0), (7.3, 3.7, 7.3, 2.6),
      (1.65, 1.6, 2.25, 1.6), (4.15, 1.6, 6.65, 1.7), (1.65, 0.5, 2.25, 0.5), (4.15, 0.5, 6.65, 1.3),
      (7.95, 1.8, 8.4, 1.8)], ylim=(0, 6.2))
fig.tight_layout()
save(fig, "f3_architecture")

# ---- F4 training curves
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.0))
logs = [pd.read_csv(f) for f in sorted(Path("reports/stage1_v2/cv_r3").glob("fold*/training_log.csv"))]
for k, lg in enumerate(logs):
    axes[0, 0].plot(lg.epoch, lg.train_loss, color="0.15", ls=STYLES[k], lw=0.9, label="training (5 folds)" if k == 0 else None)
    axes[0, 0].plot(lg.epoch, lg.val_loss, color="0.6", ls=STYLES[k], lw=0.9, label="validation (5 folds)" if k == 0 else None)
    axes[0, 1].plot(lg.epoch, lg.val_auc, color="0.2", ls=STYLES[k], marker=MARKERS[k], ms=3, lw=0.9, label=f"fold {k}")
axes[0, 0].set(title="(a) Stage 1 v2 (R3, 5 folds): loss", xlabel="epoch", ylabel="weighted cross-entropy")
axes[0, 1].set(title="(b) Stage 1 v2: validation AUC (held-out fold)", xlabel="epoch", ylabel="AUC")
axes[0, 0].legend(frameon=False, loc="lower left", fontsize=7)
axes[0, 1].legend(frameon=False, fontsize=6.5)
logs5 = {f.parent.name: pd.read_csv(f) for f in sorted(Path("reports/stage2/val/E5").glob("seed*/training_log.csv"))}
for k, (sd, lg) in enumerate(logs5.items()):
    axes[1, 0].plot(lg.epoch, lg.train_loss, color="0.2", ls=STYLES[k], marker=MARKERS[k], ms=3, lw=0.9, label=sd)
    axes[1, 1].plot(lg.epoch, lg.val_auc_macro, color="0.2", ls=STYLES[k], marker=MARKERS[k], ms=3, lw=0.9, label=sd)
axes[1, 0].set(title="(c) Stage 2 E5: training loss (val loss not logged)", xlabel="epoch", ylabel="cross-entropy (smoothed labels)")
axes[1, 1].set(title="(d) Stage 2 E5: validation macro AUC", xlabel="epoch", ylabel="macro AUC")
axes[1, 1].axhline(0.5, color="0.6", lw=0.6, ls=":")
for a_ in axes.ravel():
    a_.grid(True, axis="y")
    a_.legend(frameon=False, fontsize=6.5) if a_ in (axes[1, 0], axes[1, 1]) else None
fig.tight_layout()
save(fig, "f4_training_curves")
notes.append("F4: Stage 2 (E5) training logs record training loss and validation AUC but NOT validation loss "
             "(`src/stage2.py` never logged it), so panel (c) shows training loss only. Stage 1 v2 logs are complete.")


# ---- F5 ROC curves
def roc_panel(ax, frames, classes, title):
    for k, c in enumerate(classes):
        for j, (lab_, t) in enumerate(frames):
            y = (t["y"] == {**{n: i for i, n in enumerate(t.attrs["classes"])}}[c]).astype(int)
            fpr, tpr, _ = roc_curve(y, t[f"p_{c}"])
            ax[k].plot(fpr, tpr, color=["0.1", "0.55"][j], ls=["-", "--"][j], lw=1.1, label=lab_)
        ax[k].plot([0, 1], [0, 1], color="0.75", lw=0.6, ls=":")
        ax[k].set(title=c, xlabel="1 − specificity", aspect="equal", xlim=(0, 1), ylim=(0, 1))
    ax[0].set_ylabel("sensitivity")


e0_order = ["Benign", "HER2", "LumA", "LumB", "TN"]
frames = []
for lab_, csv in [("E0 (leaky metadata, image-wise)", "reports/stage2/test/test_E0.csv"),
                  ("E0-clean (both fixes)", "reports/stage2/test_e0clean/test_E0-clean.csv")]:
    if Path(csv).exists():
        t = pd.read_csv(csv)
        t.attrs["classes"] = e0_order
        frames.append((lab_, t))
if len(frames) == 2:
    fig, ax = plt.subplots(2, 5, figsize=(7.4, 4.4))
    roc_panel(ax[0], frames, FIVE, "")
    ch = pd.read_csv("reports/stage2/test/chained_5class.csv")
    ch.attrs["classes"] = FIVE
    roc_panel(ax[1], [("chained Stage 1 → E6", ch)], FIVE, "")
    fig.subplots_adjust(top=0.80, bottom=0.10, hspace=0.85, wspace=0.55, left=0.07, right=0.99)
    h, l = ax[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=2, frameon=False, fontsize=7.5)
    fig.text(0.01, 0.875, "(a) E0 vs E0-clean, one-vs-rest ROC (test)", fontsize=9, fontweight="bold")
    fig.text(0.01, 0.43, "(b) chained Stage 1 → E6, one-vs-rest ROC (test)", fontsize=9, fontweight="bold")
    save(fig, "f5_roc_e0_chained")
else:
    notes.append("F5: skipped — E0-clean test predictions are not available.")

# ---- F6 Stage 1 ROC with operating points
t2v = pd.read_csv("reports/stage1_v2/test_predictions.csv")
t1v = pd.read_csv("reports/stage1/test_predictions.csv")
fig, ax = plt.subplots(figsize=(3.6, 3.6))
for t, lab_, col, ls in [(t2v, f"v2 ensemble, AUC {v2['auc']:.3f}", "0.1", "-"), (t1v, f"v1 single model, AUC {v1['auc']:.3f}", "0.55", "--")]:
    fpr, tpr, _ = roc_curve(t["label"], t["prob"])
    ax.plot(fpr, tpr, color=col, ls=ls, lw=1.2, label=lab_)
for name, mk, lab_ in [("youden", "o", "Youden"), ("oof_sens90", "s", "≥90% sensitivity (OOF)")]:
    o = op(v2, name)
    ax.plot(1 - o["test"]["specificity"], o["test"]["sensitivity"], marker=mk, ms=7, mfc="white", mec="black", mew=1.2, ls="none",
            label=f"{lab_}: thr {o['threshold']:.3f}\n  sens {o['test']['sensitivity']:.2f}, spec {o['test']['specificity']:.2f}")
ax.plot([0, 1], [0, 1], color="0.75", lw=0.6, ls=":")
ax.set(xlabel="1 − specificity", ylabel="sensitivity", aspect="equal", xlim=(0, 1), ylim=(0, 1),
       title="Stage 1 test ROC (279 breasts)")
ax.legend(frameon=False, loc="lower right", fontsize=6.5)
save(fig, "f6_stage1_roc")

# ---- F7 leak ladder bars
F7_ORDER = [None, "E0-paperdata", "E0", "E0-meta", "E0-patient", "E0-truemeta", "E0-clean"]
label_of = {k: l for l, _, k in ladder}
lad = [(label_of[k], k) for k in F7_ORDER if k is None or e0m(k) is not None]
names = [l for l, _ in lad]
micro = [PAPER["micro"] if k is None else e0m(k)["auc_micro"] for _, k in lad]
macro = [np.mean([PAPER[c] for c in FIVE]) if k is None else e0m(k)["auc_macro"] for _, k in lad]
fig, ax = plt.subplots(figsize=(7.2, 3.0))
x = np.arange(len(names))
for i, (vals, lab_) in enumerate([(micro, "micro AUC"), (macro, "macro AUC")]):
    bars = ax.bar(x + (i - 0.5) * 0.38, vals, 0.36, color=GREYS[i * 2], edgecolor="black", linewidth=0.5, hatch=HATCH[i], label=lab_)
    for b_, v in zip(bars, vals):
        ax.text(b_.get_x() + b_.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=6.5)
ax.axhline(0.5, color="0.4", lw=0.7, ls=":")
ax.text(-0.62, 0.505, "chance", fontsize=6.5, ha="left", va="bottom", color="0.3")
# dashed divider between the runs that keep the metadata leak and those that remove it
split_at = [k for _, k in lad].index("E0-truemeta") - 0.5
ax.axvline(split_at, color="0.2", lw=0.9, ls="--")
ax.text(split_at - 0.08, 0.975, "leak kept", ha="right", va="top", fontsize=8, fontstyle="italic")
ax.text(split_at + 0.08, 0.975, "leak removed", ha="left", va="top", fontsize=8, fontstyle="italic")
ax.set_xticks(x, [n.replace(" (published)", "\n(published)") for n in names], fontsize=7.5)
ax.set(ylim=(0.4, 1.0), xlim=(-0.65, len(names) - 0.35), ylabel="test AUC (5 classes)",
       title="The leak ladder: from the paper's protocol to a clean evaluation")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
ax.grid(True, axis="y")
save(fig, "f7_leak_ladder")

# ---- F8 E1 -> E6 macro AUC with CIs
exps = ["E1-224", "E1", "E2", "E3", "E4", "E5", "E6"]
fig, ax = plt.subplots(figsize=(5.2, 3.0))
vals = [abl["stage2"][e]["averaged"]["auc_macro"] for e in exps]
cis = [abl["stage2"][e]["averaged"]["auc_macro_ci95"] for e in exps]
vm = [np.mean(val_runs(e)) for e in exps]
x = np.arange(len(exps))
ax.errorbar(x, vals, yerr=[[v - c[0] for v, c in zip(vals, cis)], [c[1] - v for v, c in zip(vals, cis)]], fmt="o", color="black",
            ms=5, capsize=3, lw=0.9, label="test (95% CI)")
ax.plot(x + 0.15, vm, "s", mfc="white", mec="0.35", ms=5, ls="none", label="validation (mean of seeds/folds)")
for xi, v in zip(x, vals):
    ax.text(xi - 0.12, v, f"{v:.2f}", ha="right", va="center", fontsize=6.5)
ax.axhline(0.5, color="0.4", lw=0.7, ls=":")
ax.set_xticks(x, exps)
ax.set(ylim=(0.3, 0.8), xlim=(-0.7, len(exps) - 0.4), ylabel="macro AUC (4 subtypes)", title="Stage 2 ablation: 101 test patients")
ax.legend(frameon=False, loc="upper left", fontsize=7)
ax.grid(True, axis="y")
save(fig, "f8_ablation_ci")

# ============================================================ key findings + write tables.md
def a_(name):
    return e0m(name) or {}


e5t, e6t = abl["stage2"]["E5"]["averaged"], abl["stage2"]["E6"]["averaged"]
cl = a_("E0-clean")
kf = [
    f"1. Benign vs malignant (Stage 1): our final model reaches a test AUC of {v2['auc']:.2f} ({v2['auc_ci95'][0]:.2f}–{v2['auc_ci95'][1]:.2f}) on {v2['n_breasts']} breasts, judged honestly on unseen patients.",
    f"2. At a threshold set to catch 90% of cancers it finds {op(v2, 'oof_sens90')['test']['sensitivity']:.0%} of test cancers but clears only {op(v2, 'oof_sens90')['test']['specificity']:.0%} of benign breasts. Dense breasts score {op(v2, 'youden')['test_subgroups']['dense_breasts']['auc']:.2f} against {op(v2, 'youden')['test_subgroups']['non_dense_breasts']['auc']:.2f} for non-dense; cancers no radiologist could locate ('Invisible') are hardest at {op(v2, 'youden')['test_subgroups']['invisible_cancers_vs_all_benign']['auc']:.2f}.",
    f"3. The improved Stage 1 recipe beat the first model by {cmp12['difference']:+.3f} AUC, but the difference is within noise (95% CI {cmp12['difference_ci95'][0]:+.3f} to {cmp12['difference_ci95'][1]:+.3f}).",
    f"4. The baseline paper's code is public. It sets the 'tumour type' input to 'none' for every benign image, so the model is told which images are benign.",
    f"5. Re-running their exact protocol we get {a_('E0-paperdata')['auc_micro']:.2f} micro AUC, close to their published {PAPER['micro']:.2f}; their 88.87% is a micro average, which an easy class inflates.",
    f"6. That leaked input alone, with no mammogram at all, scores {a_('E0-meta')['auc_micro']:.2f} micro AUC and a perfect {a_('E0-meta')['auc_Benign']:.2f} for benign.",
    f"7. Giving benign breasts their real lesion type drops the same model to {a_('E0-truemeta')['auc_micro']:.2f} micro AUC"
    + (f"; with a patient-wise split as well (E0-clean) it is {cl['auc_micro']:.2f} micro / {cl['auc_macro']:.2f} macro." if cl else "."),
    f"8. The paper also labelled both breasts of a patient with the tumour's subtype (1,458 images of breasts with no labelled cancer); with correct per-breast labels the leaky model scores {a_('E0')['auc_micro']:.2f}, not lower, so the metadata leak, not the labelling, drives the headline.",
    f"9. Predicting the molecular subtype from the image is genuinely hard: on 101 test patients our best models reach a macro AUC of {e5t['auc_macro']:.2f} (E5, gated fusion) and {e6t['auc_macro']:.2f} (E6), and no added component is shown to help beyond noise"
    + (f"; the leaky baseline scores {four['E0-patient']['auc_macro']:.2f} on the same 4-subtype task." if "E0-patient" in four else "."),
    f"10. Chaining the two stages gives an honest 5-class result of {chain['auc_micro']:.2f} micro / {chain['auc_macro']:.2f} macro AUC — lower than the paper's headline, but free of the label leak, the image-wise split and the per-patient labelling.",
]
(OUT / "key_findings.md").write_text("# Key findings (for the synopsis)\n\n" + "\n".join(kf) + "\n\nEvery number above is taken by "
                                     "`scripts/08b_synopsis.py` from the files listed under tables T2–T5.\n", encoding="utf-8")
md.extend(["## Key findings", ""] + kf + [""])
v1_row = pd.DataFrame([{"measure": "v1 test AUC", "v2 (final)": f"{v1['auc']:.3f}"}])
t2_short = pd.concat([t2[["measure", "v2 (final)"]].iloc[:1], v1_row, t2[["measure", "v2 (final)"]].iloc[1:]], ignore_index=True)
t2_short = t2_short[t2_short["v2 (final)"] != ""].rename(columns={"v2 (final)": "Stage 1 v2 (final)"})
t3_short = t3[["run", "micro AUC", "macro AUC", "Benign"]].rename(columns={"Benign": "Benign AUC"})
t2_short.to_csv(OUT / "t2_stage1_short.csv", index=False)
t3_short.to_csv(OUT / "t3_leak_ladder_short.csv", index=False)
(OUT / "tables_short.md").write_text("\n".join([
    "# Synopsis-width tables (shortened T2 and T3; same numbers as tables.md)", "",
    "## T2 (short): Stage 1 test results, 279 breasts / 265 patients", "", t2_short.to_markdown(index=False), "",
    "Sources: `reports/stage1_v2/metrics_test.json`; `reports/stage1/metrics_test.json` (v1 AUC); "
    "`reports/stage1_v2/compare_v1_v2_test.json`", "",
    "## T3 (short): the leak ladder (5 classes, test, average of 3 seeds)", "", t3_short.to_markdown(index=False), "",
    "Sources: `docs/baseline_paper_notes.md` (paper); `reports/stage2/test/metrics_test.json`; "
    "`reports/stage2/test_e0clean/metrics_test.json`", ""]), encoding="utf-8")

FIGS = [
    ("f1_flowchart.png", "Inclusion and exclusion: from 5,202 CMMD images to the Stage 1, E0 and Stage 2 sets.", "data/index/pairs.csv (task 04), cross-check reports/04_data_flow.md"),
    ("f2_class_distribution.png", "Class distribution per split: Stage 1 breasts (left), Stage 2 patients (right).", "t1_dataset.csv (from data/splits/stage1.csv, stage2.csv)"),
    ("f3_architecture.png", "Block diagrams of Stage 1 and Stage 2 (E5; E6 is the 5-fold ensemble of E5).", "src/models.py, src/stage2.py"),
    ("f4_training_curves.png", "Training and validation curves: Stage 1 v2 (5 CV folds of recipe R3) and Stage 2 E5 (3 seeds).", "reports/stage1_v2/cv_r3/fold*/training_log.csv, reports/stage2/val/E5/seed*/training_log.csv"),
    ("f5_roc_e0_chained.png", "One-vs-rest test ROC: (a) E0 (its 260 image-wise test images) vs E0-clean (its 388 patient-wise test images); (b) the chained 5-class model (183 breasts).", "reports/stage2/test/test_E0.csv, reports/stage2/test_e0clean/test_E0-clean.csv, reports/stage2/test/chained_5class.csv"),
    ("f6_stage1_roc.png", "Stage 1 test ROC (v2 and v1) with the two operating points of v2, both chosen on out-of-fold predictions.", "reports/stage1_v2/test_predictions.csv, reports/stage1/test_predictions.csv, reports/stage1_v2/metrics_test.json"),
    ("f7_leak_ladder.png", "The leak ladder: test micro and macro AUC from the paper's protocol to a clean evaluation.", "t3_leak_ladder.csv"),
    ("f8_ablation_ci.png", "Stage 2 ablation: test macro AUC with 95% CI (dots) and validation mean (squares).", "reports/stage2/test/metrics_test.json, reports/stage2/val/*/*/metrics_val.json"),
]
md.extend(["## Figures (300 dpi PNG, black and white)", "", "| file | caption | source |", "|---|---|---|"]
          + [f"| `{f}` | {c} | `{s}` |" for f, c, s in FIGS] + [""])
findings = Path(OUT / "key_findings.md")
head = ["# Synopsis tables (task 08b)", "",
        "All numbers are copied by `scripts/08b_synopsis.py` from saved files (listed under each table); nothing is retyped.",
        f"Baseline code: {REPO_URL} (public; checked {REPO_CHECKED}; read for the method, no code copied).", ""]
(OUT / "tables.md").write_text("\n".join(head + md + (["## Figure notes", ""] + [f"- {n}" for n in notes] if notes else [])) + "\n", encoding="utf-8")
print("\n".join(head + md))
print("figure notes:", notes)
print("four-subtype test:", {k: round(v["auc_macro"], 3) for k, v in four.items()}, "| val:", {k: np.round(v, 3).tolist() for k, v in four_val.items()})
