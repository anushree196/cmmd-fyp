# START HERE — bringing the CMMD plan to life

This folder is a ready-made project for Claude Code. Copy it to your laptop and Claude Code will work
through it step by step, the same way each time, writing everything it does into `PROGRESS.md`.

---

## 1. Your questions, answered

**Can my laptop survive this?** Yes, for everything except training. The 21 GB looks scary, but only one step
reads it: converting the DICOMs into small PNGs. That runs once, on the CPU, image by image, so it never needs
21 GB of memory. Expect 20 to 60 minutes. Disk is fine too: you have 72.8 GB free, and the new files need about
1.5 to 3 GB (plus about 3 GB for Python packages).

**Do I need the cloud?** Only for training the deep learning models, which needs a GPU. Use **Kaggle**
(free, about 30 GPU hours a week, and it keeps running when you close the browser). Google Colab is the backup.

**Do I upload the 21 GB to the cloud?** No. You convert on the laptop and upload only the PNGs, masks and
tables (about 2 to 3 GB) as a private Kaggle Dataset, once. The DICOMs stay in Downloads, untouched.

**Should I start in Claude Code with all this data?** Yes, but Claude Code never "reads" the images. It
writes small Python scripts, runs them, and reads only the short summaries they print. `CLAUDE.md` makes
that a rule.

**What about MONAI?** You still use it, on Kaggle, for loading, caching and augmenting the images during
training (the `CacheDataset` from your master doc). The one change from your master doc is that the DICOM
reading happens once, on the laptop, instead of in every training run. That's what makes the cloud upload
small. The crop, flip and scale of every image are saved, so the TOMPEI lesion outlines still land exactly
on the right pixels.

## 2. Where each step runs

| # | Step | Where | What you need |
|---|---|---|---|
| 00 | Set up Python, Git, config | Laptop | Python 3.11, Git, a private GitHub repo |
| 01 | Inventory: one table of all 5,203 images + labels | Laptop (CPU, minutes) | the clinical .xlsx |
| 02 | DICOM → PNG, cropped and flipped, with a picture to check | Laptop (CPU, 20–60 min) | laptop plugged in, sleep off |
| 03 | TOMPEI-CMMD lesion masks + **Stage 2 patient count** | Laptop | download TOMPEI-CMMD |
| 04 | CC/MLO pairing + patient-wise splits | Laptop (seconds) | — |
| 05 | Upload the prepared data to Kaggle | Laptop → Kaggle | Kaggle account, phone verified, API token |
| 06 | Stage 1 training (benign vs malignant) | Kaggle GPU | — |
| 07 | Radiomics on the real masks | Kaggle (CPU) | — |
| 08 | Stage 2 ablation E0–E6 | Kaggle GPU | — |
| 09 | Grad-CAM + SHAP | Kaggle GPU | — |
| 10 | Semester 2: calibration, biopsies avoided, uncertainty, app | Kaggle + Hugging Face | — |

Steps 00 to 05 are all laptop work, and they're the right first stretch. By the end of 04 you'll have the real
numbers (how many patients, how many usable for Stage 2) for your report and slides.

## 3. What to do today

1. Copy this whole `cmmd-kit` folder to `C:\Users\Anushree\cmmd-fyp` (not inside Downloads or OneDrive,
   because OneDrive syncing thousands of PNGs will slow everything down).
2. Make sure Python 3.11 and Git are installed.
3. Open a terminal in `C:\Users\Anushree\cmmd-fyp`, run `claude`, and paste this:

   > Read CLAUDE.md, START_HERE.md and docs/master_plan_summary.md. Then do tasks/00_setup.md. Stop after
   > each task, show me the summary and the PROGRESS.md entry, and wait for my "go" before the next task.

4. When it asks you to do something marked **[ANU]** (install, download, look at a picture), do it and tell it.

Each later session, start with: *"Read CLAUDE.md and PROGRESS.md, then continue with the next task."*

## 4. Things you'll have to do yourself (Claude Code can't)

- Download `CMMD_clinicaldata_revision.xlsx` if it isn't in your `metadata` folder (CMMD page on TCIA).
- Download **TOMPEI-CMMD** from TCIA (task 03). It's a separate, much smaller download.
- Create the GitHub repo, the Kaggle account (verify your phone for GPU), and the Kaggle API token.
- Look at the check images (`reports/02_qc_montage.png`, `reports/03_mask_overlay.png`). Your eyes are the
  quality check.
- Press "Run" on Kaggle notebooks.

## 5. Golden rules

- Never edit, move or delete anything in the CMMD download folder.
- Split by **patient**, never by image (except E0, which copies the paper on purpose).
- Every number in your report comes from a script output logged in `PROGRESS.md`.
- Commit code to GitHub after each task. Data and weights never go into git.

The first three scripts (`00_check_env.py`, `01_inventory.py`, `02_convert.py`) are already written and were
tested on fake CMMD-shaped DICOMs. Claude Code writes the rest as it reaches each task.
