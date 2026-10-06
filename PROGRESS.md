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
