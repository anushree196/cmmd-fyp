# PROGRESS — project log



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

## 2026-10-23 — Task 06: Stage 1 training (benign vs malignant)
- Anu approved task 05, including the median fill for box-only breasts in task 07.
- Kaggle environment re-checked first (`notebooks/01_env`, CPU, Internet ON → `reports/06_kaggle_env.json`):
  Python 3.13.15, torch 2.11.0 (unchanged). monai 1.6.1 and grad-cam install fine. **pyradiomics from PyPI
  fails** (wheel build error on Python 3.13); **from its GitHub source it installs and works** (67 features on a
  test circle, perimeter 263, sphericity 0.95). Pinned to commit `8ed579383` in `requirements-train.txt` and
  `tasks/07_radiomics.md`. The scikit-image fallback is written down there but not needed.
- Code written (`src/`): `data.py` (CC + MLO PNGs scaled to 512 px tall with shape kept, padded right; MONAI
  CacheDataset; train-only augmentation: rotation up to ~10°, ±10% scale, ±20 px shift, contrast and intensity
  changes, no flips), `models.py` (EfficientNet-B3 shared by both views, single grey input channel, View
  Attention, age through a small MLP, 2-class head), `metrics.py` (AUC, sensitivity, specificity, thresholds,
  bootstrap CIs resampling **patients**, 2,000 draws), `train.py` (train + val only), `evaluate.py` (test only,
  refuses to score a run twice). `scripts/make_kaggle_notebook.py` turns a `.py` file into the notebook.
  Inputs: both views + age only (as Anu specified; lesion type is not used).
- Local CPU test (128 px, 32 breasts per split, 2 epochs): runs end to end; evaluate refuses a second test run.
- Training (`notebooks/02_stage1_train` → Kaggle `cmmd-02-stage1-train`, Tesla T4, 512 px, batch 8, AdamW
  lr 1e-4, weight decay 1e-4, 1 warm-up epoch then cosine, mixed precision, early stopping patience 5 on val
  AUC). Class weights from train: benign 1.687, malignant 0.711.
  - Ran 12 of 20 epochs (early stop), about 1 min per epoch after a 7.7 min first epoch (image caching).
    **Best epoch 7, val AUC 0.833 (95% CI 0.786–0.876).**
  - Overfits early: train loss 0.67 → 0.07 by epoch 12, val loss lowest at epoch 3 (0.511) and 7 (0.510), then
    rising to 0.88. Early stopping on val AUC kept epoch 7.
  - Learned view weights on val: CC 0.475, MLO 0.525 (the model uses both views almost equally).
- Thresholds (both chosen on VALIDATION only; test never used for any choice):
  - Youden J (the rule fixed in the code before any results): 0.782 → val sensitivity 54.6%, specificity 97.6%.
  - Val sensitivity ≥ 90% (**added after seeing the val result**, before the test was scored, because Youden
    gave a corner point that misses 45% of cancers): 0.171 → val sensitivity 90.3%, specificity 50.0%.
- **Test, scored once** (`notebooks/03_stage1_test` → `cmmd-03-stage1-test`, 2026-10-23 15:36 UTC, not forced):
  279 breasts, 265 patients, 197 malignant / 82 benign.
  - **Test AUC 0.767 (95% CI 0.707–0.820).**
  - At Youden 0.782: sensitivity 54.3% (47.6–60.9), specificity 84.1% (76.1–91.8);
    found 107 / missed 90 cancers, 69 benign correct / 13 benign flagged.
  - At val-sens-90 0.171: sensitivity 84.3% (79.1–89.1), specificity 43.9% (33.3–54.9);
    found 166 / missed 31 cancers, 36 benign correct / 46 benign flagged.
  - Subgroups (AUC with 95% CI; sensitivity at Youden / at val-sens-90):
    - "Invisible" cancers (20) vs all 82 benign: AUC 0.606 (0.468–0.739); sensitivity 15.0% / 70.0%.
    - Visible cancers (177) vs all 82 benign: AUC 0.785 (0.729–0.838); sensitivity 58.8% / 85.9%.
    - Dense breasts (234; 165 mal, 69 ben): AUC 0.756 (0.689–0.818).
    - Non-dense breasts (45; 32 mal, 13 ben): AUC 0.873 (0.734–0.967).
    - Specificity on benign with no visible lesion (50): 84.0% / 38.0%; benign with a visible lesion (32):
      84.4% / 53.1%.
