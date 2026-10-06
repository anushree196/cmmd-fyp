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

## 2026-10-07 — Task 02 follow-up: two-image check, crop threshold lowered (supersedes the Task 02 numbers)
- Why: Anu looked at the QC pictures and asked for two images to be checked uncropped next to their PNG.
- Done: wrote `scripts/02c_compare_original.py` (original with crop box | original 8× brighter | saved PNG, plus
  numbers) → `reports/02_qc_original_vs_png.png`. Findings:
  - D1-1343 L MLO: not cut off sideways. The skin line sits at the crop edge; it is invisible at normal
    brightness because this 16-bit file has near-black fatty tissue. The breast is in the left half, not flipped.
  - D2-0347 R MLO: not mirrored wrongly. In the original the breast is in the right half with the chest wall on
    the right edge, so flipping it is correct. The bright patch is on the skin side in the original pixels too
    (soft-edged, not saturated: 0% of pixels at 250–255), so it is something on the skin, not a burned-in label
    and not a conversion artefact.
  - Real problem found on D2-0347: the crop started at y = 598 and cut off the faint upper breast (27,586 pixels
    brighter than 10 and 202,091 non-black pixels were outside the box).
- Fix: the breast threshold went from "pixel > 10" to "pixel > 0" (any non-black pixel). Measured on all 5,202
  images before changing: with > 10, 529 images lost more than 1% of their non-black pixels and 81 lost more
  than 5%; with > 0 that is 142 and 11. PNGs deleted and reconverted (third and final run). `png_index.csv` has
  a new column `outside_share` = share of non-black pixels left outside the crop.
- Numbers (final, these replace the Task 02 numbers above):
  - 5,202 converted, 0 failed, 5,202 PNGs on disk, 1.7 min, `data/png1024` = 0.90 GB.
  - PNGs 1024 px tall, width 203–818 (median 400).
  - Crop as a share of the original: width min 0.16 / median 0.41 / max 0.93; height min 0.45 / median 0.91 /
    max 1.00.
  - Flipped 2,519 / not flipped 2,683; the same 15 images (9 patients) disagree with the side tag.
  - `outside_share`: median 0.0000, 99th percentile 0.021, max 0.240.
  - After the fix: D2-0347 R MLO crop is y 0–2271 with 0 non-black pixels outside; D1-1343 L MLO crop is
    x 0–801, y 0–1901 with 5,890 non-black pixels outside (a thin strip below the breast at the image edge).
  - 16-bit brightness check unchanged: 58 and 65 against a median of 62.
- Outliers looked at (`reports/02_qc_crop_outliers.png`, the 3 images with the highest `outside_share` and the
  2 widest crops):
  - D1-0059 R CC (0.167) and D2-0654 R CC (0.147): what is left out is a separate bright object at the image
    edge that is not the breast. Dropping it is what we want.
  - D1-0951 R MLO (0.240): an odd source image with black holes inside the tissue; the upper strip (pectoral
    area) is disconnected from the breast and is left out. Not fixable by a threshold. Flagged, kept.
  - D2-0607 R MLO and D2-0440 L MLO (widest crops, 0.89 and 0.93 of the width): the source images really do
    contain that much non-black content connected to the breast (chest/abdomen, a band along the top). Kept.
  - Not checked by eye: the other 139 images with `outside_share` > 1%.
- Next: Task 03 (TOMPEI masks).

## 2026-10-07 — Task 03: TOMPEI-CMMD masks and the Stage 2 set
- Done: inspected the TOMPEI download; wrote `scripts/03_tompei_labels.py` (corrected sides and per-breast
  labels → `data/index/image_sides.csv`, `data/index/breast_labels.csv`, `reports/03_tompei_labels.md`) and
  `scripts/03_tompei_masks.py` (masks → `data/masks1024/`, `data/index/mask_index.csv`,
  `data/index/stage2_patients.csv`, `reports/03_stage2_counts.md`, `reports/03_mask_overlay.png`,
  `reports/03_mask_overlay_swapped.png`). Run order: labels script first, then masks script.
- TOMPEI format (confirmed, matches the master doc):
  - `annotations/TOMPEI-CMMD_v01_20250123/{patient}_MLO_{L|R}_AnnotationFile.json`. Each file is a list of
    lesions; each lesion has `cgPoints` (list of `{x, y}`, in original DICOM pixels), `label` (mass, calc, dist,
    FA, FAD, lipoma; 70 have a trailing space, "calc "), `type` (Draw 1,720 / Polyline 53), `_id`, `color`.
  - 2,770 JSON files in the folder, but 1,385 are macOS junk copies under `__MACOSX`; 1,385 are real.
  - `TOMPEI-CMMD_clinical_data_v01_20250121.xlsx`: sheets README, "Imaging Diagnosis Details Sheet" and
    "Lesion Details Sheet", one row per breast (2,601), with 2–3 header rows each.
  - Link to a CMMD image: by file name only (patient + MLO + side). There is no SOP UID in TOMPEI.
