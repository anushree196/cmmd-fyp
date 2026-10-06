# Task 09 — Explainability  (runs on: Kaggle GPU, short)

1. Grad-CAM on Stage 1 and Stage 2 image branches for ~20 test cases (mix of correct / wrong).
2. For Stage 2 MLO cases: measure overlap between the Grad-CAM hot area and the TOMPEI mask
   (e.g. fraction of top-10% heat inside the mask). This is our substitute for a radiologist checking the heatmaps.
3. SHAP on the radiomics + clinical branch: which features push towards LumA vs LumB.
4. LumA vs LumB side-by-side figure. Save all figures to `reports/figures/`.
