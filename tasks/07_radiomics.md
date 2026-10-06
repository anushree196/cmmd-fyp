# Task 07 — Radiomics on the REAL lesion mask  (runs on: Kaggle CPU notebook)

Goal: `radiomics_features.csv`, one row per Stage 2 MLO image, top-20 selected features.

Why Kaggle and not the laptop: pyradiomics is a compiled package that often fails to install on Windows.
Kaggle is Linux and installs it cleanly. This step needs no GPU — use a CPU notebook and save GPU hours.

## Steps
1. `scripts/07_radiomics.py`: for each Stage 2 image, load the PNG + its mask (from task 03), crop to the mask
   bounding box + 20 px margin (MONAI `CropForegroundd`), run pyradiomics with **the real mask**
   (never `np.ones_like`), classes: firstorder, shape2D, glcm, glrlm. Settings as in Master doc §4.5.
   **Box-only breasts (decided by Anu, 2026-10-07):** 14 Stage 2 breasts have a lesion that TOMPEI marked only
   with a box (a rectangle around an architectural distortion), not a traced outline. They are flagged
   `has_box_only = True` in `splits/stage2.csv` (10 train / 2 val / 2 test). For these breasts compute the
   texture features (firstorder, glcm, glrlm) inside the box as usual, but **no shape features**: a box's
   perimeter or sphericity describes the rectangle, not the lesion. Leave their shape2D columns empty, then
   fill them with the training-split median before the model sees them (fit the median on training rows that
   are not box-only), and keep `has_box_only` as its own input column so the model can tell. Breasts with a
   box AND a traced lesion (18 more) are not flagged; they are treated normally.
2. Feature selection on the **training split only** (no leakage): drop near-constant features, drop one of each
   highly correlated pair (|r| > 0.9), then keep the top 20 by mutual information with subtype. Save the list.
3. Save features + selected list to the Kaggle output; copy the small CSVs to `reports/radiomics/`.

## Done when
- Shape2D features differ across patients (check: std of perimeter/sphericity > 0). If they are all the same,
  the mask is wrong — stop and fix.
