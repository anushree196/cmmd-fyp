# PROGRESS — project log

Claude Code appends one entry per finished task. Newest at the bottom.
Format:

## YYYY-MM-DD — Task NN: title
- Done: ...
- Numbers: ...
- Surprises: ...
- Next: ...

---

## 2026-10-07 — Task 00: Set up the laptop project
- Done: created `.venv` and installed `requirements-local.txt` (CPU only, no PyTorch); confirmed the paths in
  `config.yaml` match the real folders; set `num_workers: 14` (16 cores − 2); ran `scripts/00_check_env.py`
  (every line OK); `git init` + first local commit.
- Numbers: Python 3.12.10, Git 2.52.0. 5,202 `.dcm` files in 1,775 patient folders (D1: 1,026, D2: 749).
  Clinical xlsx found in `metadata/` (also `metadata.csv`). TOMPEI-CMMD folder already present in Downloads.
  Free disk on C: 75.5 GB (need > 15). Key packages: pydicom 3.0.2, numpy 2.5.3, pandas 3.0.6, opencv 5.0.0.
- Surprises:
  - Python 3.11 is not installed (3.12 and 3.13 are). Used 3.12; all local packages install and import fine.
  - 5,202 DICOMs, not 5,203 as CLAUDE.md / START_HERE.md say (matches the ~5,202 in the master plan summary).
  - The project lives at `C:\Anushree\cmmd-fyp`, not `C:\Users\Anushree\cmmd-fyp`. Not in OneDrive, so fine.
  - `config.example.yaml` was missing from the kit (only `config.yaml` existed, which is git-ignored). Recreated
    the example from it so the repo has a template when Kaggle clones it.
  - `src/config.py` now reads the config as `utf-8-sig`, because a Windows-saved config with a BOM crashed the
    YAML loader.
- Next: [ANU] create an empty private GitHub repo (`cmmd-fyp`) and push. Then Task 01 (inventory).

## 2026-10-07 — Task 01: Inventory
- Done: ran `scripts/01_inventory.py` (50-file trial, then full scan, headers only) → `data/index/dicom_index.csv`,
  5,202 rows, 0 unreadable. Wrote `scripts/01b_inventory_summary.py`, which reads the index + clinical sheet and
  writes `reports/01_inventory_summary.md` (all counts below come from it).
- Side and view tags (decision): side = `ImageLaterality` (filled 5,202/5,202; L 2,682, R 2,520).
  View = `ViewCodeSequence[0].CodeMeaning` (filled 5,202/5,202; "cranio-caudal" 2,601, "medio-lateral oblique"
  2,601). `Laterality`, `ViewPosition` and `SeriesDescription` are empty on every file. No image is missing a
  side or a view. These are the original DICOM labels; TOMPEI's corrected labels get compared in task 03.
- Clinical sheet, real column names: `ID1`, `LeftRight`, `Age`, `number`, `abnormality`, `classification`,
  `subtype`. 1,872 rows = one row per labelled breast, 1,775 patients (1,678 with one labelled breast, 97 with two).
  Values: `LeftRight` L 988 / R 884; `number` always 2; `abnormality` mass 1,149 / both 461 / calcification 262;
  `classification` Malignant 1,316 / Benign 556; `subtype` Luminal B 376 / Luminal A 152 / HER2-enriched 135 /
  triple negative 86 / empty 1,123. No duplicate (ID1, LeftRight) rows. Every patient is in both the sheet and
  the DICOM folders.
- Numbers:
  - Images: 5,202 (D1 2,214; D2 2,988). Patients: 1,775 (D1 1,026; D2 749). 949 patients have 2 images, 826 have 4.
  - Breasts (patient + side): 2,601, every one has exactly one CC and one MLO. Labelled breasts: 1,872.
  - Join on patient ID + side: 3,744 images labelled, 1,458 unlabelled.
  - Benign / malignant: per image 1,112 / 2,632; per breast 556 / 1,316; per patient 465 / 1,310 (patient counted
    malignant if any breast is malignant).
  - Subtype (LumA / LumB / HER2 / TN): per image 304 / 752 / 270 / 172; per breast and per patient
    152 / 376 / 135 / 86. Patients with a subtype: 749 (all D2, exactly one subtyped breast each).
  - Age: 17 to 87, mean 47.4, median 46, none missing; same age on both rows of two-breast patients.
  - Format: all 2294 × 1914, MONOCHROME2, all have a window/VOI LUT. `Manufacturer` tag empty everywhere.
