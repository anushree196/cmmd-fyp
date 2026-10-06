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

## 2026-10-07 — Task 04: CC/MLO pairs and patient-wise splits
- Decision by Anu (before the run, now in `docs/master_plan_summary.md`): Stage 1 label = CMMD benign /
  malignant with TOMPEI side corrections; drop the 16 TOMPEI-excluded breasts; keep TOMPEI class, density and
  BI-RADS as extra columns for later subgroup results ("Invisible" cancers, dense breasts).
- **Damaged source image flagged: D1-0951 R MLO.** Black holes inside the tissue, upper strip disconnected and
  cut off by the crop (found in the task 02 follow-up). It carries a `qc_note` in `pairs.csv`. TOMPEI
  independently lists this breast as Exclusion ("Scale is incorrect"), so it is one of the 16 dropped breasts
  and is in neither stage.
- Done: wrote and ran `scripts/04_pairs_splits.py` → `data/index/pairs.csv` (all 2,601 breasts),
  `data/splits/stage1.csv`, `data/splits/stage2.csv`, `data/splits/stage2_e0_imagewise.csv`,
  `reports/04_data_flow.md`. All sanity checks are asserts and all pass: no patient in two splits; a patient
  has the same split in both stage files; class shares in every split within 3 percentage points of overall
  (Stage 1, Stage 2 and E0); every PNG and mask the tables point to exists; no missing label or age.
- Design choice (mine, recorded under "Decisions made in this kit"): each patient is assigned to a split
  **once**, and both stage files are cut from that assignment, instead of two independent splits as the task
  file says. Otherwise a Stage 2 test patient could be a Stage 1 training patient and the chained 5-class
  score would leak. Strata: Stage 2 patients by subtype; the rest by benign only / malignant / one benign +
  one malignant breast.
- Numbers, data flow:
  - 5,202 images → 2,601 breasts, all paired (0 missing a view, 0 with more than one image per view).
  - − 729 breasts (1,458 images) with no CMMD label. TOMPEI class of these: Normal 712 / Exclusion 9 / Benign 8.
  - − 16 labelled breasts TOMPEI recommends excluding (phyllodes tumour 6, white objects 2, and 8 single reasons).
  - **Stage 1 set: 1,856 breasts (3,712 images), 1,762 patients; benign 549 / malignant 1,307.**
    94 patients have two breasts in the set; 30 have one benign and one malignant. D1 1,095 / D2 761 breasts.
    Age 17–87, mean 47.4. 13 patients have no breast in Stage 1.
  - Stage 1 by TOMPEI class: benign = Benign 207 + Normal 342; malignant = Malignant 1,167 + Invisible 140.
  - **Stage 2 set: 671 patients (1,342 images)**: LumA 140 / LumB 335 / HER2 126 / TN 70 (unchanged from task 03).
- Numbers, splits (train / val / test):
  - Stage 1 patients 1,233 / 264 / 265. Breasts 1,289 / 280 / 287.
    Benign 375 / 84 / 90; malignant 914 / 196 / 197 (malignant share 70.9% / 70.0% / 68.6%; overall 70.4%).
  - Stage 2 patients 470 / 100 / 101. LumA 98 / 21 / 21; LumB 235 / 50 / 50; HER2 88 / 19 / 19; TN 49 / 10 / 11.
  - Subgroups in Stage 1: Invisible cancers 92 / 26 / 22; benign with no visible lesion (TOMPEI Normal)
    234 / 45 / 63; dense breasts 1,107 / 239 / 251; not dense 182 / 41 / 36; no density missing in Stage 1.
  - E0 (image-wise 72/18/10 on the 1,342 Stage 2 images): 966 / 241 / 135 images.
- Surprises:
  - E0's image-wise split leaks heavily, as expected: 282 of 671 patients have their CC and MLO in different
    splits, and 95 of the 135 E0 test images have the same breast's other view in E0 train. Worth quoting when
    comparing E0 with E1.
  - Only 11 triple-negative patients and 22 Invisible cancers are in the test split; subgroup results on them
    will have wide error bars.
  - The subgroup columns were not used for stratifying, so their shares vary by split (for example TOMPEI
    Normal is 63 of 90 benign test breasts but 234 of 375 in train).
  - Stage 2 has only 11 "fatty" breasts in total (6 / 2 / 3).
- Next: Task 05 (upload the prepared data to Kaggle). [ANU] Kaggle account, phone verification and API token.

