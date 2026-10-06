# Task 04 — CC/MLO pairing and patient-wise splits  (runs on: laptop, seconds)

Goal: the tables every training notebook reads. No images are touched.

## Steps (`scripts/04_pairs_splits.py`)
1. Build one row per **patient + breast side** with one CC path and one MLO path (Master doc §5.3).
   If several images exist per view, pick a fixed rule (e.g. first by SOP UID) and log how many had duplicates.
   Count and log breasts excluded for a missing view.
2. Attach labels: benign/malignant, subtype, age, lesion type (abnormality), TOMPEI mask path (MLO, may be empty).
3. Stage 1 split: patient-wise, stratified by benign/malignant, 70/15/15, seed 42 → `data/splits/stage1.csv`.
4. Stage 2 split: only the Stage 2 set from task 03, patient-wise, stratified by subtype, 70/15/15, seed 42
   → `data/splits/stage2.csv`. Same split for E1–E6.
5. E0 split: image-wise 72/18/10 on the Stage 2 set, to copy the baseline paper → `data/splits/stage2_e0_imagewise.csv`.
6. Sanity checks (assert, not just print): no patient appears in two splits (except E0 by design); class ratios
   per split within a few % of overall; every path exists.
7. Write `reports/04_data_flow.md`: the exclusion flow (all images → paired breasts → Stage 1 set → Stage 2 set),
   like Figure 2 of the baseline paper. This becomes a figure in the report/PPT.

## Done when
- The three split CSVs exist and pass the asserts; PROGRESS.md has the counts.
