# CLAUDE.md — CMMD project (read this first, every session)

You are helping Anu build their final year project:
**"Advanced Multimodal Deep Learning Framework for Integrated Breast Cancer Diagnosis & Grading"**
on the CMMD mammography dataset. Anu works solo with you. They must be able to explain every line in the viva,
so explain what you do in plain words as you go, and keep code simple and commented.

## The project in one paragraph
Stage 1: benign vs malignant from both mammogram views (CC + MLO) plus age.
Stage 2 (malignant cases only): molecular subtype (Luminal A / Luminal B / HER2 / Triple-negative), adding the
MLO lesion crop from TOMPEI-CMMD masks, radiomics from the real lesion mask, and gated fusion.
Ablation E0–E6 is defined in `docs/master_plan_summary.md`.
Semester 2 adds calibration + uncertainty, a "benign biopsies avoided" result, and a Streamlit app.

## How we work
- Work through `tasks/` in number order. Before starting, read `PROGRESS.md` to see where we stopped.
- Do ONE task file at a time. At the end of each task: run its "Done when" checks, then append a dated entry
  to `PROGRESS.md` (what was done, numbers produced, problems, next step). Never skip the log.
- If a task says **[ANU]**, stop and ask Anu to do it (downloads, accounts, uploading to Kaggle, decisions).
- If a real fact (a column name, a DICOM tag, a count) differs from what a task file assumes, trust the data,
  write the difference into `PROGRESS.md` under "Surprises", and adapt. Never invent numbers.

## Paths
All paths come from `config.yaml` (copy `config.example.yaml`). Never hard-code `C:\Users\...` in scripts.
- `raw_root`: the CMMD download (read-only, ~21 GB, 5,203 DICOMs). **Never modify, move, or delete anything here.**
- `work_root`: where all generated data goes (`data/` inside this repo by default; it is git-ignored).

## Hard rules (this dataset is big; your context is not)
1. **Never print, cat, or Read a DICOM, PNG, or large CSV into the conversation.** Write a script, run it, and have it
   print a short summary (counts, `df.head()`, value_counts). Large outputs go to files under `data/` or `reports/`.
2. Read DICOM headers with `pydicom.dcmread(path, stop_before_pixels=True)` when you only need tags.
3. Every long-running script must: use `tqdm`, be **resumable** (skip outputs that already exist), and write a log/CSV.
4. Use `multiprocessing` with `cfg.num_workers` for per-image work. Test on 20 files (`--limit 20`) before the full run.
5. Splits are **patient-wise** (all images of a patient in one split). Never split by image. Fixed seed 42.
6. Keep git clean: data, PNGs, model weights, zips and `.venv` are never committed (see `.gitignore`).
7. Training does NOT happen on this laptop. Local = data prep, checks, small debugging. GPU training = Kaggle
   notebooks (see `tasks/06_*`). Write training code so it runs unchanged on Kaggle (paths from config / CLI args).
8. Windows: use `pathlib`, no shell-specific tricks; scripts are run as `python scripts/xx.py --config config.yaml`.

## Layout
```
scripts/      numbered scripts, one per step (01_inventory.py, 02_convert.py, ...)
src/          reusable code (datasets, models, metrics) imported by scripts and notebooks
notebooks/    Kaggle notebooks (training); they attach the private `cmmd-code` dataset and import src/ from it
tasks/        the step-by-step plan you follow
docs/         plan summary, decisions
reports/      small outputs worth keeping (tables, QC montages, figures) — committed
data/         generated data (git-ignored)
PROGRESS.md   running log — update after every task
```
