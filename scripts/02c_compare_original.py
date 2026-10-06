"""Task 02 (part c): show chosen images uncropped next to their PNG, to check the crop and the flip by eye.

For each image the picture has three panels:
  1. the original DICOM, untouched, with the crop box drawn on it
  2. the same original brightened 8x, so very faint tissue or skin near the edge becomes visible
  3. the PNG that was saved (cropped, maybe mirrored)
It also prints a few numbers per image (crop box, what lies outside it, very bright patches).

Usage:
    python scripts/02c_compare_original.py --config config.yaml --images D1-1343_L_MLO D2-0347_R_MLO
"""
import argparse, importlib, sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pydicom

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.config import load_config

convert = importlib.import_module("02_convert")  # reuse the exact pixel code of the conversion

PANEL_H = 700  # height of every panel in the picture


def panel(img, title):
    """Resize to PANEL_H tall and write a title in the top-left corner."""
    img = cv2.resize(img, (round(img.shape[1] * PANEL_H / img.shape[0]), PANEL_H), interpolation=cv2.INTER_AREA)
    cv2.putText(img, title, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 255, 2)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--images", nargs="+", required=True, help="like D1-1343_L_MLO (patient_side_view)")
    ap.add_argument("--out", default="reports/02_qc_original_vs_png.png")
    args = ap.parse_args()
    cfg = load_config(args.config)
    idx = pd.read_csv(cfg["index_dir"] / "png_index.csv")
    idx["key"] = idx["patient_id"] + "_" + idx["side"] + "_" + idx["view"]

    rows_of_panels = []
    for key in args.images:
        r = idx[idx["key"] == key].iloc[0]
        orig = convert.dicom_to_uint8(pydicom.dcmread(r["path"]))
        png = cv2.imread(str(cfg["png_dir"] / r["png"]), cv2.IMREAD_GRAYSCALE)
        H, W = orig.shape
        x0, y0, x1, y1 = int(r["crop_x0"]), int(r["crop_y0"]), int(r["crop_x1"]), int(r["crop_y1"])

        # ---- numbers
        outside = np.ones_like(orig, bool)
        outside[y0:y1, x0:x1] = False  # True for pixels the crop threw away
        cols_with_tissue = np.where((orig > 0).any(axis=0))[0]
        print(f"\n{key}  (bits_stored {r['bits_stored']}, side tag {r['side']}, flipped {r['flipped']})")
        print(f"  original {W} wide x {H} tall | crop box x {x0}-{x1}, y {y0}-{y1}")
        print(f"  columns that contain any non-black pixel: {cols_with_tissue.min()} to {cols_with_tissue.max()}")
        print(f"  pixels thrown away by the crop: {outside.sum()} | of these non-black: {(orig[outside] > 0).sum()}"
              f" | brighter than 10: {(orig[outside] > 10).sum()} | brightest: {orig[outside].max()}")
        for name, strip in [("left", orig[:, :5]), ("right", orig[:, -5:]), ("top", orig[:5]), ("bottom", orig[-5:])]:
            print(f"  outermost 5 px on the {name}: {(strip > 10).mean():.0%} is tissue (brighter than 10)")
        left, right = (orig[:, : W // 2] > 10).sum(), (orig[:, W // 2:] > 10).sum()
        print(f"  tissue pixels in left half {left}, right half {right} -> breast is on the "
              f"{'left' if left >= right else 'right'} of the original")
        # very bright patches (markers, labels, skin folds): position in ORIGINAL pixel coordinates
        n, _, stats, _ = cv2.connectedComponentsWithStats((orig >= 250).astype(np.uint8), connectivity=8)
        big = sorted([s for s in stats[1:] if s[cv2.CC_STAT_AREA] >= 500], key=lambda s: -s[cv2.CC_STAT_AREA])[:3]
        print(f"  share of pixels at 250-255: {(orig >= 250).mean():.2%} | saturated patches of 500+ px: {len(big)}")
        for s in big:
            print(f"    patch x {s[0]}-{s[0] + s[2]}, y {s[1]}-{s[1] + s[3]}, area {s[4]} px")

        # ---- picture
        boxed = orig.copy()
        cv2.rectangle(boxed, (x0, y0), (x1 - 1, y1 - 1), 255, 6)
        bright = np.clip(orig.astype(np.int32) * 8, 0, 255).astype(np.uint8)
        cv2.rectangle(bright, (x0, y0), (x1 - 1, y1 - 1), 255, 6)
        gap = np.zeros((PANEL_H, 12), np.uint8)
        rows_of_panels.append(np.hstack([panel(boxed, f"{key} original + crop box"), gap,
                                         panel(bright, "original x8 brighter"), gap,
                                         panel(png, "saved PNG")]))

    width = max(p.shape[1] for p in rows_of_panels)
    rows_of_panels = [np.pad(p, ((0, 12), (0, width - p.shape[1]))) for p in rows_of_panels]
    cv2.imwrite(args.out, np.vstack(rows_of_panels))
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
