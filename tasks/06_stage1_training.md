# Task 06 — Stage 1 training: benign vs malignant  (runs on: Kaggle GPU)

Goal: a working, honest Stage 1 model and the training code every later experiment reuses.

## Code to write (in `src/`, so laptop and Kaggle share it)
- `src/data.py`: MONAI dataset reading the pair table; loads CC + MLO PNGs, resizes to `img_size`,
  augmentation (small rotation, brightness/contrast, NO vertical flip; horizontal flip is already normalised),
  CacheDataset.
- `src/models.py`: EfficientNet-B3 (timm, ImageNet weights) shared by both views → View Attention
  (learned weights over the 2 view embeddings) → concat with clinical MLP (age, lesion type) → 2-class head.
- `src/train.py`: one entry point, CLI args (`--stage 1 --img-size 512 --epochs ... --exp-name ...`), mixed
  precision, AdamW + cosine schedule, early stopping on val AUC, saves best weights + `metrics.json`
  (AUC, sensitivity, specificity, confusion matrix) + **val/test predicted probabilities as CSV** (semester 2
  calibration needs these).
- `notebooks/train_kaggle.ipynb`: attach the two private datasets (no GitHub clone, no token),
  `pip install -r requirements-train.txt`, run `src/train.py`, save outputs to `/kaggle/working/`.

## Facts measured in task 05 (2026-10-07, `reports/05_kaggle_check.json`)
- Datasets mount at `/kaggle/input/datasets/honeyyy09/cmmd-png1024` (holding `png1024/`, `masks1024/`,
  `index/`, `splits/`, `manifest.json`) and `/kaggle/input/datasets/honeyyy09/cmmd-code` (holding `src/`,
  `requirements-train.txt`). NOT `/kaggle/input/cmmd-png1024`. Do not hard-code either: find the folder by
  searching `/kaggle/input` for `png1024`, as `notebooks/00_check` does.
- After changing anything in `src/`, re-upload the code dataset before running a notebook:
  `python scripts/05_package.py --config config.yaml`, then
  `kaggle datasets version -p data/kaggle_code --dir-mode zip -m "what changed"`.
- GPU works: 2 × Tesla T4, torch 2.11, Python 3.13. Already installed: timm, shap, SimpleITK, scikit-learn,
  OpenCV. **Not installed: monai, pyradiomics, grad-cam**, so the notebook needs Internet ON for `pip install`.
- Notebooks can be pushed and run from the laptop: `kaggle kernels push -p notebooks/<folder>`, then
  `kaggle kernels status` and `kaggle kernels output`.

## Steps
1. Test locally on CPU first: `python -m src.train --stage 1 --img-size 128 --epochs 1 --limit 32` must run end to end.
2. Push to GitHub. **[ANU]** On Kaggle: new notebook → add the dataset → Accelerator: GPU T4 x2 or P100 →
   Internet ON → run. Use "Save Version → Save & Run All" for long runs so it continues with the browser closed.
3. Download `metrics.json`, prediction CSVs and the training curve into `reports/stage1/` (small files only).
   Keep weights (.pth) as a Kaggle notebook output or a Kaggle model, not in git.

## Done when
- Test AUC reported with a 95% bootstrap confidence interval, confusion matrix saved, curves saved.
- PROGRESS.md entry with the numbers and GPU hours used.

Budget: Kaggle gives roughly 30 free GPU hours per week. A 512 px dual-view run should take ~1–2 h.
Check the current quota on your Kaggle profile.