- Files kept in git: `reports/stage1/` (metrics_val.json, metrics_test.json, val and test probabilities as CSV,
  training_log.csv, training_curves.png, run_config.json). Weights `best.pt` (42 MB) stay as the Kaggle output
  of `cmmd-02-stage1-train`, not in git.
- **GPU time: 33.7 min this task** (training 21.1 min + test scoring 12.6 min, both T4). Earlier GPU use:
  `cmmd-00-check` under 1 min (task 05). The env check ran on CPU. Total so far about 0.58 GPU hours.
- Surprises:
  - Test AUC (0.767) is clearly below val AUC (0.833); the two CIs only just overlap. Part of the gap is
    expected (the best of 12 epochs was picked on val, which flatters val), part is the small sets (82 benign
    in each). The test number is the one to report.
  - Youden's threshold transferred badly: val specificity 97.6% fell to 84.1% on test. The val-sens-90 threshold
    held up better on sensitivity (90.3% → 84.3%).
  - "Invisible" cancers are much harder: AUC 0.61, and its CI (0.468–0.739) includes 0.5, so on this test set the model is not clearly better than chance for them. Dense breasts
    are harder than non-dense (0.76 vs 0.87), as expected; both subgroups are small, so the CIs are wide.
  - Scoring took 12.6 min of a GPU session, mostly the CPU bootstrap. Evaluation notebooks should run with the
    GPU off (or the bootstrap should be vectorised).
  - On Windows the Kaggle CLI fails with a forward-slash folder (`-p data/kaggle_code`); use `data\kaggle_code`.
  - pandas 3 drops the grouping columns inside `groupby().apply()`; `read_split` uses a plain loop instead.
- This is the first Stage 1 model. Any later change to Stage 1 must be judged on val; scoring a new model on
  test would be a second look at the test set and must be reported as such.
- Next: Anu to decide whether to improve Stage 1 first (it overfits; stronger augmentation or regularisation,
  judged on val) or to move on to task 07 (radiomics, CPU) and task 08.

## 2026-10-24 — Task 06 v2: Stage 1 improved once (fixed budget), 5-fold CV ensemble, SECOND test evaluation
- Why: v1 overfitted early (train loss 0.07, val loss rising after epoch 3). Anu asked to improve Stage 1 once
  with a fixed budget, choosing everything on validation only, then score test once more with the frozen
  recipe. **This is the second time the Stage 1 test split has been scored**, for that reason; it is the last.
- Code added: `src/folds.py` (5 folds over train+val patients, same strata as task 04, seed 42),
  `src/evaluate_ensemble.py` (OOF thresholds, ensemble test scoring, refuses a second run), in `src/train.py`
  `--fold`, `--label-smoothing`, `--dropout`, `--backbone-lr`, `--aug strong`, plus guards against 16-bit
  overflow; `scripts/06_compare_stage1.py` (paired v1 vs v2 comparison from the saved test predictions).
- Bugs found on the way (all reproduced and fixed on the laptop CPU before rerunning):
  - First two Kaggle runs crashed with NaN (16-bit overflow on the GPU poisons the batch-norm statistics).
    Fixed: the layers after the encoder run in 32-bit; a step with a non-finite loss is skipped and the
    batch-norm statistics restored; a non-finite prediction batch is redone in 32-bit. No step was skipped in
    any later run.
  - The next two runs finished with near-chance val AUC (0.606, 0.548). Traced by 1-epoch CPU tests (v1
    control val loss 0.66; strong aug 1.50; crop-and-resize alone 2.45; rotation, contrast, brightness alone
    0.66–0.67): MONAI "random resized crop" only zooms IN (train images ~6% larger than val, and stretched),
    made worse by `Resized`'s default "area" mode (blocky texture). **Deviation from Anu's spec:** replaced by a
    symmetric zoom of the same strength (`RandZoomd`, side ×0.894–1.118 = area 80–125%, one factor for both
    axes, bilinear). Rotation ±15°, brightness and contrast as specified.
  - Found while checking the zoom: `RandAffined(scale_range=x)` with one number scales only the first axis
    (height). v1's light augmentation therefore scaled height only (±10%); v1 itself is unchanged.
