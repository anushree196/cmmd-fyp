# Task 02 — Convert DICOM → PNG once  (runs on: laptop, ~20–60 min, CPU)

Goal: `data/png1024/*.png` (8-bit, breast-cropped, same orientation) + `data/index/png_index.csv`.
This is the only time the 21 GB of DICOMs are read. Output is ~2–3 GB.

## What the script does per image (`scripts/02_convert.py`)
1. Read pixels with pydicom. Apply the VOI LUT / window if the file has one. Invert if `MONOCHROME1`.
2. Scale to 0–255 (uint8).
3. Find the breast: Otsu threshold → largest connected component → bounding box (+ small margin).
   This removes the black background and labels/markers, which also shrinks the file.
4. Mirror right-breast images (`flip_to_left: true`) so all breasts face the same way.
5. Resize to `png_height` px tall, keeping aspect ratio. Save PNG named `{patient}_{L|R}_{CC|MLO}_{sop8}.png`.
6. Record for every image: original size, crop box (x0, y0, x1, y1), flip flag, scale factor, output size.
   **Task 03 needs these to map TOMPEI polygons onto the PNGs. Do not drop them.**

## Steps
1. `python scripts/02_convert.py --config config.yaml --limit 20`, then look at
   `reports/02_qc_montage.png` (a grid of random outputs). **[ANU]** Look at it too: breasts visible, not inverted,
   not cut off, background removed, all facing the same way?
2. If good, run the full conversion (no `--limit`). It is resumable: if the laptop sleeps, run it again.
3. Regenerate the montage on 48 random images and check again. Count failures (logged in
   `data/index/convert_errors.csv`) and look at a few.

## Done when
- One PNG per usable DICOM, `png_index.csv` complete, errors explained, montage looks right.
- PROGRESS.md entry: number converted, failures, total size of `data/png1024`, time taken.

Note: laptop must be plugged in; set Windows to not sleep during the run.
