# Task 01 — Inventory: what exactly is in the 21 GB?  (runs on: laptop, ~5–15 min, CPU)

Goal: one table `data/index/dicom_index.csv` with one row per DICOM, joined to the clinical labels.
This replaces clicking through folder after folder. Reads **headers only** (fast, no pixels).

## Steps
1. Run `python scripts/01_inventory.py --config config.yaml --limit 50` first, inspect the summary.
2. Look at which tags actually hold laterality (L/R) and view (CC/MLO). Candidates: `ImageLaterality`,
   `Laterality`, `ViewPosition`, `ViewCodeSequence[0].CodeMeaning`, `SeriesDescription`. The script records all
   of them; decide which is reliable and write it in PROGRESS.md. If none are filled, fall back to the retriever's
   `metadata.csv` or (later) TOMPEI-CMMD's corrected labels.
3. Run the full scan (no `--limit`).
4. Open the clinical xlsx with pandas; **print the real column names and unique values** of the label columns
   (benign/malignant and subtype). Record them in PROGRESS.md. Update `scripts/01_inventory.py`'s join if needed.
5. Join on patient ID + laterality. Report: images per patient, patients with both CC and MLO per breast,
   class counts (benign / malignant; LumA / LumB / HER2 / TN) **per patient and per image**, and age range.
6. Save the summary table to `reports/01_inventory_summary.md` (small, committed).

## Done when
- `data/index/dicom_index.csv` exists with columns: path, patient_id, study_uid, series_uid, sop_uid, laterality,
  view, rows, cols, bits_stored, photometric, has_voi_lut, plus clinical columns.
- Every DICOM has a laterality and view, or the missing ones are counted and explained.
- PROGRESS.md entry lists the real column names and all counts.
