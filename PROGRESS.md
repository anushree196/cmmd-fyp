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