- Recipe search, fixed train/val split (val = same 278 breasts as v1), at most 3 runs; the 4 failed attempts
  above are not counted as recipes:
  | run | recipe | best epoch | val AUC (95% CI) |
  |---|---|---|---|
  | v1 | light aug, dropout 0.3, wd 1e-4, lr 1e-4 all layers | 7 / 12 | 0.833 (0.786–0.876) |
  | R1 | strong aug, label smoothing 0.1, dropout 0.5, wd 1e-2, backbone lr 3e-5, head 3e-4, 512 px | 5 / 11 | 0.770 (0.710–0.829) |
  | R2 | as R1 at 768 px (batch 6) | 10 / 16 | 0.788 (0.731–0.846) |
  | R3 | as R1 but backbone lr 1e-4 | 14 / 20 | 0.824 (0.771–0.873) |
  768 px fitted on a T4 but was not clearly better than 512 px at 2.3× the GPU time.
- Anu's rule (2026-10-24): run BOTH v1 and R3 through the same 5 folds; pick the higher mean held-out AUC;
  within 0.01 prefer R3 (it overfits less). Fold assignment confirmed identical in both (`reports/stage1_v2/cv_folds.csv`):
  299–300 patients per fold, malignant share 69.8–71.4%, Normal-among-benign 61.7–63.5%, Invisible-among-malignant 10.4–11.7%.
  | recipe | fold held-out AUCs (folds 0–4) | **mean ± std** | pooled OOF AUC (1,577 breasts) |
  |---|---|---|---|
  | v1 | 0.846, 0.796, 0.800, 0.790, 0.842 | **0.815 ± 0.027** | 0.780 |
  | R3 | 0.837, 0.827, 0.802, 0.799, 0.825 | **0.818 ± 0.017** | 0.809 (0.786–0.830) |
  **Winner: R3** (+0.003, within 0.01, so R3 by the tie rule too). R3 is also steadier across folds.
- Final model = ensemble of R3's 5 fold models (mean probability). Thresholds chosen on R3's OOF predictions:
  - Youden 0.611 → OOF sensitivity 67.1%, specificity 82.4%.
  - OOF sensitivity ≥ 90%: 0.169 → OOF sensitivity 90.1%, specificity 43.7%.
- **Test, second evaluation** (`cmmd-06-stage1-ensemble-test`, CPU, 2026-10-24 07:40 UTC, not forced; 279 breasts):
  | | v1 (single model) | **v2 (R3 5-fold ensemble)** |
  |---|---|---|
  | test AUC (95% CI) | 0.767 (0.707–0.820) | **0.787 (0.728–0.843)** |
  | Youden threshold: sensitivity / specificity | 54.3% / 84.1% | 60.9% (54.1–67.7) / 76.8% (67.6–85.5) |
  | 90%-sensitivity threshold: sensitivity / specificity | 84.3% / 43.9% | 94.4% (91.0–97.5) / 25.6% (15.5–35.9) |
  | "Invisible" cancers vs all benign, AUC | 0.606 (0.468–0.739) | 0.679 (0.558–0.793) |
  | visible cancers vs all benign, AUC | 0.785 (0.729–0.838) | 0.799 (0.741–0.852) |
  | dense breasts, AUC | 0.756 (0.689–0.818) | 0.790 (0.726–0.850) |
  | non-dense breasts, AUC | 0.873 (0.734–0.967) | 0.841 (0.700–0.951) |
  - v2 confusion, Youden: found 120 / missed 77 cancers, 63 benign correct / 19 flagged.
    At 90%-sensitivity: found 186 / missed 11, 21 benign correct / 61 flagged.
  - **Paired comparison on the same test breasts** (`reports/stage1_v2/compare_v1_v2_test.json`): AUC
    difference +0.020, 95% CI −0.023 to +0.061; v2 better in 83% of bootstrap draws. **Not statistically
    distinguishable** on 279 breasts. Probabilities of v1 and v2 correlate 0.81.
  - Each single fold model on test (descriptive only, not used for any choice): 0.765, 0.746, 0.751, 0.731,
    0.761. The ensemble (0.787) beats every one of its members.
- Uncertainty for semester 2: `reports/stage1_v2/test_predictions.csv` holds `prob_fold0`–`prob_fold4`, the
  mean `prob` and the spread `prob_std` (mean spread 0.165) for every test breast; OOF predictions in
  `oof_predictions.csv`. Fold weights stay as the Kaggle outputs of `cmmd-07-stage1-r3cv-a/b` (not in git).
