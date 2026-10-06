# Task 10 — Semester 2: trust layer and app  (do not start before semester 1 results exist)

1. Calibration: temperature scaling fitted on the validation predictions; report ECE and reliability diagrams
   before/after, for Stage 1 and Stage 2.
2. Benign biopsies avoided (Stage 1): on test predictions, pick the threshold giving ~98% sensitivity on the
   validation set; report what fraction of benign cases fall below it (= biopsies that could be avoided) with a
   bootstrap CI. Every CMMD case was biopsied, so this is measured on real outcomes.
3. Uncertainty for Stage 2: MC-dropout or a 3–5 model ensemble; an "unsure → wait for IHC" option. Report
   accuracy vs coverage (how accurate the confident cases are, and what share is flagged).
4. Streamlit app (upload CC + MLO + age → Stage 1 result with calibrated confidence, Grad-CAM, and Stage 2 hint or
   "unsure") deployed on Hugging Face Spaces (Master doc §6).
