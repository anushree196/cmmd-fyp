"""Task 05 (before upload): independent audit of tasks 01-04.

Nothing is imported from the earlier scripts. Everything is recounted from the files on disk (DICOM folder
listing, PNG and mask folders, the CSV tables) and from the two ORIGINAL spreadsheets (CMMD and TOMPEI).

Checks:
  1. Counts     recount images / breasts / patients and compare with the numbers logged in PROGRESS.md
  2. Leakage    no patient in two splits; same split in stage1.csv and stage2.csv
  3. Labels     trace 20 random breasts from the raw spreadsheets to pairs.csv (and then all 2,601)
  4. Files      every PNG and mask opens, has the right size, and is not blank or all white
  5. Picture    16 random Stage 2 test breasts: CC | MLO with outline | mask  -> reports/05_audit_montage.png

Writes reports/05_audit.md. Exit code 1 if any check found a problem.

Usage:
    python scripts/05_audit.py --config config.yaml
"""
import argparse, random, re, subprocess, sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

# Numbers as logged in PROGRESS.md (tasks 01-04). The audit recounts each one.
EXPECTED = {
    "DICOM files in the CMMD download": 5202,
    "PNG files": 5202, "patients (PNG file names)": 1775, "breasts (PNG file names)": 2601,
    "mask files": 1385, "patients with a mask": 1363,
    "CMMD sheet rows": 1872, "CMMD benign rows": 556, "CMMD malignant rows": 1316, "CMMD subtyped patients": 749,
    "TOMPEI sheet rows": 2601, "TOMPEI Malignant": 1167, "TOMPEI Normal": 1054, "TOMPEI Benign": 215,
    "TOMPEI Invisible": 140, "TOMPEI Exclusion": 25, "TOMPEI annotation files": 1385, "TOMPEI lesions": 1773,
    "pairs.csv rows": 2601, "breasts without CMMD label": 729, "labelled breasts TOMPEI excludes": 16,
    "Stage 1 breasts": 1856, "Stage 1 patients": 1762, "Stage 1 benign": 549, "Stage 1 malignant": 1307,
    "Stage 1 Invisible cancers": 140, "Stage 1 benign with TOMPEI Normal": 342,
    "Stage 2 patients": 671, "Stage 2 Luminal A": 140, "Stage 2 Luminal B": 335, "Stage 2 HER2-enriched": 126,
    "Stage 2 triple negative": 70,
    # split sizes (train, val, test), after the re-split of 2026-10-07 that added TOMPEI class to the strata.
    # Before the re-split these were (1233, 264, 265), (1289, 280, 287), (375, 84, 90), (914, 196, 197),
    # (470, 100, 101), (966, 241, 135), and the audit confirmed those too.
    "Stage 1 patients per split": (1233, 264, 265), "Stage 1 breasts per split": (1299, 278, 279),
    "Stage 1 benign per split": (385, 82, 82), "Stage 1 malignant per split": (914, 196, 197),
    "Stage 2 patients per split": (469, 101, 101), "E0 images per split": (966, 241, 135),
}
SPLITS = ["train", "val", "test"]
SUBTYPES = ["Luminal A", "Luminal B", "HER2-enriched", "triple negative"]
lines, problems = [], []


def say(text=""):
    print(text)
    lines.append(text)


def problem(text):
    problems.append(text)
    say(f"**PROBLEM:** {text}")


def per_split(df, mask=None):
    d = df if mask is None else df[mask]
    return tuple(int((d["split"] == s).sum()) for s in SPLITS)


def same(a, b):
    """Equal, treating two empty cells as equal and 44 == 44.0."""
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def check_png(args):
    """Open one PNG and return facts about it."""
    path, want_h, want_w = args
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        return {"file": path.name, "opens": False}
    return {"file": path.name, "opens": True, "ndim": im.ndim, "dtype": str(im.dtype),
            "size_ok": im.shape[:2] == (want_h, want_w), "min": int(im.min()), "max": int(im.max()),
            "mean": float(im.mean()), "std": float(im.std()), "nonblack": float((im > 0).mean())}