- Link rule (decision): annotation → our MLO image of that patient with the same **corrected** side. Matching on
  the DICOM side tag is wrong for 4 patients (the outline falls in the opposite half of the image).
- Numbers, labels:
  - TOMPEI class per breast: Malignant 1,167 / Normal 1,054 / Benign 215 / Invisible 140 / Exclusion 25.
    "Normal" includes benign with no lesion locatable on the image; "Invisible" = malignant but not locatable.
  - Image sides corrected on 16 images (8 patients): D1-0252, D1-0690, D1-0711 (TOMPEI "Reversed left and
    right", both images); D1-0999, D2-0224, D2-0229, D2-0642 (the two MLO tags swapped); D2-0041 (the two CC
    tags swapped). One image, D2-0112 L CC, disagrees with the pixels but keeps its tag (looks stored mirrored).
    After correction: 2,601 breasts, identical to TOMPEI's 2,601, no duplicate (patient, side, view).
  - CMMD label rows moved to the other breast: 10 (the 3 D1 patients above, plus D2-0048, D2-0132, D2-0153,
    D2-0212, D2-0282, D2-0458, D2-0637, where TOMPEI found the cancer on the other side from the CMMD sheet).
  - CMMD class vs TOMPEI class per breast, after the moves: CMMD Benign 556 = TOMPEI Benign 207 + Normal 342 +
    Exclusion 7. CMMD Malignant 1,316 = Malignant 1,167 + Invisible 140 + Exclusion 9. No CMMD row 729 =
    Normal 712 + Benign 8 + Exclusion 9. Ages agree everywhere.
  - TOMPEI also gives breast density (heterogeneous dense 1,671 / extremely dense 551 / scattered 340 / fatty 30
    / missing 9) and BI-RADS category per breast.
- Numbers, masks:
  - 1,385 annotation files, all MLO, 1,363 patients (D1 700 files, D2 685) → 1,385 masks, 0 failed, 3.8 MB.
  - 1,773 lesions. Per breast: 1 lesion 1,069 / 2: 271 / 3: 26 / 4: 14 / 5: 3 / 6: 1 / 7: 1. Number of outlines
    in each file equals TOMPEI's "Number of lesions" on all 1,385.
  - No empty masks. Outlined area cut off by our crop box: none on 1,380 masks; 5 masks lose some (D1-1057 L
    13.1%, D1-0992 L 7.3%, D2-0463 R 5.7%, D2-0326 L 5.5%, D2-0163 R 2.1%).
  - Mask area as a share of the PNG: min 0.0004, median 0.026, max 0.368.
  - Overlays checked by eye: outlines sit on the lesions for left and right breasts, including the 4 patients
    with swapped MLO tags.
- **Stage 2 set = subtype label AND lesion mask on that breast AND TOMPEI class Malignant: 671 patients**
  (`data/index/stage2_patients.csv`, one breast per patient, every one has both a CC and an MLO PNG).
  - Luminal A 140 (of 152), Luminal B 335 (of 376), HER2-enriched 126 (of 135), triple negative 70 (of 86).
  - 78 of the 749 subtyped patients are lost: 75 Invisible (no outline exists), 3 Exclusion.
  - Patients with a subtype label: 749. Patients with any TOMPEI mask: 1,363.
  - Stage 2 age 21 to 87, mean 50.2. CMMD abnormality: mass 364 / both 219 / calcification 88.
  - 6 Stage 2 patients have their subtype on the other breast from the CMMD sheet (TOMPEI's correction).
- Surprises:
  - TOMPEI has 1,385 annotated images, not ~2,436 as the plan said (fixed in `docs/master_plan_summary.md`).
  - TOMPEI does not give "corrected view labels"; all views agree with ours. Its corrections are left/right.
  - TOMPEI's classes are not just benign/malignant: 342 of the 556 CMMD-benign breasts are "Normal" (no lesion
    locatable) and 140 of the 1,316 malignant ones are "Invisible". This matters for Stage 1 (see Next).
  - TOMPEI recommends excluding 25 breasts (CV port 7, phyllodes tumour 6, white objects 3, and others).
  - The PNG and mask file names still carry the original DICOM side tag; for the 16 corrected images the right
    side is in `image_sides.csv` (`side_corrected`), which later steps must use.
  - 53 outlines are of type "Polyline"; they are filled as closed shapes like the rest. Not checked one by one.
- Next: [ANU] look at `reports/03_mask_overlay.png`. Decision needed before task 04: how Stage 1 uses TOMPEI's
  classes (Normal / Invisible / Exclusion). Then Task 04 (pairs + splits).
