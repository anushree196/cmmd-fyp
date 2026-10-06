"""Task 02 (part b): sanity checks on the converted PNGs. Reads png_index.csv and a sample of PNGs.

Prints a short summary and saves reports/02_qc_16bit.png (the two 16-bit images next to six normal ones).

Usage:
    python scripts/02b_convert_checks.py --config config.yaml
"""
import argparse, sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config


def breast_brightness(png_path):
    """Mean grey level of the non-black pixels (roughly: how bright the breast tissue is)."""
    im = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
    return float(im[im > 0].mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    cfg = load_config(ap.parse_args().config)
    png_dir = cfg["png_dir"]
    df = pd.read_csv(cfg["index_dir"] / "png_index.csv")

    # ---- 1. is there one PNG per row?
    on_disk = {p.name for p in png_dir.glob("*.png")}
    print(f"rows in png_index.csv: {len(df)}  |  PNG files on disk: {len(on_disk)}"
          f"  |  rows whose PNG is missing: {(~df['png'].isin(on_disk)).sum()}"
          f"  |  duplicate PNG names: {df['png'].duplicated().sum()}")
    print(f"PNGs on disk that are not in the index (left over from test runs): {len(on_disk - set(df['png']))}")

    # ---- 2. the flip is decided from the pixels; it should agree with the side tag (R flipped, L not)
    print("\nflipped vs side tag:")
    print(pd.crosstab(df["side"], df["flipped"]).to_string())
    # the few that disagree are images whose side tag does not match where the breast actually is
    odd_side = df[(df["side"] == "R") != df["flipped"]]
    odd_side[["patient_id", "side", "view", "flipped", "png"]].to_csv(
        cfg["index_dir"] / "side_tag_vs_pixels.csv", index=False)
    print(f"side tag disagrees with the pixels on {len(odd_side)} images "
          f"({odd_side['patient_id'].nunique()} patients) -> data/index/side_tag_vs_pixels.csv")
    print("  ", (odd_side["patient_id"] + "_" + odd_side["side"] + "_" + odd_side["view"]).tolist())

    # ---- 3. crop boxes: how much of the original image was kept
    crop_w = (df["crop_x1"] - df["crop_x0"]) / df["orig_w"]
    crop_h = (df["crop_y1"] - df["crop_y0"]) / df["orig_h"]
    print(f"\ncrop width  as share of original: min {crop_w.min():.2f}, median {crop_w.median():.2f}, max {crop_w.max():.2f}")
    print(f"crop height as share of original: min {crop_h.min():.2f}, median {crop_h.median():.2f}, max {crop_h.max():.2f}")
    print(f"crops keeping the whole image (no background found): {((crop_w > 0.999) & (crop_h > 0.999)).sum()}")
    tiny = df[(crop_w < 0.15) | (crop_h < 0.30)]
    print(f"suspiciously small crops (width < 15% or height < 30%): {len(tiny)}")
    if len(tiny):
        print("  ", tiny["png"].head(10).tolist())
    # how much non-black content (tissue, but also labels and markers) each crop left out
    lost = df["outside_share"]
    print(f"non-black pixels left outside the crop: median {lost.median():.4f}, 99th pct {lost.quantile(0.99):.3f}, "
          f"max {lost.max():.3f} | images losing > 1%: {(lost > 0.01).sum()} | > 5%: {(lost > 0.05).sum()}")
    worst = df.nlargest(6, "outside_share")
    print("   most left out:", (worst["patient_id"] + "_" + worst["side"] + "_" + worst["view"]).tolist(),
          worst["outside_share"].tolist())
    widest = df.assign(w=crop_w).nlargest(3, "w")
    print("   widest crops:", (widest["patient_id"] + "_" + widest["side"] + "_" + widest["view"]).tolist(),
          widest["w"].round(2).tolist())
    print(f"PNG size: height {df['png_h'].min()}-{df['png_h'].max()}, width {df['png_w'].min()}-{df['png_w'].max()}"
          f" (median {df['png_w'].median():.0f})")

    # ---- 4. the two 16-bit files: are they on the same brightness scale as the rest?
    odd = df[df["bits_stored"] != 8]
    normal = df[df["bits_stored"] == 8].sample(300, random_state=cfg["seed"])
    normal_b = np.array([breast_brightness(png_dir / n) for n in normal["png"]])
    print(f"\nbreast brightness of 300 random 8-bit images: 5th pct {np.percentile(normal_b, 5):.0f}, "
          f"median {np.median(normal_b):.0f}, 95th pct {np.percentile(normal_b, 95):.0f}")
    for n in odd["png"]:
        print(f"breast brightness of 16-bit image {n}: {breast_brightness(png_dir / n):.0f}")

    # ---- 5. picture: the 16-bit images (first two tiles) next to six normal ones
    names = odd["png"].tolist() + normal["png"].head(6).tolist()
    tiles = []
    for n in names:
        im = cv2.imread(str(png_dir / n), cv2.IMREAD_GRAYSCALE)
        im = cv2.resize(im, (round(im.shape[1] * 400 / im.shape[0]), 400))
        cv2.putText(im, n[:14], (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 255, 1)
        tiles.append(im)
    out = Path("reports") / "02_qc_16bit.png"
    cv2.imwrite(str(out), np.hstack(tiles))
    print(f"\nSaved {out} (first {len(odd)} tiles are the 16-bit files)")


if __name__ == "__main__":
    main()
