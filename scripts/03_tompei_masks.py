"""Task 03 (part 2): draw TOMPEI's lesion outlines as masks aligned to our PNGs, and build the Stage 2 set.

Run 03_tompei_labels.py first (it writes image_sides.csv and breast_labels.csv).

Each TOMPEI file `{patient}_MLO_{side}_AnnotationFile.json` is a list of lesions; each lesion has a `label`
(mass, calc, dist, FA, FAD, lipoma) and `cgPoints`, a list of {x, y} points in ORIGINAL DICOM pixels.
For each file we fill the outlines on a blank image the size of the DICOM, then apply exactly the crop, flip
and resize that 02_convert.py applied to that image, so the mask lines up with the PNG.

Writes:
    data/masks1024/{png name}_mask.png   0 = background, 255 = lesion
    data/index/mask_index.csv            one row per mask
    data/index/stage2_patients.csv       patients usable for Stage 2 (subtype label AND a lesion mask)
    reports/03_mask_overlay.png          16 random PNGs with the mask outline drawn in red
    reports/03_mask_overlay_swapped.png  the patients whose MLO side tags were swapped (checks the link)
    reports/03_stage2_counts.md          the counts

Usage:
    python scripts/03_tompei_masks.py --config config.yaml --limit 20
    python scripts/03_tompei_masks.py --config config.yaml
"""
import argparse, json, random, re, sys
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config

NAME = re.compile(r"^(D[12]-\d{4})_MLO_([LR])_AnnotationFile\.json$")
SUBTYPES = ["Luminal A", "Luminal B", "HER2-enriched", "triple negative"]
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def find_annotation_files(tompei_dir):
    """Real annotation files only (the download also contains macOS junk copies in __MACOSX)."""
    out = []
    for p in sorted(Path(tompei_dir).rglob("*_AnnotationFile.json")):
        m = NAME.match(p.name)
        if m and "__MACOSX" not in p.parts:
            out.append({"json": str(p), "patient_id": m.group(1), "side": m.group(2)})
    return pd.DataFrame(out)


def make_mask(rec, mask_dir):
    """Draw one breast's lesions and transform the mask the same way its PNG was transformed."""
    out = mask_dir / (Path(rec["png"]).stem + "_mask.png")
    info = {"png": rec["png"], "mask": out.name}
    try:
        lesions = json.loads(Path(rec["json"]).read_text(encoding="utf-8"))
        full = np.zeros((int(rec["orig_h"]), int(rec["orig_w"])), np.uint8)  # same size as the DICOM
        for lesion in lesions:
            pts = np.array([[p["x"], p["y"]] for p in lesion["cgPoints"]], np.float32)
            cv2.fillPoly(full, [np.round(pts).astype(np.int32)], 255)
        x0, y0, x1, y1 = (int(rec[k]) for k in ("crop_x0", "crop_y0", "crop_x1", "crop_y1"))
        crop = full[y0:y1, x0:x1]                    # same crop box as the PNG
        if rec["flipped"]:
            crop = crop[:, ::-1]                     # same mirror as the PNG
        small = cv2.resize(np.ascontiguousarray(crop), (int(rec["png_w"]), int(rec["png_h"])),
                           interpolation=cv2.INTER_NEAREST)  # nearest keeps the mask strictly 0 / 255
        if not out.exists():  # resumable
            cv2.imwrite(str(out), small)
        ys, xs = np.where(small > 0)
        info.update(
            n_lesions=len(lesions),
            lesion_labels=",".join(sorted({l["label"].strip() for l in lesions})),
            n_polyline=sum(l.get("type") == "Polyline" for l in lesions),
            # a "box" = 6 points or fewer: the annotator drew a rectangle, not the lesion's real outline
            n_box=sum(len(l["cgPoints"]) <= 6 for l in lesions),
            area_full_px=int((full > 0).sum()),
            # share of the outlined area that falls outside the PNG's crop box (0 = nothing lost)
            cut_off_share=round(1 - (crop > 0).sum() / max((full > 0).sum(), 1), 4),
            area_png_px=int((small > 0).sum()),
            box_x0=int(xs.min()) if len(xs) else -1, box_y0=int(ys.min()) if len(ys) else -1,
            box_x1=int(xs.max()) + 1 if len(xs) else -1, box_y1=int(ys.max()) + 1 if len(ys) else -1,
            error=None)
    except Exception as e:
        info["error"] = repr(e)
    return info


