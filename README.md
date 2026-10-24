# Multimodal deep learning for breast cancer diagnosis and molecular subtyping (CMMD)

Final year project. Two stages on the Chinese Mammography Database (CMMD) with TOMPEI-CMMD lesion outlines:

1. **Stage 1 — benign vs malignant**, per breast, from both views (CC + MLO) and age.
2. **Stage 2 — molecular subtype** (Luminal A / Luminal B / HER2-enriched / triple negative) of malignant
   breasts, adding the MLO lesion crop, radiomics from the real lesion outline and gated fusion.

An ablation (E0–E6) compares this with the baseline paper, re-run under its own protocol and under a fair one.

## Baseline

Ben Rabah C., Sattar A., Ibrahim A., Serag A. *A Multimodal Deep Learning Model for the Classification of Breast
Cancer Subtypes.* Diagnostics 2025, 15, 995. doi:10.3390/diagnostics15080995

Its code: https://github.com/serag-ai/Multimodal-BC-Classifier — public when checked on **2026-10-24**
(notebooks uploaded 2026-04-13). We read it to reproduce the method (E0); **none of its code is copied** into this
repository (it carries no licence). Our re-implementation is `src/e0.py`. What the code review found is in
`reports/08_e0_eligibility.md` and `reports/ablation_table.md`.

## Layout

```
scripts/   numbered steps, run in order: 01 inventory, 02 DICOM -> PNG, 03 TOMPEI labels + masks,
           04 pairs + splits, 05 audit / Kaggle packaging, 06 Stage 1 comparison, 07 radiomics, 08 ablation
src/       shared code: data, models, training, metrics, radiomics, E0 and Stage 2 experiments
notebooks/ Kaggle notebooks (each a .py source + the generated .ipynb); they import src/ from a private dataset
tasks/     the step-by-step plan          docs/     plan, decisions, master document, baseline notes
reports/   small results kept in git      PROGRESS.md  dated log of every step and number
```

Data (CMMD DICOMs, generated PNGs, masks, model weights) is never committed. Paths come from `config.yaml`
(copy `config.example.yaml`). Training runs on Kaggle GPUs; data preparation runs locally (`requirements-local.txt`).
