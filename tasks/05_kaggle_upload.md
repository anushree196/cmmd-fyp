# Task 05 — Send the prepared data to Kaggle  (runs on: laptop → Kaggle)

Goal: a private Kaggle Dataset holding `png1024/`, `masks1024/`, `index/`, `splits/` (~2–3 GB, not 21 GB).

## Steps
1. **[ANU]** Kaggle account → Settings → **verify phone number** (needed for free GPU) → "Create New API Token"
   → save `kaggle.json` to `C:\Users\Anushree\.kaggle\kaggle.json`. Never commit it.
2. `python scripts/05_package.py --config config.yaml` builds `data/kaggle_upload/` with exactly those 4 folders and a
   `dataset-metadata.json` (title "cmmd-png1024", private).
3. `kaggle datasets create -p data/kaggle_upload --dir-mode zip` (first time) or
   `kaggle datasets version -p data/kaggle_upload --dir-mode zip -m "message"` (updates).
   Upload of ~2–3 GB takes a while on home Wi-Fi; it is a one-time cost.
4. **[ANU]** On kaggle.com, open the dataset and check the file count matches `png_index.csv`.
5. Delete `data/kaggle_upload/` afterwards if disk is tight (the source folders stay).

## Done when
- The Kaggle dataset exists, is private, and a Kaggle notebook can list its `png1024` folder
  (measured mount path: `/kaggle/input/datasets/honeyyy09/cmmd-png1024/png1024`).

Backup option: if Kaggle is unavailable, zip the same folders, upload to Google Drive, and use Colab
(mount Drive, unzip to `/content` local disk before training — never train reading from Drive directly).
