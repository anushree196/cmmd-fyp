# Task 08 — Stage 2 ablation E0–E6  (runs on: Kaggle GPU)

Goal: the ablation table, every experiment on the SAME fixed Stage 2 patient set (Master doc §3.4).

## Steps
1. E0: Xception (timm), single view, age + lesion type, concatenation, **image-wise split** file, 224 px,
   10 epochs, batch 64 (or the largest that fits; note any difference). Compare to the paper's
   LumA 67% / LumB 74% / overall 88.87% (published, full dataset) — report as "E0 re-run on fair subset".
2. E1 → E6 one at a time, each adding exactly one component (see `docs/master_plan_summary.md`).
   Same split, same seed, same epochs budget, same img size. Only the component changes.
3. Run each experiment with 3 seeds if GPU budget allows; report mean ± std. If not, 1 seed + bootstrap CI.
4. Per experiment save `metrics.json` (macro AUC, per-class AUC, especially LumA and LumB) + predictions CSV.
5. `scripts/08_ablation_table.py` collects all metrics into `reports/ablation_table.md`.
6. Chained Stage 1 → Stage 2 5-class AUC (Master doc §7.1) for the best model.

## Done when
- `reports/ablation_table.md` complete, with honest notes on anything that could not be matched.