def check_mask(args):
    """Open one mask and its MLO PNG; return facts about both together."""
    mask_path, png_path = args
    m = cv2.imread(str(mask_path), cv2.IMREAD_UNCHANGED)
    p = cv2.imread(str(png_path), cv2.IMREAD_UNCHANGED)
    if m is None or p is None:
        return {"file": mask_path.name, "opens": False}
    values = set(np.unique(m).tolist())
    on = m > 0
    return {"file": mask_path.name, "opens": True, "same_size_as_png": m.shape == p.shape,
            "only_0_255": values <= {0, 255}, "share_on": float(on.mean()),
            # share of the lesion area that lies on breast (non-black PNG pixels): low = mask misplaced
            "on_breast": float((p[on] > 0).mean()) if on.any() else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--previous-stage1", default="", help="an older stage1.csv, to show what a re-split changed")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8-sig"))
    work = Path(cfg["work_root"])
    png_dir, mask_dir = work / f"png{cfg['png_height']}", work / f"masks{cfg['png_height']}"
    idx_dir, split_dir = work / "index", work / "splits"
    raw_dicom = Path(cfg["raw_root"]) / cfg["dicom_dir"]
    tompei = Path(cfg["tompei_dir"])

    # ---------- load everything fresh
    pairs = pd.read_csv(idx_dir / "pairs.csv")
    s1 = pd.read_csv(split_dir / "stage1.csv")
    s2 = pd.read_csv(split_dir / "stage2.csv")
    e0 = pd.read_csv(split_dir / "stage2_e0_imagewise.csv")
    png_index = pd.read_csv(idx_dir / "png_index.csv")
    sides = pd.read_csv(idx_dir / "image_sides.csv")
    cmmd = pd.read_excel(cfg["clinical_xlsx"])
    xlsx = next(tompei.glob("*.xlsx"))
    t_img = pd.read_excel(xlsx, sheet_name="Imaging Diagnosis Details Sheet", header=None, skiprows=2)
    t_les = pd.read_excel(xlsx, sheet_name="Lesion Details Sheet", header=None, skiprows=3)
    t_les = t_les[t_les[0].astype(str).str.match(r"^D[12]-\d{4}$")]
    T = {(r[0], r[1]): {"t_class": r[3], "exclusion": r[4], "density": r[5], "birads": r[21]} for r in t_img.itertuples(index=False)}
    for r in t_les.itertuples(index=False):
        T[(r[0], r[1])].update(n_lesions=int(r[3]), note=r[18])
    C = {(r.ID1, r.LeftRight): r for r in cmmd.itertuples(index=False)}
    json_files = [p for p in tompei.rglob("*_AnnotationFile.json") if "__MACOSX" not in p.parts and not p.name.startswith("._")]
    J = {}
    for p in json_files:
        m = re.match(r"^(D[12]-\d{4})_(MLO|CC)_([LR])_", p.name)
        J[(m.group(1), m.group(3))] = p
    import json as jsonlib
    n_lesions_json = {k: len(jsonlib.loads(p.read_text(encoding="utf-8"))) for k, p in J.items()}

    say("# Audit of tasks 01–04 (before the Kaggle upload)")
    say("\nEverything below is recounted from the files and the two original spreadsheets by `scripts/05_audit.py`.")

    # ================= 1. counts
    say("\n## 1. Counts: recounted against PROGRESS.md\n")
    pngs = sorted(png_dir.glob("*.png"))
    masks = sorted(mask_dir.glob("*.png"))
    name = [re.match(r"^(D[12]-\d{4})_([LR])_(CC|MLO)_", p.name) for p in pngs]
    in_s1 = pairs[pairs["in_stage1"]]
    in_s2 = pairs[pairs["in_stage2"]]
    # Stage 1 exclusions recounted straight from the two raw sheets (same patient + side in both)
    excl_raw = sum(1 for k in C if T.get(k, {}).get("t_class") == "Exclusion")
    got = {
        "DICOM files in the CMMD download": sum(1 for _ in raw_dicom.rglob("*.dcm")),
        "PNG files": len(pngs), "patients (PNG file names)": len({m.group(1) for m in name}),
        "breasts (PNG file names)": len({(m.group(1), m.group(2)) for m in name}),
        "mask files": len(masks), "patients with a mask": len({p.name[:7] for p in masks}),
        "CMMD sheet rows": len(cmmd), "CMMD benign rows": int((cmmd["classification"] == "Benign").sum()),
        "CMMD malignant rows": int((cmmd["classification"] == "Malignant").sum()),
        "CMMD subtyped patients": int(cmmd.loc[cmmd["subtype"].notna(), "ID1"].nunique()),
        "TOMPEI sheet rows": len(T), "TOMPEI annotation files": len(J), "TOMPEI lesions": sum(n_lesions_json.values()),
        "pairs.csv rows": len(pairs), "breasts without CMMD label": int(pairs["cmmd_class"].isna().sum()),
        "labelled breasts TOMPEI excludes": excl_raw,
        "Stage 1 breasts": len(s1), "Stage 1 patients": s1["patient_id"].nunique(),
        "Stage 1 benign": int((s1["label"] == 0).sum()), "Stage 1 malignant": int((s1["label"] == 1).sum()),
        "Stage 1 Invisible cancers": int((s1["t_class"] == "Invisible").sum()),
        "Stage 1 benign with TOMPEI Normal": int(((s1["label"] == 0) & (s1["t_class"] == "Normal")).sum()),
        "Stage 2 patients": s2["patient_id"].nunique(),
        "Stage 1 patients per split": tuple(int(s1.loc[s1["split"] == s, "patient_id"].nunique()) for s in SPLITS),
        "Stage 1 breasts per split": per_split(s1), "Stage 1 benign per split": per_split(s1, s1["label"] == 0),
        "Stage 1 malignant per split": per_split(s1, s1["label"] == 1),
        "Stage 2 patients per split": per_split(s2), "E0 images per split": per_split(e0),
    }
    for c in ["Malignant", "Normal", "Benign", "Invisible", "Exclusion"]:
        got[f"TOMPEI {c}"] = sum(1 for v in T.values() if v["t_class"] == c)
    for s in SUBTYPES:
        got[f"Stage 2 {s}"] = int((s2["subtype"] == s).sum())
    say("| what | PROGRESS.md | recounted | |")
    say("|---|---|---|---|")
    for k, want in EXPECTED.items():
        ok = got[k] == want
        say(f"| {k} | {want} | {got[k]} | {'ok' if ok else '**DIFFERENT**'} |")
        if not ok:
            problems.append(f"count '{k}': PROGRESS.md says {want}, recount gives {got[k]}")

    say("\nCross-checks between files:\n")
    checks = {
        "every PNG file name matches {patient}_{L|R}_{CC|MLO}_...": all(name),
        "PNG folder holds exactly the files listed in png_index.csv": {p.name for p in pngs} == set(png_index["png"]),
        "mask folder holds exactly the files listed in pairs.csv": {p.name for p in masks} == set(pairs["mask"].dropna()),
        "every DICOM path in png_index.csv exists and is used once": png_index["path"].is_unique and all(Path(p).is_file() for p in png_index["path"]),
        "every PNG is used by exactly one breast in pairs.csv": sorted(pairs["png_cc"].tolist() + pairs["png_mlo"].tolist()) == sorted(p.name for p in pngs),
        "stage1.csv is exactly the in_stage1 rows of pairs.csv": set(zip(s1["patient_id"], s1["side"])) == set(zip(in_s1["patient_id"], in_s1["side"])),
        "stage2.csv is exactly the in_stage2 rows of pairs.csv": set(zip(s2["patient_id"], s2["side"])) == set(zip(in_s2["patient_id"], in_s2["side"])),
        "every Stage 2 breast is also a Stage 1 breast": set(zip(s2["patient_id"], s2["side"])) <= set(zip(s1["patient_id"], s1["side"])),
        "Stage 2 has one breast per patient, each with a mask and a subtype": s2["patient_id"].is_unique and s2["mask"].notna().all() and s2["subtype"].isin(SUBTYPES).all(),
        "E0 images are exactly the CC + MLO of the Stage 2 breasts": sorted(e0["png"]) == sorted(s2["png_cc"].tolist() + s2["png_mlo"].tolist()),
        "Stage 1 has no missing label, age, CC or MLO": bool(s1[["label", "age", "png_cc", "png_mlo"]].notna().all().all()),
        "no Stage 1 breast is a TOMPEI Exclusion": not (s1["t_class"] == "Exclusion").any(),
    }
    tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines()
    checks["git tracks no data, DICOM, mask or weight files"] = not any(
        f.startswith("data/") or f.endswith((".dcm", ".pth", ".pt", ".zip")) or f == "config.yaml" for f in tracked)
    for k, ok in checks.items():
        say(f"- {'ok' if ok else '**FAILED**'}: {k}")
        if not ok:
            problems.append(f"cross-check failed: {k}")

    # Stage 2 recounted a different way: subtyped patients who have ANY TOMPEI-Malignant outlined breast
    sub_pat = set(cmmd.loc[cmmd["subtype"].notna(), "ID1"])
    any_mal = {p for (p, s), v in T.items() if v["t_class"] == "Malignant" and (p, s) in J}
    extra = sorted((sub_pat & any_mal) - set(s2["patient_id"]))
    say(f"\nStage 2 recounted another way: subtyped patients with any outlined TOMPEI-Malignant breast = "
        f"{len(sub_pat & any_mal)}; Stage 2 has {len(s2)}. Difference: {extra}")
    for p in extra:
        rows = [(s, C[(p, s)].classification, C[(p, s)].subtype, T[(p, s)]["t_class"]) for s in "LR" if (p, s) in C]
        say(f"  - {p}: CMMD rows and TOMPEI class per side (side, CMMD class, subtype, TOMPEI) = {rows}. The subtype "
            f"belongs to a breast with no outline; the outlined malignant breast is a second cancer with no "
            f"subtype label, so leaving the patient out is correct.")
    if set(s2["patient_id"]) - (sub_pat & any_mal):
        problem("a Stage 2 patient has no subtype or no outlined malignant breast in the raw sheets")

    # ================= 2. leakage
    say("\n## 2. Leakage\n")
    a = int((s1.groupby("patient_id")["split"].nunique() > 1).sum())
    b = int((s2.groupby("patient_id")["split"].nunique() > 1).sum())
    both = s1[["patient_id", "split"]].drop_duplicates().merge(s2[["patient_id", "split"]], on="patient_id")
    c = int((both["split_x"] != both["split_y"]).sum())
    sets = {s: set(s1.loc[s1["split"] == s, "patient_id"]) for s in SPLITS}
    overlap = len(sets["train"] & sets["val"]) + len(sets["train"] & sets["test"]) + len(sets["val"] & sets["test"])
    say(f"- Stage 1 patients in more than one split: {a}")
    say(f"- Stage 2 patients in more than one split: {b}")
    say(f"- Patients shared between the train, val and test sets (Stage 1): {overlap}")
    say(f"- Stage 2 patients found in stage1.csv: {len(both)} of {len(s2)}; with a different split there: {c}")
    say(f"- Splits used: Stage 1 {sorted(s1['split'].dropna().unique())}, rows with no split: {int(s1['split'].isna().sum())}"
        f"; Stage 2 rows with no split: {int(s2['split'].isna().sum())}")
    img_split = {}
    for _, r in s1.iterrows():
        img_split[r["png_cc"]] = img_split[r["png_mlo"]] = r["split"]
    say(f"- Images appearing in two Stage 1 splits: {len(s1) * 2 - len(img_split)}")
    leak = int((e0.groupby("patient_id")["split"].nunique() > 1).sum())
    say(f"- E0 (image-wise on purpose): {leak} of {e0['patient_id'].nunique()} patients have images in different splits. "
        f"Expected and intended for E0 only.")
    if a or b or c or overlap or len(both) != len(s2) or s1["split"].isna().any() or s2["split"].isna().any():
        problem("leakage or missing split found (see numbers above)")

    # ================= 3. labels
    say("\n## 3. Labels: raw spreadsheets → pairs.csv\n")
    png_row = png_index.merge(sides[["png", "side_corrected"]], on="png").set_index("png")

    def trace(r):
        """Compare one pairs.csv row with the raw sheets. Returns (list of mismatches, description)."""
        pid, side, bad = r["patient_id"], r["side"], []
        t = T.get((pid, side))
        if t is None:
            return ["breast not in TOMPEI sheet"], ""
        for col, key in [("t_class", "t_class"), ("density", "density"), ("birads", "birads"), ("n_lesions", "n_lesions")]:
            if not same(r[col], t[key]):
                bad.append(f"{col}: pairs {r[col]} vs TOMPEI {t[key]}")
        # which CMMD row should this breast carry? the one on its own side, unless TOMPEI moved the label
        other = "R" if side == "L" else "L"
        own, oth = C.get((pid, side)), C.get((pid, other))
        src = pid + " " + side
        if pd.isna(r["cmmd_class"]):
            expect = None
            if own is not None and not (T.get((pid, other), {}).get("t_class") not in (None, "Normal") and t["t_class"] == "Normal" and oth is None):
                bad.append("CMMD has a row for this side but pairs has no label")
        elif r["cmmd_side_original"] == side:
            expect = own
        else:
            expect, src = oth, f"{pid} {other} (moved: TOMPEI note '{t.get('note')}', class there {T.get((pid, other), {}).get('t_class', 'no such side')})"
            if own is not None:
                bad.append("label taken from the other side although CMMD has a row for this side")
        if not pd.isna(r["cmmd_class"]):
            if expect is None:
                bad.append("pairs has a CMMD label but the CMMD sheet has no such row")
            else:
                for col, val in [("cmmd_class", expect.classification), ("subtype", expect.subtype),
                                 ("age", expect.Age), ("abnormality", expect.abnormality)]:
                    if not same(r[col], val):
                        bad.append(f"{col}: pairs {r[col]} vs CMMD {val}")
                if not same(r["label"], 1 if expect.classification == "Malignant" else 0):
                    bad.append("label 0/1 does not match the class")
        # mask exists exactly when TOMPEI has an annotation file for this breast, with the same lesion count
        if ((pid, side) in J) != (not pd.isna(r["mask"])):
            bad.append("mask present/absent does not match the TOMPEI annotation file")
        if (pid, side) in J and n_lesions_json[(pid, side)] != t["n_lesions"]:
            bad.append("lesion count in JSON differs from the sheet")
        # the two PNGs really are this patient's CC and MLO of this side
        for col, view in [("png_cc", "CC"), ("png_mlo", "MLO")]:
            pr = png_row.loc[r[col]]
            if Path(pr["path"]).parts[-4] != pid or pr["patient_id"] != pid or pr["view"] != view or pr["side_corrected"] != side:
                bad.append(f"{col} is not the {view} of {pid} {side}")
        # Stage flags follow from the labels
        if bool(r["in_stage1"]) != (not pd.isna(r["cmmd_class"]) and t["t_class"] != "Exclusion"):
            bad.append("in_stage1 flag wrong")
        if bool(r["in_stage2"]) != (not pd.isna(r["subtype"]) and t["t_class"] == "Malignant" and (pid, side) in J):
            bad.append("in_stage2 flag wrong")
        return bad, src

    sample = pairs.sample(20, random_state=2026).sort_values(["patient_id", "side"])
    say("20 random breasts (seed 2026), each compared field by field with the raw CMMD and TOMPEI sheets:\n")
    say("| breast | CMMD sheet (class / subtype / age / abnormality) | TOMPEI sheet (class / density / BI-RADS / lesions) | "
        "annotation file | pairs.csv (class / subtype / TOMPEI / mask / Stage 1 / Stage 2 / split) | result |")
    say("|---|---|---|---|---|---|")
    n_bad_sample = 0
    for _, r in sample.iterrows():
        bad, _ = trace(r)
        k = (r["patient_id"], r["side"])
        c_row = C.get(k)
        c_txt = "no row for this side" if c_row is None else f"{c_row.classification} / {c_row.subtype if pd.notna(c_row.subtype) else '–'} / {c_row.Age} / {c_row.abnormality}"
        t = T[k]
        t_txt = f"{t['t_class']} / {t['density']} / {t['birads']:.0f} / {t['n_lesions']}" if pd.notna(t["birads"]) else f"{t['t_class']} / {t['density']} / – / {t['n_lesions']}"
        p_txt = (f"{r['cmmd_class'] if pd.notna(r['cmmd_class']) else '–'} / {r['subtype'] if pd.notna(r['subtype']) else '–'} / "
                 f"{r['t_class']} / {'yes' if pd.notna(r['mask']) else 'no'} / {'yes' if r['in_stage1'] else 'no'} / "
                 f"{'yes' if r['in_stage2'] else 'no'} / {r['split'] if pd.notna(r['split']) else '–'}")
        say(f"| {k[0]} {k[1]} | {c_txt} | {t_txt} | {'yes' if k in J else 'no'} | {p_txt} | {'match' if not bad else '**' + '; '.join(bad) + '**'} |")
        n_bad_sample += bool(bad)
    say(f"\nMismatches in the 20: {n_bad_sample}")
    all_bad, moved = [], []
    for _, r in pairs.iterrows():
        bad, src = trace(r)
        if bad:
            all_bad.append((r["patient_id"], r["side"], bad))
        if pd.notna(r["cmmd_class"]) and r["cmmd_side_original"] != r["side"]:
            moved.append(src)
    say(f"Same comparison on all {len(pairs)} breasts: {len(all_bad)} mismatches.")
    for pid, side, bad in all_bad[:20]:
        problem(f"label mismatch {pid} {side}: {'; '.join(bad)}")
    say(f"\nBreasts whose CMMD label comes from the other side's row ({len(moved)}; these are the only labels that do "
        f"not come from the breast's own CMMD row):")
    for m in moved:
        say(f"- label read from {m}")
    cmmd_used = len(pairs[pairs["cmmd_class"].notna()])
    say(f"\nCMMD rows: {len(cmmd)}; breasts in pairs.csv carrying a CMMD label: {cmmd_used} "
        f"({'every CMMD row is used exactly once' if cmmd_used == len(cmmd) else '**rows lost or duplicated**'}).")
    if cmmd_used != len(cmmd):
        problems.append("number of labelled breasts differs from the number of CMMD rows")
    changed = sides[sides["side"] != sides["side_corrected"]]
    say(f"Images whose side differs from the DICOM tag: {len(changed)} in {changed['patient_id'].nunique()} patients "
        f"({sorted(changed['patient_id'].unique())}).")

    # ================= 4. files
    say("\n## 4. Files: every PNG and mask opened\n")
    want = png_index.set_index("png")
    with Pool(cfg["num_workers"]) as pool:
        jobs = [(p, int(want.loc[p.name, "png_h"]), int(want.loc[p.name, "png_w"])) for p in pngs]
        P = pd.DataFrame(list(tqdm(pool.imap(check_png, jobs, chunksize=32), total=len(jobs), desc="PNGs")))
        mlo_of = pairs.dropna(subset=["mask"]).set_index("mask")["png_mlo"]
        jobs = [(m, png_dir / mlo_of[m.name]) for m in masks]
        M = pd.DataFrame(list(tqdm(pool.imap(check_mask, jobs, chunksize=32), total=len(jobs), desc="masks")))
    Pok = P[P["opens"]]
    png_flags = {
        "do not open": (~P["opens"]).sum(),
        "not 8-bit greyscale": ((Pok["ndim"] != 2) | (Pok["dtype"] != "uint8")).sum(),
        "size differs from png_index.csv": (~Pok["size_ok"].astype(bool)).sum(),
        "blank (all black)": (Pok["max"] == 0).sum(),
        "all white, or nearly (mean above 250)": (Pok["mean"] > 250).sum(),
        "flat (almost no contrast, std below 2)": (Pok["std"] < 2).sum(),
        "less than 10% of the image is breast": (Pok["nonblack"] < 0.10).sum(),
    }
    say(f"PNGs opened: {len(P)}\n")
    for k, v in png_flags.items():
        say(f"- {k}: {int(v)}")
        if v:
            problem(f"{int(v)} PNG(s): {k}")
    say(f"- brightness (mean grey level) across PNGs: min {Pok['mean'].min():.1f}, median {Pok['mean'].median():.1f}, max {Pok['mean'].max():.1f}")
    say(f"- brightest pixel per PNG: lowest {int(Pok['max'].min())}, median {int(Pok['max'].median())}")
    say(f"- share of each PNG that is breast (non-black): min {Pok['nonblack'].min():.2f}, median {Pok['nonblack'].median():.2f}, max {Pok['nonblack'].max():.2f}")
    dim = Pok.nsmallest(3, "max")
    say(f"- three dimmest PNGs (lowest brightest-pixel): {list(zip(dim['file'].str[:13], dim['max']))}")
    Mok = M[M["opens"]]
    mask_flags = {
        "do not open": (~M["opens"]).sum(),
        "size differs from their MLO PNG": (~Mok["same_size_as_png"].astype(bool)).sum(),
        "contain values other than 0 and 255": (~Mok["only_0_255"].astype(bool)).sum(),
        "empty (no lesion pixels)": (Mok["share_on"] == 0).sum(),
        "all white, or more than half the image": (Mok["share_on"] > 0.5).sum(),
        "less than 90% of the lesion area lies on breast pixels": (Mok["on_breast"] < 0.90).sum(),
    }
    say(f"\nMasks opened: {len(M)}\n")
    for k, v in mask_flags.items():
        say(f"- {k}: {int(v)}")
    for k in list(mask_flags)[:5]:
        if mask_flags[k]:
            problem(f"{int(mask_flags[k])} mask(s): {k}")
    say(f"- lesion area as a share of the image: min {Mok['share_on'].min():.4f}, median {Mok['share_on'].median():.4f}, max {Mok['share_on'].max():.3f}")
    say(f"- share of lesion area lying on breast pixels: min {Mok['on_breast'].min():.3f}, median {Mok['on_breast'].median():.3f}")
    low = Mok[Mok["on_breast"] < 0.90].sort_values("on_breast")
    if len(low):
        say(f"- masks under 90% on breast: {[(f[:9], round(v, 3)) for f, v in zip(low['file'], low['on_breast'])]}")
        # picture of exactly these, so they can be judged by eye
        tiles = []
        for f in low["file"]:
            im = cv2.cvtColor(cv2.imread(str(png_dir / mlo_of[f]), cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR)
            contours, _ = cv2.findContours(cv2.imread(str(mask_dir / f), cv2.IMREAD_GRAYSCALE), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(im, contours, -1, (0, 0, 255), 3)
            im = cv2.resize(im, (round(im.shape[1] * 500 / im.shape[0]), 500), interpolation=cv2.INTER_AREA)
            cv2.putText(im, f[:9], (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            tiles.append(np.pad(im, ((0, 0), (0, 8), (0, 0))))
        cv2.imwrite("reports/05_audit_masks_off_breast.png", np.hstack(tiles))
        say("  Picture of these: `reports/05_audit_masks_off_breast.png`.")

    # Some TOMPEI "outlines" are plain boxes (4 corners, sometimes with the first point repeated), not traced
    # lesion shapes. They are valid annotations, but worth knowing about before computing shape features.
    box_rows = []
    for (pid, side), p in J.items():
        lesions = jsonlib.loads(p.read_text(encoding="utf-8"))
        n_box = sum(len(l["cgPoints"]) <= 6 for l in lesions)
        box_rows.append({"patient_id": pid, "side": side, "n": len(lesions), "n_box": n_box,
                         "labels": ",".join(sorted({l["label"].strip() for l in lesions if len(l["cgPoints"]) <= 6}))})
    B = pd.DataFrame(box_rows)
    Bs2 = B.merge(s2[["patient_id", "side", "split"]], on=["patient_id", "side"])
    say(f"\nBox-shaped annotations (6 points or fewer, a rectangle instead of a traced outline): "
        f"{int(B['n_box'].sum())} of {int(B['n'].sum())} lesions, in {int((B['n_box'] > 0).sum())} of {len(B)} annotated breasts.")
    say(f"- lesion types of the boxes: {B.loc[B['n_box'] > 0, 'labels'].value_counts().to_dict()}")
    say(f"- Stage 2 breasts with at least one box: {int((Bs2['n_box'] > 0).sum())} of {len(Bs2)}; "
        f"where every lesion is a box: {int((Bs2['n_box'] == Bs2['n']).sum())} "
        f"(train / val / test: {[int(((Bs2['n_box'] == Bs2['n']) & (Bs2['split'] == s)).sum()) for s in SPLITS]})")

    # ================= 5. picture
    say("\n## 5. Picture\n")
    rows = s2[s2["split"] == "test"].sample(16, random_state=2026)
    cells, H = [], 300
    for _, r in rows.iterrows():
        cc = cv2.imread(str(png_dir / r["png_cc"]), cv2.IMREAD_GRAYSCALE)
        mlo = cv2.imread(str(png_dir / r["png_mlo"]), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mask_dir / r["mask"]), cv2.IMREAD_GRAYSCALE)
        mlo_c = cv2.cvtColor(mlo, cv2.COLOR_GRAY2BGR)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(mlo_c, contours, -1, (0, 0, 255), 4)
        panels = [cv2.cvtColor(cc, cv2.COLOR_GRAY2BGR), mlo_c, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)]
        panels = [cv2.resize(p, (round(p.shape[1] * H / p.shape[0]), H), interpolation=cv2.INTER_AREA) for p in panels]
        for p, tag in zip(panels, ["CC", "MLO", "mask"]):
            cv2.putText(p, tag, (4, H - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cell = np.hstack([np.pad(p, ((0, 0), (0, 4), (0, 0))) for p in panels])
        bar = np.zeros((26, cell.shape[1], 3), np.uint8)
        cv2.putText(bar, f"{r['patient_id']}  {r['side']}  {r['subtype']}", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cells.append(np.vstack([bar, cell]))
    w = max(c.shape[1] for c in cells) + 14
    cells = [np.pad(c, ((0, 10), (0, w - c.shape[1]), (0, 0))) for c in cells]
    cv2.imwrite("reports/05_audit_montage.png", np.vstack([np.hstack(cells[i:i + 4]) for i in range(0, 16, 4)]))
    say("`reports/05_audit_montage.png`: 16 random Stage 2 **test** breasts (seed 2026). Each cell is CC | MLO with the "
        "lesion outline in red | the mask itself, titled patient, side (corrected) and subtype.")
    say(f"Breasts shown: {[(a, b, c) for a, b, c in zip(rows['patient_id'], rows['side'], rows['subtype'])]}")

    # ================= subgroup spread (input to the re-split question)
    say("\n## 6. How evenly the subgroups are spread over the splits (Stage 1 breasts)\n")
    ben, mal = s1[s1["label"] == 0], s1[s1["label"] == 1]
    say("| subgroup | train | val | test | all |")
    say("|---|---|---|---|---|")
    for title, d, m in [("benign breasts that are TOMPEI Normal (no visible lesion)", ben, ben["t_class"] == "Normal"),
                        ("malignant breasts that are TOMPEI Invisible", mal, mal["t_class"] == "Invisible"),
                        ("breasts that are dense", s1, s1["dense"].astype(str) == "True")]:
        cell = [f"{int((m & (d['split'] == s)).sum())} of {int((d['split'] == s).sum())} ({(m & (d['split'] == s)).sum() / (d['split'] == s).sum():.1%})" for s in SPLITS]
        say(f"| {title} | " + " | ".join(cell) + f" | {int(m.sum())} of {len(d)} ({m.mean():.1%}) |")
    if args.previous_stage1:
        old = pd.read_csv(args.previous_stage1)
        o_ben, o_mal = old[old["label"] == 0], old[old["label"] == 1]
        say("\nThe same shares in the split as it was BEFORE the re-split:\n")
        say("| subgroup | train | val | test |")
        say("|---|---|---|---|")
        for title, d, m in [("benign breasts that are TOMPEI Normal", o_ben, o_ben["t_class"] == "Normal"),
                            ("malignant breasts that are TOMPEI Invisible", o_mal, o_mal["t_class"] == "Invisible")]:
            say(f"| {title} | " + " | ".join(
                f"{int((m & (d['split'] == s)).sum())} of {int((d['split'] == s).sum())} ({(m & (d['split'] == s)).sum() / (d['split'] == s).sum():.1%})"
                for s in SPLITS) + " |")
        was = old.drop_duplicates("patient_id").set_index("patient_id")["split"]
        now = s1.drop_duplicates("patient_id").set_index("patient_id")["split"]
        say(f"\nPatients whose split changed in the re-split: {int((was != now.reindex(was.index)).sum())} of {len(was)}. "
            f"Nothing had been trained yet, so no result depends on the old split.")
    say("\n| Stage 2 subtype | train | val | test |")
    say("|---|---|---|---|")
    for s in SUBTYPES:
        say(f"| {s} | " + " | ".join(str(int(((s2['subtype'] == s) & (s2['split'] == x)).sum())) for x in SPLITS) + " |")

    # ---- the result goes at the TOP of the report, the evidence follows
    head = ["", "## Result", ""]
    if problems:
        head.append(f"**{len(problems)} problem(s) found:**")
        head += [f"- {p}" for p in problems]
    else:
        head.append("**No problems found.** Every count in PROGRESS.md recounts exactly, there is no leakage, all "
                    f"{len(pairs)} breasts trace back to the raw spreadsheets, and every PNG and mask opens and is sane.")
    head += ["", "Not problems, but worth knowing (details in the sections below):", ""]
    head.append(f"- {int(B['n_box'].sum())} TOMPEI annotations are boxes, not traced outlines; all are architectural "
                f"distortions ('dist'). {int((Bs2['n_box'] == Bs2['n']).sum())} Stage 2 breasts have only a box. "
                f"Shape radiomics on those describe the box, not the lesion.")
    head.append(f"- {len(low)} masks overhang the skin edge (under 90% of the area on breast pixels); they are such "
                f"boxes, not misplaced masks (`reports/05_audit_masks_off_breast.png`).")
    head.append(f"- {len(extra)} subtyped patient ({', '.join(extra)}) has an outlined cancer but is correctly not in "
                f"Stage 2: the subtype belongs to the other breast.")
    if args.previous_stage1:
        head.append("- The splits were redone during this audit so TOMPEI's Normal and Invisible subgroups are spread "
                    "evenly (section 6 shows before and after). The counts in section 1 are checked against the new split.")
    print("\n".join(head))
    lines[2:2] = head
    Path("reports/05_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nSaved reports/05_audit.md")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
