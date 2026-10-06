# Task 00 — Set up the laptop project  (runs on: laptop)

Goal: a working Python environment and a git repo, without touching the raw data.

## Steps
1. **[ANU]** Install Python 3.11 from python.org (tick "Add to PATH") and Git for Windows, if not already installed.
   Check: `python --version` shows 3.11.x, `git --version` works.
2. In this folder: `python -m venv .venv`, then `.venv\Scripts\activate`, then
   `pip install -r requirements-local.txt`. (CPU only. Do NOT install CUDA/GPU PyTorch on the laptop.)
3. Copy `config.example.yaml` to `config.yaml`. Fix the paths if they differ (check with `dir`).
   Set `num_workers` to (number of CPU cores − 2): find cores with
   `python -c "import os; print(os.cpu_count())"`.
4. `git init`, first commit. **[ANU]** Create an empty **private** GitHub repo (e.g. `cmmd-fyp`) and push.
   Kaggle notebooks will clone it later.
5. Check free disk space on C: (`python scripts/00_check_env.py --config config.yaml` prints it). Need ≥ 15 GB free.

## Done when
- `python scripts/00_check_env.py --config config.yaml` prints OK for: Python version, packages, raw_root exists,
  number of .dcm files found (expect ~5,203), clinical xlsx found (or a clear "missing" message), free disk.
- PROGRESS.md has a Task 00 entry with those numbers.

If the clinical xlsx is missing: **[ANU]** download `CMMD_clinicaldata_revision.xlsx` from the CMMD page on
cancerimagingarchive.net (Data Access table) and put its path in config.yaml.