- Files: `reports/stage1_v2/` (test and OOF predictions, metrics_test.json, comparison, both recipes' fold
  metrics, logs and val predictions, the three recipe-search runs, the fold assignment).
- **GPU time, Task 06 v2: 385 min = 6.4 h** (T4): crashed attempts 5.0 + 10.1; broken-augmentation runs 22.5 +
  46.0; R1 22.0; R2 48.7; R3 30.0; v1 CV 39.3 + 37.8; R3 CV 72.6 + 51.2. Ensemble test scoring ran on CPU
  (64.8 min, no GPU). Wasted on bugs: 83.6 min.
  **Project total so far: about 7.0 GPU hours** (task 05 check < 1 min, task 06 v1 33.7 min, v2 385 min).
- Surprises:
  - The strong regularisation did not beat v1 on single runs; it only tied within noise once the backbone
    learning rate was restored (R3). Its real gain is stability: lower fold-to-fold spread and a much better
    pooled OOF AUC (0.809 vs 0.780), i.e. its fold models agree better on what a probability means.
  - The 90%-sensitivity threshold from OOF over-shot on test (94.4% sensitivity, 25.6% specificity).
  - The "Invisible" subgroup improved (0.606 → 0.679) but still has a wide CI, with only 20 such cancers.
- Stage 1 is now frozen. The test split is not to be scored again for Stage 1.
- Next: Task 07 (radiomics on the real lesion masks, CPU notebook, pyradiomics from GitHub commit 8ed579383).

## 2026-10-24 — Task 07: radiomics on the real lesion masks
- Done: `src/radiomics_features.py` (extraction + training-only selection) and `scripts/07_radiomics.py`
  → `data/features/radiomics_features.csv` (671 Stage 2 breasts × 67 features), `radiomics_selected.json`,
  `reports/radiomics/selection_table.csv`, `reports/radiomics/summary.md`. Uploaded as the private Kaggle dataset
  `honeyyy09/cmmd-features` (862 KB) so task 08 notebooks can attach it; `scripts/05_package.py` builds it.
- **Ran on the laptop, not on Kaggle** (differs from the task file): the pinned pyradiomics commit `8ed579383`
  installed on Windows / Python 3.12 too, with the same SimpleITK 2.5.6 as Kaggle. 34 s for all 671 lesions.
- Settings (my choice at the time; **superseded the same day by the §4.5 settings, see the next entry**):
  2D (`force2D`), classes firstorder, shape2D, glcm, glrlm; image cropped to the mask's bounding box + 20 px;
  bin width 8 on the 8-bit scale (32 bins); no intensity normalisation (all PNGs share one 8-bit scale); B-spline
  resampling; the real TOMPEI mask (union of all outlined lesions of the breast) as the ROI, never a full box.