- Surprises:
  - 1,458 images (729 D2 patients × 2 views) are the *other* breast of a subtyped patient and have no clinical
    row. They are not labelled benign or normal, so they must not be used as benign examples.
  - 30 patients have one benign breast and one malignant breast, so "benign vs malignant" is really a per-breast
    label. Splits must still be per patient.
  - D2 is not purely "malignant with subtype": it holds 12 benign breasts, and 4 malignant breasts with no subtype.
    567 malignant breasts in total (563 of them D1) have no subtype.
  - 2 files are 16-bit, not 8-bit: patient D1-1343, left CC and left MLO. Task 02 must handle them.
  - The images are already 8-bit in the DICOMs (5,200 of 5,202), so the PNG conversion loses no bit depth.
  - The index column for side is called `side` (not `laterality` as the task file says), because
    `scripts/02_convert.py` reads `side`; the `laterality` column is the raw, empty `Laterality` tag.
  - Added `tabulate` to `requirements-local.txt` (pandas needs it to write markdown tables).
- Next: Task 02 (DICOM → PNG). Decisions for Anu before task 04: whether Stage 1 trains per breast (my
  recommendation) and whether the 1,458 unlabelled images are left out (my recommendation).

## 2026-10-07 — Task 02: DICOM → PNG
- Decisions by Anu (before the run): Stage 1 trains per breast with per-patient splits; the 1,458 unlabelled
  images are excluded and counted in the data-flow report (both now in `docs/master_plan_summary.md`).
  Pixel values: 8-bit files are kept exactly as stored (no windowing, no percentile stretch); only the two
  16-bit D1-1343 files are rescaled to 0–255.
- Done: changed `scripts/02_convert.py` (pixel handling, breast finding, flip rule; details under Surprises),
  ran the 20-image trial, then the full conversion → `data/png1024/` + `data/index/png_index.csv`.
  Wrote `scripts/02b_convert_checks.py` (counts, flip vs side tag, crop sizes, 16-bit brightness check,
  `reports/02_qc_16bit.png`). Regenerated `reports/02_qc_montage.png` on 48 random images.
  Updated steps 1–4 of `tasks/02_convert.md` to describe what the script now does.
- Numbers (final run):
  - 5,202 converted, 0 failed (no `convert_errors.csv`), 5,202 PNGs on disk, none missing, no duplicate names.
  - Time 1.7 min with 14 workers. `data/png1024` = 0.92 GB.
  - PNGs are 1024 px tall, width 202–812 px (median 397).
  - Crop kept, as a share of the original 2294 × 1914 image: width min 0.15 / median 0.40 / max 0.93;
    height min 0.42 / median 0.90 / max 1.00. No crop kept the whole image; none is suspiciously small.
  - Flipped 2,519, not flipped 2,683. Flip agrees with the side tag on 5,187 images.
  - 16-bit check: the two files had an identity window (centre 32768, width 65536) and used the full 0–65535
    range; the 8-bit files have an identity window too (centre 128, width 256). After dividing down, their
    breast brightness (mean of non-black pixels) is 58 and 65; 300 random 8-bit images: 5th pct 42, median 62,
    95th pct 91. So they sit on the same scale as everything else.
- Surprises:
  - The kit's Otsu threshold was wrong for this data. It landed around 43 (median), inside the breast, so the
    crop cut off fatty tissue and skin: on 2,112 images the Otsu box was under 70% of the real breast area, and
    47 crops were under 30% of the image height. The background is exactly 0 (median 74% of pixels), so the
    script now uses a fixed threshold (pixel > 10) and keeps the largest connected region.
  - The kit's flip rule (compare the two halves of the *cropped* image) was wrong on about 700 images
    (720 disagreed with the side tag). It now asks which half of the *full* image holds the breast, which was
    never ambiguous on any image.
  - Because of these two bugs the first full run (1.8 min, 1.29 GB) was thrown away: PNGs deleted and
    reconverted. All numbers above are from the second run.
  - 15 images (9 patients) have a side tag that disagrees with where the breast actually is; list saved to
    `data/index/side_tag_vs_pixels.csv`. Patients: D1-0252, D1-0690, D1-0711, D1-0999, D2-0041, D2-0112,
    D2-0224, D2-0229, D2-0642. The PNG orientation is right either way (it comes from the pixels); whether the
    *label* is wrong gets checked against TOMPEI's corrected labels in task 03.
  - The PNG file name and the `side` column still carry the original DICOM side tag for those 15 images.
  - Far faster and smaller than the plan expected (1.7 min and 0.92 GB, not 20–60 min and 2–3 GB), because
    the DICOMs are 8-bit and the crops are narrow.
- Next: [ANU] look at `reports/02_qc_montage.png` and `reports/02_qc_16bit.png`. Then Task 03 (TOMPEI masks).