def overlay(png_dir, mask_dir, rows, out_path, cols=8, tile_h=420):
    """Grid of PNGs with the mask outline in red, so the alignment can be checked by eye."""
    tiles = []
    for _, r in rows.iterrows():
        im = cv2.imread(str(png_dir / r["png"]), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mask_dir / r["mask"]), cv2.IMREAD_GRAYSCALE)
        colour = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(colour, contours, -1, (0, 0, 255), 3)  # red in OpenCV's blue-green-red order
        colour = cv2.resize(colour, (round(colour.shape[1] * tile_h / colour.shape[0]), tile_h),
                            interpolation=cv2.INTER_AREA)
        cv2.putText(colour, f"{r['patient_id']} {r['side']} {r['lesion_labels']}"[:30], (4, 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        tiles.append(colour)
    tile_w = max(t.shape[1] for t in tiles)
    tiles = [np.pad(t, ((0, 6), (0, tile_w - t.shape[1] + 6), (0, 0))) for t in tiles]
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    grid = np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])
    cv2.imwrite(str(out_path), grid)
    print(f"overlay -> {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cfg = load_config(args.config)
    idx_dir, png_dir = cfg["index_dir"], cfg["png_dir"]
    mask_dir = cfg["work_root"] / f"masks{cfg.get('png_height', 1024)}"
    mask_dir.mkdir(parents=True, exist_ok=True)

    png = pd.read_csv(idx_dir / "png_index.csv")
    sides = pd.read_csv(idx_dir / "image_sides.csv")[["png", "side_corrected"]]
    png = png.merge(sides, on="png")
    breasts = pd.read_csv(idx_dir / "breast_labels.csv")

    # ---- link: annotation file -> our MLO image of that patient with the same CORRECTED side
    ann = find_annotation_files(cfg["tompei_dir"])
    mlo = png[png["view"] == "MLO"].drop(columns="side").rename(columns={"side_corrected": "side"})
    linked = ann.merge(mlo, on=["patient_id", "side"], how="left")
    print(f"annotation files: {len(ann)} | linked to one of our MLO images: {linked['png'].notna().sum()}"
          f" | patients: {ann['patient_id'].nunique()}")
    recs = linked[linked["png"].notna()].to_dict("records")
    if args.limit:
        recs = random.Random(cfg["seed"]).sample(recs, min(args.limit, len(recs)))

    with Pool(cfg["num_workers"]) as pool:
        rows = list(tqdm(pool.imap_unordered(partial(make_mask, mask_dir=mask_dir), recs, chunksize=8),
                         total=len(recs)))
    res = pd.DataFrame(rows)
    bad = res[res["error"].notna()]
    ok = res[res["error"].isna()].drop(columns="error")
    ok = linked[["patient_id", "side", "png"]].merge(ok, on="png")
    if len(bad):
        bad.to_csv(idx_dir / "mask_errors.csv", index=False)
    print(f"masks made: {len(ok)} | failed: {len(bad)}")
    if args.limit:
        overlay(png_dir, mask_dir, ok.head(16), Path("reports/03_mask_overlay.png"))
        return
    ok.to_csv(idx_dir / "mask_index.csv", index=False)

    # ---- checks on the masks
    say("# Task 03 — lesion masks and the Stage 2 set")
    say(f"\nAnnotation files: {len(ann)} (all MLO)  |  patients: {ann['patient_id'].nunique()}"
        f"  |  masks made: {len(ok)}  |  failed: {len(bad)}")
    say(f"Lesions outlined: {ok['n_lesions'].sum()}  |  lesions per breast: "
        f"{ok['n_lesions'].value_counts().sort_index().to_dict()}")
    say(f"Lesion types present per breast: {ok['lesion_labels'].value_counts().to_dict()}")
    say(f"Outlines of type 'Polyline' (treated as closed shapes like the rest): {ok['n_polyline'].sum()}")
    say(f"Empty masks (outline entirely outside the PNG): {(ok['area_png_px'] == 0).sum()}")
    cut = ok["cut_off_share"]
    say(f"Outlined area cut off by the PNG crop box: none on {(cut == 0).sum()} masks, "
        f"up to 1% on {((cut > 0) & (cut <= 0.01)).sum()}, 1-10% on {((cut > 0.01) & (cut <= 0.10)).sum()}, "
        f"over 10% on {(cut > 0.10).sum()} (max {cut.max():.3f})")
    worst = ok.nlargest(5, "cut_off_share")
    say(f"   most cut off: {list(zip(worst['patient_id'] + ' ' + worst['side'], worst['cut_off_share']))}")
    share = ok["area_png_px"] / (ok["png"].map(png.set_index("png")["png_w"]) * cfg["png_height"])
    say(f"Mask area as a share of the PNG: min {share.min():.4f}, median {share.median():.4f}, max {share.max():.3f}")

    # ---- the Stage 2 set: subtype label AND a lesion mask on that same breast
    b = breasts.merge(ok[["patient_id", "side", "png", "mask", "lesion_labels"]]
                      .rename(columns={"png": "png_mlo"}), on=["patient_id", "side"], how="left")
    cc = png[png["view"] == "CC"][["patient_id", "side_corrected", "png"]].rename(
        columns={"side_corrected": "side", "png": "png_cc"})
    b = b.merge(cc, on=["patient_id", "side"], how="left")
    b["has_mask"] = b["mask"].notna()
    sub = b[b["subtype"].notna()]
    say("\n## Stage 2 set\n")
    say(f"Patients with a subtype label: {sub['patient_id'].nunique()} ({len(sub)} breasts, one per patient)")
    say(f"Patients with at least one TOMPEI mask (any class): {b.loc[b['has_mask'], 'patient_id'].nunique()}")
    say("\nSubtyped breasts by TOMPEI class and whether a mask exists:\n")
    say(pd.crosstab(sub["t_class"], sub["has_mask"].map({True: "mask", False: "no mask"}), margins=True).to_markdown())
    stage2 = sub[sub["has_mask"] & (sub["t_class"] == "Malignant")]
    excl = sub[sub["has_mask"] & (sub["t_class"] == "Exclusion")]
    say(f"\n**Stage 2 set = subtype label AND mask AND TOMPEI class Malignant: {len(stage2)} patients**")
    say(f"Subtyped breasts with a mask that TOMPEI recommends excluding (left out): {len(excl)} "
        f"{list(zip(excl['patient_id'], excl['exclusion_reason']))}")
    say(f"Stage 2 breasts with no CC image: {stage2['png_cc'].isna().sum()}")
    say("\n| subtype | patients with subtype | in Stage 2 set | lost |")
    say("|---|---|---|---|")
    for s in SUBTYPES:
        n_all, n_s2 = (sub["subtype"] == s).sum(), (stage2["subtype"] == s).sum()
        say(f"| {s} | {n_all} | {n_s2} | {n_all - n_s2} |")
    say(f"| **total** | {len(sub)} | {len(stage2)} | {len(sub) - len(stage2)} |")
    lost = sub[~sub.index.isin(stage2.index)]
    say(f"\nWhy the {len(lost)} subtyped patients are lost: {lost['t_class'].value_counts().to_dict()}")
    say(f"Stage 2 lesion types: {stage2['lesion_labels'].value_counts().to_dict()}")
    say(f"Stage 2 abnormality (CMMD): {stage2['abnormality'].value_counts().to_dict()}")
    say(f"Stage 2 age: {stage2['age'].min():.0f} to {stage2['age'].max():.0f}, mean {stage2['age'].mean():.1f}")
    moved = stage2[stage2["side"] != stage2["cmmd_side_original"]]
    say(f"Stage 2 patients whose subtype was moved to the other breast by TOMPEI's correction: {len(moved)} "
        f"{moved['patient_id'].tolist()}")

    cols = ["patient_id", "side", "subtype", "age", "abnormality", "density", "birads", "n_lesions",
            "lesion_labels", "png_cc", "png_mlo", "mask", "cmmd_side_original"]
    stage2[cols].to_csv(idx_dir / "stage2_patients.csv", index=False)
    Path("reports/03_stage2_counts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved {idx_dir / 'stage2_patients.csv'} ({len(stage2)} rows), reports/03_stage2_counts.md")

    # ---- pictures
    overlay(png_dir, mask_dir, ok.sample(16, random_state=cfg["seed"]), Path("reports/03_mask_overlay.png"))
    swapped = pd.read_csv(idx_dir / "image_sides.csv")
    swapped = swapped[(swapped["view"] == "MLO") & (swapped["side"] != swapped["side_corrected"])]
    rows_sw = ok[ok["png"].isin(swapped["png"])]
    if len(rows_sw):
        overlay(png_dir, mask_dir, rows_sw, Path("reports/03_mask_overlay_swapped.png"), cols=len(rows_sw))


if __name__ == "__main__":
    main()