- Physical scale (a problem found and fixed before extraction): PNGs were resized by different factors in
  task 02, so one PNG pixel is 0.151–0.211 mm depending on the image. Every image is given its true pixel size
  (DICOM `ImagerPixelSpacing` 0.0941 mm on all 671 MLOs, divided by that PNG's scale factor 0.446–0.622), and
  every lesion is resampled to 0.211 mm (the coarsest, so no image is enlarged). Shape features are in mm / mm².
- Box-only breasts (Anu's rule): 14 of 14 have empty shape2D columns in the CSV; for selection (and later for
  the model) they are filled with the median of the TRAINING breasts that are not box-only (medians saved in
  `radiomics_selected.json`), and `has_box_only` stays as its own column.
- "Done when" check passed: shape features differ between patients (traced outlines): perimeter 15–535 mm
  (median 126, std 86), sphericity 0.19–0.94 (median 0.64, std 0.15), area 14–8,341 mm² (median 423).
- Feature selection on the training split only (469 breasts): 0 near-constant, 38 dropped for |Spearman r| > 0.9
  with a better-ranked feature, 20 kept by mutual information with subtype, 9 left over. Kept: 7 glrlm, 5
  firstorder, 4 glcm, 4 shape2D (PerimeterSurfaceRatio, MajorAxisLength, Perimeter, MinorAxisLength). Top three:
  glrlm_RunEntropy (MI 0.070), glrlm_RunVariance (0.064), glrlm_LongRunLowGrayLevelEmphasis (0.061).
- Surprises:
  - The mutual information values are small (at most 0.07): on their own the radiomics carry only a weak
    subtype signal. E4 in task 08 will show whether they add anything to the images.
  - Three shape features (Elongation, Major/MinorAxisLength) come back from pyradiomics as complex numbers
    with a zero imaginary part (eigenvalues); the code keeps the real part and stops if an imaginary part is
    ever non-zero (it never was).
  - The 18 breasts with a box AND a traced lesion are treated normally (Anu's rule), so their shape features
    describe the union of the outline and the box.
- GPU time: 0 (laptop CPU). Project total unchanged at about 7.0 GPU hours.
- Next: Task 08 (Stage 2 ablation E0–E6).

## 2026-10-24 — Task 07 rerun with the Master Document §4.5 settings (supersedes the features above)
- Why: Anu added `docs/master_document_v2.md` (now committed) and asked for its §4.5 settings.
- Settings now (`src/radiomics_features.py`): **binWidth 25, normalize True, normalizeScale 100**, classes
  glcm, glrlm, shape2D, firstorder, crop margin 20 px (from §4.4 `CropForegroundd(margin=20)`). Kept in addition:
  `force2D` (pyradiomics computes shape2D only in 2D mode; the §4.5 snippet omits it) and resampling every
  lesion to 0.211 mm (task 07 scale fix).
- **Deliberately not copied from the document:** §4.5 runs on the output of the §4.4 lesion pipeline, which
  resizes every lesion crop to 224 × 224 first. That would make every lesion the same size, so area,
  perimeter and axis lengths would describe the crop box, not the tumour — the same kind of shape bug §4.5 was
  written to fix. The crop keeps its real size here; only the pixel size is made common.
- Rerun: 671 of 671 lesions, 0 failures, 67 features. The first run's files are kept in
  `data/features/previous_binwidth8/` and `reports/radiomics/previous_binwidth8/`.
  - Shape features are identical to the first run (they do not depend on grey-level settings):
    perimeter 15–535 mm (std 86), sphericity 0.19–0.94 (std 0.15), area 14–8,341 mm². "Done when" check passes.
  - After normalisation, firstorder_Mean ranges −14 to 197 (it is now relative to each crop, not 0–255).
- Re-selected on the training split only (469 breasts): 0 near-constant, 34 dropped for |Spearman r| > 0.9,
  **20 kept**, 13 left over. Kept by class: firstorder 7, glcm 5, shape2D 5, glrlm 3.
  Top three: glcm_Contrast (MI 0.080), glrlm_GrayLevelNonUniformity (0.061), shape2D_PerimeterSurfaceRatio
  (0.057). Full list and every drop reason in `reports/radiomics/selection_table.csv`.
  - 9 of 20 also chosen in the first run (incl. shape2D Perimeter, MajorAxisLength, PerimeterSurfaceRatio).
  - **5 of the 20 carry almost no signal** (MI < 0.01): firstorder_Skewness, shape2D_Elongation,
    firstorder_Median, firstorder_Minimum, and shape2D_Sphericity (MI 0.000). 14 candidates share MI = 0, so the
    20th place is a tie; the sort is now stable (ties keep pyradiomics' own order) so the choice is reproducible.
- Uploaded: new versions of `honeyyy09/cmmd-features` and `honeyyy09/cmmd-code`.
- GPU time: 0. Project total unchanged at about 7.0 GPU hours.
- Next: wait for Anu's "go", then Task 08 (Stage 2 ablation E0–E6).

## 2026-10-24 — Task 08: Stage 2 ablation E0–E6, the baseline re-run, and the one-time test scoring
- Plan approved by Anu with decisions: E6 = E5 as a 5-fold CV ensemble; chained 5-class uses the soft rule
  (P(subtype) = p(malignant) × Stage 2 probability; benign breasts without a mask get 1/4 per subtype); E1–E6 at
  512 px plus an E1-224 bridge; the paper's per-class numbers from `docs/baseline_paper_notes.md` (Benign 100,
  LumA 67, LumB 74, HER2 78, TN 78, images-only overall 61.3). Anu then redefined E0 as an exact copy of the
  paper (one 5-class model on every labelled image) and added E0-images, E0-meta, E0-patient, and later
  E0-paperdata. All models and settings fixed on validation; **test scored once for all experiments together**.
- **Baseline code is public:** https://github.com/serag-ai/Multimodal-BC-Classifier (checked 2026-10-24;
  notebooks uploaded 2026-04-13; no licence → read, not copied; cited in `README.md` and the report). What it shows:
  - **Metadata leak:** "tumour class" is set from the image's folder — every benign image gets 0 ("None"), every
    malignant one 1–3 — although CMMD gives benign breasts a real lesion type (in our 1,098 benign images: mass
    812, both 160, calcification 126). The metadata therefore reveals the benign label.
  - **88.87% is a micro-average** (Keras `AUC()` on one-hot labels). Model used = last of 10 epochs.
  - Model: Xception (all but the last 20 Keras layers frozen) → GAP → Dense 512 → Dropout 0.3; metadata (age
    binarised at 40, tumour class 0–3 as one number) → Dense 32 → Dropout 0.3; concat → 256 → 128 → 5. Adam 1e-3,
    balanced class weights, batch 64, 10 epochs, LR halved on plateau. Re-implemented in `src/e0.py` (timm
    `legacy_xception` = the same TF ImageNet weights; same frozen layers; whole frame rebuilt from our PNGs, un-mirrored,
    squashed to 224).
- **Eligible images** (`scripts/08_e0_eligibility.py` → `reports/08_e0_eligibility.md`): ours 2,590 (1,223 patients;
  benign 1,098, LumA 300, LumB 750, HER2 270, TN 172). Labelling per patient instead gives 4,040 — 16 short of the
  paper's 4,056 — so the paper very likely labelled per patient: 1,458 images of breasts with no labelled cancer
  were trained and tested as subtypes. Their image-wise split also leaks: 198 of our 260 E0 test images have a
  sibling image of the same patient in train. E0-paperdata split 2,908 / 727 / 405 (paper 2,920 / 730 / 406).
- **Test, the leak ladder** (5 classes, average of 3 seeds, `reports/ablation_table.md` §1):
  | run | micro AUC | macro AUC | Benign | LumA | LumB | HER2 | TN |
  |---|---|---|---|---|---|---|---|
  | paper (published) | 0.889 | ≈0.794 | 1.00 | 0.67 | 0.74 | 0.78 | 0.78 |
  | E0-paperdata (their full protocol) | 0.859 | 0.770 | 1.000 | 0.714 | 0.755 | 0.735 | 0.646 |
  | E0 (our correct labels) | 0.920 | 0.850 | 1.000 | 0.821 | 0.826 | 0.830 | 0.773 |
  | E0-truemeta (real lesion types) | 0.685 | 0.632 | 0.738 | 0.618 | 0.514 | 0.713 | 0.577 |
  | E0-patient (patient-wise split) | 0.904 | 0.810 | 1.000 | 0.728 | 0.795 | 0.807 | 0.721 |
  Controls: E0-images micro 0.689 (paper images-only 0.613); **E0-meta (metadata only, no image) micro 0.902,
  Benign 1.000** — the headline number does not need the mammogram; E0-meta-true micro 0.614.
  We reproduce the paper's protocol (0.859 vs 0.889); removing the leak alone drops micro AUC to 0.685.
- **Test, E1–E6** (4 subtypes, same 101 test patients, average of 3 seeds / 5 folds; macro AUC with 95% CI):
  E1-224 0.502 (0.41–0.60), E1 0.551 (0.47–0.64), E2 0.586 (0.49–0.68), E3 0.590 (0.51–0.67), E4 0.618
  (0.54–0.69), E5 0.644 (0.57–0.72), E6 0.587 (0.51–0.66). Validation (mean ± std over seeds): E1 0.611 ± 0.043,
  E1-224 0.586 ± 0.014, E2 0.622 ± 0.013, E3 0.586 ± 0.011, E4 0.576 ± 0.017, E5 0.590 ± 0.002, E6 0.643 ± 0.034
  (5 folds). Validation and test rankings disagree (best val E6, best test E5) and all test CIs overlap: **no single
  component is shown to help** on 101 test patients. Per-class test AUC in `reports/ablation_table.md` §2.
- **Test, chained Stage 1 v2 → E6, 5 classes** (82 benign + 101 subtyped breasts; 96 other Stage 1 test breasts
  cannot get a 5-class label): micro 0.775 (0.72–0.82), macro 0.724 (0.67–0.77); Benign 0.822, LumA 0.707,
  LumB 0.636, HER2 0.799, TN 0.658. These subtype AUCs include benign negatives and are not comparable with §2.
- Surprises:
  - E0 with our correct labels scores HIGHER than the paper's own labelling (micro 0.920 vs 0.859): per-patient
    labels put 1,458 normal-looking breasts into subtype classes, which is label noise, not help.
  - E0-patient barely drops (0.904): with the leak present the split hardly matters; the leak dominates.
  - Stage 2 runs stopped early (best epochs mostly 1–6 for E3–E6): the subtype signal in these images is weak.
  - Runs were much faster than estimated (4–9 min each, not 10–18).
- Files: `reports/ablation_table.md`, `reports/08_e0_eligibility.md`, `reports/stage2/` (val metrics, logs and
  predictions of every run; the one-time test predictions per experiment with every seed's and fold's
  probabilities; chained 5-class predictions and metrics; E0 row tables; E6 folds), `README.md` (new).
  Weights stay as Kaggle outputs of `cmmd-08-e0`, `cmmd-08-e0-paperdata`, `cmmd-09-s2-a`…`-e`.
- **GPU time, task 08: 212.6 min = 3.5 h** (E0 family 41.9, E0-paperdata 27.5, E1/E1-224/E2 37.4, E3 29.3, E4
  18.6, E5 18.4, E6 39.4). Test scoring on CPU (76.8 min). **Project total about 10.5 GPU hours.**
- Next: Task 09 (Grad-CAM and SHAP).

## 2026-10-24 — Task 08b: synopsis tables and figures (+ E0-clean)
- Done: `scripts/08b_synopsis.py` builds everything in `reports/synopsis/` from saved files only (each table
  lists its sources): `tables.md` with T1–T6, key findings, figure list; one CSV per table; F1–F8 as 300-dpi
  black-and-white PNGs (Times-style serif). Every number is read from a file by the script, not retyped.
- **One new run, E0-clean** (E0 with real lesion types AND our patient-wise split, 3 seeds; `src/e0.py`,
  notebook `cmmd-08-e0-clean`). Nothing is chosen on validation in E0 (last epoch kept, as the paper), so the
  notebook trains it and then scores its test set once (`--only E0-clean`; 2026-10-24 14:11 UTC, not forced) →
  `reports/stage2/test_e0clean/`. First attempt failed at import (no `pip install monai`; 0.6 min, nothing trained).
  - Test (388 images, patient-wise): micro AUC 0.704 (0.66–0.74), macro 0.602 (0.55–0.65); Benign 0.681,
    LumA 0.612, LumB 0.499, HER2 0.723, TN 0.495; ACC 0.381, F1 (macro) 0.280.
- **E0-patient and E0-clean re-scored on 4 subtypes, 101 Stage 2 test patients** (CPU, from saved test
  probabilities only: benign column dropped, subtypes renormalised, CC and MLO averaged per breast):
  E0-patient macro AUC 0.520 (0.44–0.61), E0-clean 0.546 (0.46–0.63); validation 0.563 ± 0.019 and
  0.593 ± 0.009. Both below E2–E5 on the same patients (T4).
- Leak ladder (T3, test micro / macro AUC): paper 0.889 / ≈0.794 → E0-paperdata 0.859 / 0.770 → E0 0.920 /
  0.850 → E0-meta 0.902 / 0.850 → E0-truemeta 0.685 / 0.632 → E0-patient 0.904 / 0.810 → E0-clean 0.704 / 0.602.
- Figures: F1 flowchart, F2 class distribution, F3 architecture, F4 training curves, F5 ROC (E0 vs E0-clean,
  chained), F6 Stage 1 ROC with both operating points, F7 leak ladder, F8 ablation with CIs.
  - **F4 is partial:** the Stage 2 logs never recorded validation loss (`src/stage2.py` did not log it), so the
    E5 panel shows training loss and validation macro AUC only. Stage 1 v2 logs are complete. Nothing skipped
    otherwise.
- `reports/synopsis/key_findings.md`: the 10-line plain-English summary for the synopsis.
- GPU time: 18.5 min (E0-clean 17.9 + failed start 0.6). **Project total about 10.8 GPU hours.**
- Next: Task 09 (Grad-CAM and SHAP) — waiting for Anu.
