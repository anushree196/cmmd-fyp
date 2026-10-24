# Key findings (for the synopsis)

1. Benign vs malignant (Stage 1): our final model reaches a test AUC of 0.79 (0.73–0.84) on 279 breasts, judged honestly on unseen patients.
2. At a threshold set to catch 90% of cancers it finds 94% of test cancers but clears only 26% of benign breasts. Dense breasts score 0.79 against 0.84 for non-dense; cancers no radiologist could locate ('Invisible') are hardest at 0.68.
3. The improved Stage 1 recipe beat the first model by +0.020 AUC, but the difference is within noise (95% CI -0.023 to +0.061).
4. The baseline paper's code is public. It sets the 'tumour type' input to 'none' for every benign image, so the model is told which images are benign.
5. Re-running their exact protocol we get 0.86 micro AUC, close to their published 0.89; their 88.87% is a micro average, which an easy class inflates.
6. That leaked input alone, with no mammogram at all, scores 0.90 micro AUC and a perfect 1.00 for benign.
7. Giving benign breasts their real lesion type drops the same model to 0.69 micro AUC; with a patient-wise split as well (E0-clean) it is 0.70 micro / 0.60 macro.
8. The paper also labelled both breasts of a patient with the tumour's subtype (1,458 images of breasts with no labelled cancer); with correct per-breast labels the leaky model scores 0.92, not lower, so the metadata leak, not the labelling, drives the headline.
9. Predicting the molecular subtype from the image is genuinely hard: on 101 test patients our best models reach a macro AUC of 0.64 (E5, gated fusion) and 0.59 (E6), and no added component is shown to help beyond noise; the leaky baseline scores 0.52 on the same 4-subtype task.
10. Chaining the two stages gives an honest 5-class result of 0.77 micro / 0.72 macro AUC — lower than the paper's headline, but free of the label leak, the image-wise split and the per-patient labelling.

Every number above is taken by `scripts/08b_synopsis.py` from the files listed under tables T2–T5.