## 2026-10-07 — Audit of tasks 01–04, and re-split (supersedes the Task 04 split numbers)
- Why: Anu asked for an independent audit before the Kaggle upload, and for the splits to be stratified by
  TOMPEI class as well.
- Done: wrote `scripts/05_audit.py`. It imports nothing from the earlier scripts and recounts from the DICOM
  folder listing, the PNG and mask folders, the CSV tables and the two original spreadsheets →
  `reports/05_audit.md`, `reports/05_audit_montage.png`, `reports/05_audit_masks_off_breast.png`.
  Run once on the Task 04 state (all counts matched PROGRESS.md), then again after the re-split.
- **Result: no problems found. Nothing in the data, labels, masks or pairing needed fixing.** The only change
  made is the re-split below.
  - Counts: all 38 logged numbers recount exactly (5,202 DICOMs / PNGs, 2,601 breasts, 1,775 patients, 1,385
    masks, Stage 1 1,856 breasts and 1,762 patients, 549 / 1,307, Stage 2 671, and every split size). 13
    cross-checks between files pass (for example every PNG is used by exactly one breast; git tracks no data).
  - Leakage: 0 patients in two splits (Stage 1, Stage 2); all 671 Stage 2 patients have the same split in
    `stage1.csv`; 0 images in two Stage 1 splits. E0 leaks by design (282 of 671 patients).
  - Labels: 20 random breasts (seed 2026) traced field by field from the raw CMMD and TOMPEI sheets to
    `pairs.csv`: 0 mismatches. The same comparison on all 2,601 breasts: 0 mismatches. All 1,872 CMMD rows are
    used exactly once; exactly 10 breasts take their label from the other side's row (the known moves).
  - Files: 5,202 PNGs and 1,385 masks all open. 0 blank, 0 all-white, 0 flat, 0 wrong size, 0 non-8-bit PNGs.
    Masks: all 0/255 only, same size as their MLO PNG, 0 empty, 0 over half the image.
  - Picture: 16 random Stage 2 test breasts (CC | MLO with outline | mask) look right by eye.
- Re-split (`scripts/04_pairs_splits.py`): the patient strata now also use TOMPEI class. Stage 2 patients by
  subtype (unchanged); benign-only patients split into "lesion visible" (194) and "no visible lesion" (265);
  malignant patients not in Stage 2 into "visible" (477) and "invisible" (136); one benign + one malignant
  breast (19). A new assert requires the Normal and Invisible shares to be within 3 points in every split.
  610 of 1,762 patients changed split. Nothing had been trained, so no result depends on the old split.
  - "Normal" among benign breasts, train / val / test: before 62.4% / 53.6% / 70.0%; now 62.9% / 61.0% / 61.0%.
  - "Invisible" among malignant breasts: before 10.1% / 13.3% / 11.2%; now 10.8% / 10.7% / 10.2%.
- Numbers, splits (final; train / val / test):
  - Stage 1 patients 1,233 / 264 / 265. Breasts 1,299 / 278 / 279.
    Benign 385 / 82 / 82; malignant 914 / 196 / 197 (malignant share 70.4% / 70.5% / 70.6%).
  - Stage 2 patients 469 / 101 / 101. LumA 98 / 21 / 21; LumB 234 / 50 / 51; HER2 88 / 19 / 19; TN 49 / 11 / 10.
  - Subgroups in Stage 1: Invisible cancers 99 / 21 / 20; benign TOMPEI Normal 242 / 50 / 50; benign TOMPEI
    Benign 143 / 32 / 32; dense 1,120 / 243 / 234 (86.2% / 87.4% / 83.9%); not dense 179 / 35 / 45.
  - E0 unchanged: 966 / 241 / 135 images (it does not depend on the patient split).
- Surprises (not bugs):
  - 60 of the 1,773 TOMPEI annotations are boxes (6 points or fewer), not traced outlines. All 60 are
    architectural distortions ("dist"), and every "dist" lesion is a box. 32 Stage 2 breasts have at least one
    box; 14 have only a box (10 / 2 / 2). Shape radiomics on those will describe the box, not the lesion: to
    handle in task 07.
  - 6 masks have under 90% of their area on breast pixels (lowest D1-1057 L, 68%). Looked at all 6: each
    contains a box whose corners overhang the skin edge. Not misalignment.
  - D2-0220 has a subtype and an outlined cancer but is correctly not in Stage 2: the subtype (Luminal B)
    belongs to the right breast, which TOMPEI excludes; the outlined left breast is a second cancer with no
    subtype label.
  - Density was not used for stratifying; the dense share is 83.9% in test against 86.2% in train.
