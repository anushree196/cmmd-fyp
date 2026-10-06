"""Task 02: convert every DICOM once into a breast-cropped 8-bit PNG, and record how each was transformed.

Usage:
    python scripts/02_convert.py --config config.yaml --limit 20   # test + QC montage
    python scripts/02_convert.py --config config.yaml              # full run (resumable)
    python scripts/02_convert.py --config config.yaml --montage-only 48

Every output row stores the crop box, flip and scale, so masks drawn on the ORIGINAL DICOM pixels
(TOMPEI-CMMD, task 03) can be mapped onto the PNG with transform_points() below.
"""
import argparse, random, sys, time
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pydicom
from pydicom.pixels import apply_voi_lut
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config


def dicom_to_uint8(ds):
    """Pixels -> 0..255, with the file's own VOI LUT / window applied and MONOCHROME1 inverted."""
    img = ds.pixel_array
    if "VOILUTSequence" in ds or "WindowCenter" in ds:
        img = apply_voi_lut(img, ds)
    img = img.astype(np.float32)
    lo, hi = np.percentile(img, 0.5), np.percentile(img, 99.5)
    img = np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1)
    if str(ds.get("PhotometricInterpretation", "")) == "MONOCHROME1":
        img = 1.0 - img
    return (img * 255).astype(np.uint8)


def breast_box(img, margin=10):
    """Bounding box (x0, y0, x1, y1) of the largest bright region = the breast."""
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return 0, 0, img.shape[1], img.shape[0]
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = stats[i, :4]
    return (max(x - margin, 0), max(y - margin, 0),
            min(x + w + margin, img.shape[1]), min(y + h + margin, img.shape[0]))


def transform_points(xs, ys, row):
    """Map (x, y) in original DICOM pixels to PNG pixels, using one png_index.csv row."""
    xs = np.asarray(xs, float) - row["crop_x0"]
    ys = np.asarray(ys, float) - row["crop_y0"]
    if row["flipped"]:
        xs = (row["crop_x1"] - row["crop_x0"]) - 1 - xs
    return xs * row["scale"], ys * row["scale"]


def convert_one(rec, out_dir, height, flip_to_left):
    name = f"{rec['patient_id']}_{rec['side'] or 'U'}_{rec['view'] or 'U'}_{str(rec['sop_uid'])[-8:]}.png"
    out = out_dir / name
    info = {"path": rec["path"], "png": name}
    try:
        ds = pydicom.dcmread(rec["path"])
        img = dicom_to_uint8(ds)
        x0, y0, x1, y1 = breast_box(img)
        crop = img[y0:y1, x0:x1]
        # decide orientation from the image itself: the breast's bright mass should sit on the left
        left_heavier = crop[:, : crop.shape[1] // 2].mean() >= crop[:, crop.shape[1] // 2:].mean()
        flipped = bool(flip_to_left and not left_heavier)
        if flipped:
            crop = crop[:, ::-1]
        scale = height / crop.shape[0]
        width = max(1, round(crop.shape[1] * scale))
        if not out.exists():  # resumable
            small = cv2.resize(np.ascontiguousarray(crop), (width, height), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(out), small)
        info.update(orig_h=img.shape[0], orig_w=img.shape[1], crop_x0=x0, crop_y0=y0, crop_x1=x1,
                    crop_y1=y1, flipped=flipped, scale=scale, png_h=height, png_w=width, error=None)
    except Exception as e:
        info["error"] = repr(e)
    return info


def montage(png_dir, names, out_path, n=24, cols=8, tile=200):
    names = random.Random(0).sample(list(names), min(n, len(names)))
    rows = (len(names) + cols - 1) // cols
    canvas = np.zeros((rows * tile, cols * tile), np.uint8)
    for k, nm in enumerate(names):
        im = cv2.imread(str(png_dir / nm), cv2.IMREAD_GRAYSCALE)
        if im is None:
            continue
        s = tile / max(im.shape)
        im = cv2.resize(im, (int(im.shape[1] * s), int(im.shape[0] * s)))
        r, c = divmod(k, cols)
        canvas[r * tile: r * tile + im.shape[0], c * tile: c * tile + im.shape[1]] = im
        cv2.putText(canvas, nm[:16], (c * tile + 3, r * tile + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, 255, 1)
    cv2.imwrite(str(out_path), canvas)
    print(f"QC montage -> {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--montage-only", type=int, default=0)
    args = ap.parse_args()
    cfg = load_config(args.config)
    png_dir, idx_dir = cfg["png_dir"], cfg["index_dir"]
    out_csv = idx_dir / "png_index.csv"

    if args.montage_only:
        montage(png_dir, pd.read_csv(out_csv)["png"], Path("reports/02_qc_montage.png"), n=args.montage_only)
        return

    index = pd.read_csv(idx_dir / "dicom_index.csv", dtype=str)
    recs = index.to_dict("records")
    if args.limit:
        recs = random.Random(cfg["seed"]).sample(recs, min(args.limit, len(recs)))
    print(f"Converting {len(recs)} images -> {png_dir} (height {cfg['png_height']}) ...")
    t = time.time()
    work = partial(convert_one, out_dir=png_dir, height=cfg["png_height"], flip_to_left=cfg["flip_to_left"])
    with Pool(cfg["num_workers"]) as pool:
        rows = list(tqdm(pool.imap_unordered(work, recs, chunksize=4), total=len(recs)))
    res = pd.DataFrame(rows)
    ok, bad = res[res["error"].isna()], res[res["error"].notna()]
    ok = index.merge(ok.drop(columns="error"), on="path")
    if not args.limit:
        ok.to_csv(out_csv, index=False)
    else:
        ok.to_csv(idx_dir / "png_index_test.csv", index=False)
    if len(bad):
        bad.to_csv(idx_dir / "convert_errors.csv", index=False)

    size_gb = sum(p.stat().st_size for p in png_dir.glob("*.png")) / 1e9
    print(f"Done in {(time.time() - t) / 60:.1f} min: {len(ok)} ok, {len(bad)} failed, "
          f"png folder now {size_gb:.2f} GB")
    print("flipped:", ok["flipped"].value_counts().to_dict(),
          "| png width range:", ok["png_w"].min(), "-", ok["png_w"].max())
    montage(png_dir, ok["png"], Path("reports/02_qc_montage.png"), n=min(24, len(ok)))


if __name__ == "__main__":
    main()