- Next: Task 05 (upload the prepared data to Kaggle). [ANU] Kaggle account, phone verification and API token.

## 2026-10-07 — Task 05: upload to Kaggle
- Anu approved the audit. Kaggle username `honeyyy09`.
- Decision by Anu (for task 07, written into `tasks/07_radiomics.md`): the 14 Stage 2 breasts whose lesion is
  only a box get texture features but no shape features, and are marked `has_box_only`.
- Done:
  - `kaggle.json` was at `C:\Anushree\.kaggle\kaggle.json`; moved to `C:\Users\Anushree\.kaggle\kaggle.json`
    (the standard place; outside the repo, never committed; `.gitignore` also lists `kaggle.json`).
  - Added `has_box_only` to `pairs.csv`, `stage1.csv` and `stage2.csv` (from a new `n_box` column in
    `mask_index.csv`): 14 Stage 2 breasts, 10 train / 2 val / 2 test. Re-ran tasks 03 (masks script), 04 and the
    audit afterwards: splits unchanged, all checks pass, no problems.
  - Wrote `scripts/05_package.py` → `data/kaggle_upload/` and `data/kaggle_code/` (both git-ignored), each with
    a `dataset-metadata.json`; the data folder also holds `manifest.json` (the counts a notebook should find).
  - Uploaded two **private** datasets with `kaggle datasets create --dir-mode zip`:
    `honeyyy09/cmmd-png1024` (png1024.zip 855 MB, masks1024.zip, index.zip, splits.zip, manifest.json) and
    `honeyyy09/cmmd-code` (`src/`, `requirements-train.txt`).
  - Pushed the private test notebook `honeyyy09/cmmd-00-check` (`notebooks/00_check/`, GPU on, internet off,
    both datasets attached) with `kaggle kernels push`; it ran to COMPLETE; fetched its output with
    `kaggle kernels output` → `reports/05_kaggle_check.json`.
- Numbers (counted on Kaggle by the notebook):
  - **5,202 PNGs and 1,385 masks arrived** (manifest says 5,202 and 1,385). PNG bytes 895,567,571.
  - 8 index files, 3 split files. `pairs.csv` 2,601 rows. Stage 1 1,856 breasts (train 1,299 / val 278 /
    test 279). Stage 2 671 patients (469 / 101 / 101). E0 1,342 images. `has_box_only` 14.
  - 0 PNGs and 0 masks named in `pairs.csv` are missing; 0 patients in two Stage 1 splits.
  - One Stage 2 breast opened (D2-0001): CC 385 × 1024, MLO 272 × 1024, mask 272 × 1024, 8-bit greyscale.
  - `src.config` imports from the code dataset. GPU: 2 × Tesla T4, CUDA available, torch 2.11.0, Python 3.13.15.
  - Upload folder 865 MB. Notebook run time under 1 minute.
- Surprises:
  - Datasets mount at `/kaggle/input/datasets/honeyyy09/<name>/`, not `/kaggle/input/<name>/` as the task
    files assumed. Notebooks must search for the folder instead of hard-coding the path (noted in task 06).
  - monai, pyradiomics and grad-cam are NOT preinstalled on Kaggle (timm, shap, SimpleITK, scikit-learn and
    OpenCV are). Training notebooks need Internet ON to `pip install` them.
  - Kaggle runs Python 3.13. pyradiomics is an old compiled package and may not install on 3.13: a risk for
    task 07, not tested yet.
  - Notebooks now get the code from the `cmmd-code` dataset, not a GitHub clone, so no GitHub token is needed;
    the code dataset must be re-uploaded whenever `src/` changes (command in `tasks/06_stage1_training.md`).
  - `index/png_index.csv` and `dicom_index.csv` on Kaggle contain the laptop's DICOM paths
    (`C:\Users\Anushree\Downloads\...`). Harmless on a private dataset; remove the column before ever making
    the dataset public.
  - The dataset licence field is set to "unknown"; set the real CMMD / TOMPEI licence before any public release.
- Next: Task 06 (Stage 1 training code, tested locally on CPU, then run on Kaggle GPU).
