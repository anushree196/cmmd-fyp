# Synopsis tables (task 08b)

All numbers are copied by `scripts/08b_synopsis.py` from saved files (listed under each table); nothing is retyped.
Baseline code: https://github.com/serag-ai/Multimodal-BC-Classifier (public; checked 2026-10-24; read for the method, no code copied).

## T1: Dataset by split and class

| set                              | split   | class     |   patients |   breasts |   images |
|:---------------------------------|:--------|:----------|-----------:|----------:|---------:|
| Stage 1 (benign vs malignant)    | train   | benign    |        341 |       385 |      770 |
| Stage 1 (benign vs malignant)    | train   | malignant |        911 |       914 |     1828 |
| Stage 1 (benign vs malignant)    | train   | all       |       1233 |      1299 |     2598 |
| Stage 2 (subtype; E1–E6)         | train   | LumA      |         98 |        98 |      196 |
| Stage 2 (subtype; E1–E6)         | train   | LumB      |        234 |       234 |      468 |
| Stage 2 (subtype; E1–E6)         | train   | HER2      |         88 |        88 |      176 |
| Stage 2 (subtype; E1–E6)         | train   | TN        |         49 |        49 |       98 |
| Stage 2 (subtype; E1–E6)         | train   | all       |        469 |       469 |      938 |
| Stage 1 (benign vs malignant)    | val     | benign    |         74 |        82 |      164 |
| Stage 1 (benign vs malignant)    | val     | malignant |        196 |       196 |      392 |
| Stage 1 (benign vs malignant)    | val     | all       |        264 |       278 |      556 |
| Stage 2 (subtype; E1–E6)         | val     | LumA      |         21 |        21 |       42 |
| Stage 2 (subtype; E1–E6)         | val     | LumB      |         50 |        50 |      100 |
| Stage 2 (subtype; E1–E6)         | val     | HER2      |         19 |        19 |       38 |
| Stage 2 (subtype; E1–E6)         | val     | TN        |         11 |        11 |       22 |
| Stage 2 (subtype; E1–E6)         | val     | all       |        101 |       101 |      202 |
| Stage 1 (benign vs malignant)    | test    | benign    |         74 |        82 |      164 |
| Stage 1 (benign vs malignant)    | test    | malignant |        196 |       197 |      394 |
| Stage 1 (benign vs malignant)    | test    | all       |        265 |       279 |      558 |
| Stage 2 (subtype; E1–E6)         | test    | LumA      |         21 |        21 |       42 |
| Stage 2 (subtype; E1–E6)         | test    | LumB      |         51 |        51 |      102 |
| Stage 2 (subtype; E1–E6)         | test    | HER2      |         19 |        19 |       38 |
| Stage 2 (subtype; E1–E6)         | test    | TN        |         10 |        10 |       20 |
| Stage 2 (subtype; E1–E6)         | test    | all       |        101 |       101 |      202 |
| Stage 1 (benign vs malignant)    | total   | benign    |        489 |       549 |     1098 |
| Stage 1 (benign vs malignant)    | total   | malignant |       1303 |      1307 |     2614 |
| Stage 1 (benign vs malignant)    | total   | all       |       1762 |      1856 |     3712 |
| Stage 2 (subtype; E1–E6)         | total   | LumA      |        140 |       140 |      280 |
| Stage 2 (subtype; E1–E6)         | total   | LumB      |        335 |       335 |      670 |
| Stage 2 (subtype; E1–E6)         | total   | HER2      |        126 |       126 |      252 |
| Stage 2 (subtype; E1–E6)         | total   | TN        |         70 |        70 |      140 |
| Stage 2 (subtype; E1–E6)         | total   | all       |        671 |       671 |     1342 |
| E0 (5 classes, image-wise split) | train   | Benign    |        452 |       501 |      790 |
| E0 (5 classes, image-wise split) | train   | LumA      |        135 |       135 |      216 |
| E0 (5 classes, image-wise split) | train   | LumB      |        354 |       354 |      540 |
| E0 (5 classes, image-wise split) | train   | HER2      |        129 |       129 |      194 |
| E0 (5 classes, image-wise split) | train   | TN        |         81 |        81 |      124 |
| E0 (5 classes, image-wise split) | train   | all       |       1141 |      1200 |     1864 |
| E0 (5 classes, image-wise split) | val     | Benign    |        176 |       179 |      197 |
| E0 (5 classes, image-wise split) | val     | LumA      |         47 |        47 |       54 |
| E0 (5 classes, image-wise split) | val     | LumB      |        130 |       130 |      135 |
| E0 (5 classes, image-wise split) | val     | HER2      |         45 |        45 |       49 |
| E0 (5 classes, image-wise split) | val     | TN        |         30 |        30 |       31 |
| E0 (5 classes, image-wise split) | val     | all       |        425 |       431 |      466 |
| E0 (5 classes, image-wise split) | test    | Benign    |        104 |       106 |      111 |
| E0 (5 classes, image-wise split) | test    | LumA      |         26 |        26 |       30 |
| E0 (5 classes, image-wise split) | test    | LumB      |         72 |        72 |       75 |
| E0 (5 classes, image-wise split) | test    | HER2      |         26 |        26 |       27 |
| E0 (5 classes, image-wise split) | test    | TN        |         17 |        17 |       17 |
| E0 (5 classes, image-wise split) | test    | all       |        245 |       247 |      260 |
| E0 (5 classes, image-wise split) | total   | Benign    |        489 |       549 |     1098 |
| E0 (5 classes, image-wise split) | total   | LumA      |        150 |       150 |      300 |
| E0 (5 classes, image-wise split) | total   | LumB      |        375 |       375 |      750 |
| E0 (5 classes, image-wise split) | total   | HER2      |        135 |       135 |      270 |
| E0 (5 classes, image-wise split) | total   | TN        |         86 |        86 |      172 |
| E0 (5 classes, image-wise split) | total   | all       |       1223 |      1295 |     2590 |

Stage 1 and Stage 2 use one patient-wise split (a patient's breasts are always in the same part). In the E0 image-wise split one patient's images can sit in different parts, so its patient counts add up to more than the total.

Sources: `data/splits/stage1.csv`; `data/splits/stage2.csv`; `reports/stage2/e0_rows.csv`; `cross-check: reports/04_data_flow.md`

## T2: Stage 1 (benign vs malignant) test results, 279 breasts / 265 patients

| measure                                                 | v1                       | v2 (final)                               |
|:--------------------------------------------------------|:-------------------------|:-----------------------------------------|
| Test AUC (95% CI)                                       | 0.767 (0.71–0.82)        | 0.787 (0.73–0.84)                        |
| Model                                                   | single model (epoch 7)   | ensemble of 5 CV fold models (recipe R3) |
| Thresholds chosen on                                    | validation (278 breasts) | out-of-fold predictions (1,577 breasts)  |
| Youden: threshold                                       | 0.782                    | 0.611                                    |
| Youden: sensitivity (95% CI)                            | 0.543 (0.48–0.61)        | 0.609 (0.54–0.68)                        |
| Youden: specificity (95% CI)                            | 0.841 (0.76–0.92)        | 0.768 (0.68–0.86)                        |
| ≥90% sensitivity: threshold                             | 0.171                    | 0.169                                    |
| ≥90% sensitivity: sensitivity (95% CI)                  | 0.843 (0.79–0.89)        | 0.944 (0.91–0.97)                        |
| ≥90% sensitivity: specificity (95% CI)                  | 0.439 (0.33–0.55)        | 0.256 (0.15–0.36)                        |
| Subgroup AUC: dense breasts (n=234)                     | 0.756 (0.69–0.82)        | 0.790 (0.73–0.85)                        |
| Subgroup AUC: non-dense breasts (n=45)                  | 0.873 (0.73–0.97)        | 0.841 (0.70–0.95)                        |
| Subgroup AUC: 'Invisible' cancers vs all benign (n=102) | 0.606 (0.47–0.74)        | 0.679 (0.56–0.79)                        |
| Subgroup AUC: visible cancers vs all benign (n=259)     | 0.785 (0.73–0.84)        | 0.799 (0.74–0.85)                        |
| Paired difference v2 − v1 in test AUC (95% CI)          |                          | +0.020 (-0.023 to +0.061)                |

The test split was scored twice in total (v1, then v2 with the frozen recipe); the reason is logged in PROGRESS.md (task 06 v2).

Sources: `reports/stage1/metrics_test.json`; `reports/stage1_v2/metrics_test.json`; `reports/stage1_v2/compare_v1_v2_test.json`

## T3: The leak ladder (E0 family, 5 classes, test, average of 3 seeds)

| run               | what                                                                                     | test images   | micro AUC         | macro AUC         |   Benign |    LumA |    LumB |    HER2 |      TN |     ACC |   precision |   recall |      F1 |
|:------------------|:-----------------------------------------------------------------------------------------|:--------------|:------------------|:------------------|---------:|--------:|--------:|--------:|--------:|--------:|------------:|---------:|--------:|
| Paper (published) | their protocol, their data                                                               | 406           | 0.889             | ≈0.794            |    1     |   0.67  |   0.74  |   0.78  |   0.78  |   0.638 |       0.46  |    0.64  |   0.52  |
| E0-paperdata      | their full protocol: per-patient labels (4,040 images), leaky metadata, image-wise split | 405           | 0.859 (0.83–0.88) | 0.770 (0.74–0.80) |    1     |   0.714 |   0.755 |   0.735 |   0.646 |   0.548 |       0.452 |    0.456 |   0.452 |
| E0                | our per-breast labels (2,590 images); their leaky metadata and image-wise split          | 260           | 0.920 (0.90–0.94) | 0.850 (0.82–0.88) |    1     |   0.821 |   0.826 |   0.83  |   0.773 |   0.638 |       0.47  |    0.481 |   0.469 |
| E0-meta           | E0's metadata only, no image                                                             | 260           | 0.902 (0.88–0.93) | 0.850 (0.82–0.88) |    1     |   0.78  |   0.84  |   0.842 |   0.79  |   0.577 |       0.341 |    0.485 |   0.382 |
| E0-truemeta       | E0 with real lesion types for benign (leak removed)                                      | 260           | 0.685 (0.64–0.73) | 0.632 (0.58–0.68) |    0.738 |   0.618 |   0.514 |   0.713 |   0.577 |   0.365 |       0.275 |    0.281 |   0.27  |
| E0-patient        | E0 on our patient-wise split (leak kept)                                                 | 388           | 0.904 (0.87–0.93) | 0.810 (0.77–0.85) |    1     |   0.728 |   0.795 |   0.807 |   0.721 |   0.621 |       0.426 |    0.426 |   0.423 |
| E0-clean          | real lesion types AND patient-wise split (both fixes) — NOT RUN                          | –             | nan               | nan               |  nan     | nan     | nan     | nan     | nan     | nan     |     nan     |  nan     | nan     |

Precision, recall and F1 are macro averages (our runs); the paper does not say which average it reports. The paper's macro AUC is our average of its five per-class AUCs. E0-paperdata, E0, E0-meta and E0-truemeta are tested on their own image-wise test parts; E0-patient and E0-clean on our patient-wise test patients (images).

Sources: `paper: docs/baseline_paper_notes.md`; `reports/stage2/test/metrics_test.json`; `E0-clean: reports/stage2/test_e0clean/metrics_test.json`

## T4: Stage 2 ablation, 4 subtypes, the same 101 test patients

| experiment                            | what changed                                                                     | val macro AUC (mean ± std)   | test macro AUC (95% CI)   |   test LumA |   test LumB |   test HER2 |   test TN |
|:--------------------------------------|:---------------------------------------------------------------------------------|:-----------------------------|:--------------------------|------------:|------------:|------------:|----------:|
| E0-patient (4 subtypes)               | E0 (Xception, 224 px, leaky metadata) on the patient split, scored on 4 subtypes | 0.563 ± 0.019 (n=3)          | 0.520 (0.44–0.61)         |       0.468 |       0.507 |       0.639 |     0.466 |
| E0-clean (4 subtypes)                 | E0-clean (both fixes), scored on 4 subtypes — NOT RUN                            | nan                          | nan                       |     nan     |     nan     |     nan     |   nan     |
| E1-224                                | EfficientNet-B3, MLO only, 224 px, age + lesion type                             | 0.586 ± 0.014 (n=3)          | 0.502 (0.41–0.60)         |       0.581 |       0.505 |       0.551 |     0.37  |
| E1                                    | image size 224 → 512 px                                                          | 0.611 ± 0.043 (n=3)          | 0.551 (0.47–0.64)         |       0.558 |       0.489 |       0.688 |     0.467 |
| E2                                    | + CC view with View Attention                                                    | 0.622 ± 0.013 (n=3)          | 0.586 (0.49–0.68)         |       0.545 |       0.541 |       0.635 |     0.625 |
| E3                                    | + MLO lesion crop (TOMPEI mask)                                                  | 0.586 ± 0.011 (n=3)          | 0.590 (0.51–0.67)         |       0.604 |       0.485 |       0.669 |     0.602 |
| E4                                    | + radiomics branch (20 features + box flag)                                      | 0.576 ± 0.017 (n=3)          | 0.618 (0.54–0.69)         |       0.615 |       0.507 |       0.687 |     0.663 |
| E5                                    | concatenation → Gated Fusion                                                     | 0.590 ± 0.002 (n=3)          | 0.644 (0.57–0.72)         |       0.624 |       0.509 |       0.693 |     0.751 |
| E6                                    | E5 trained as a 5-fold CV ensemble                                               | 0.643 ± 0.034 (n=5)          | 0.587 (0.51–0.66)         |       0.611 |       0.459 |       0.675 |     0.603 |
| Paper (5-class model, leaky protocol) | for reference only — not comparable                                              |                              |                           |       0.67  |       0.74  |       0.78  |     0.78  |

Test class sizes: LumA 21, LumB 51, HER2 19, TN 10 patients. Each row adds one change to the row above it (from E1-224 on).

Sources: `reports/stage2/test/metrics_test.json`; `reports/stage2/val/<experiment>/*/metrics_val.json`; `E0 rows: reports/stage2/test/test_E0-patient.csv, reports/stage2/test_e0clean/test_E0-clean.csv, reports/stage2/val/E0-*/seed*/val_predictions.csv (re-scored here: benign column dropped, subtypes renormalised, CC and MLO averaged per breast)`

## T5: Chained Stage 1 → Stage 2, one 5-class probability per breast

| model                                       | breasts    | micro AUC         | macro AUC         | Benign            | LumA              | LumB              | HER2              | TN                |
|:--------------------------------------------|:-----------|:------------------|:------------------|:------------------|:------------------|:------------------|:------------------|:------------------|
| Ours: Stage 1 v2 → E6, soft chaining (test) | 183        | 0.775 (0.72–0.82) | 0.724 (0.67–0.77) | 0.822 (0.76–0.88) | 0.707 (0.58–0.82) | 0.636 (0.55–0.72) | 0.799 (0.69–0.89) | 0.658 (0.53–0.79) |
| Paper (leaky protocol)                      | 406 images | 0.889             | ≈0.794            | 1.00              | 0.67              | 0.74              | 0.78              | 0.78              |

82 benign test breasts + 101 subtyped test patients; P(subtype) = p(malignant) × Stage 2 probability; benign breasts have no lesion mask, so 1/4 per subtype. Subtype AUCs here count benign breasts as negatives and are higher than T4's.

Sources: `reports/stage2/test/chained_5class_metrics.json`; `reports/ablation_table.md §3`

## T6: Our work compared with the baseline paper

| aspect              | paper (Ben Rabah et al. 2025)                                                            | ours                                                                                                                           |
|:--------------------|:-----------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------|
| Data                | CMMD, 4,056 images (we reproduce 4,040 by labelling per patient)                         | CMMD + TOMPEI-CMMD; Stage 1 3,712 images (1,856 breasts), Stage 2 671 patients, E0 2,590 images                                |
| Labels              | per patient: both breasts get the patient's subtype (1,458 images of unlabelled breasts) | per breast, CMMD rows with TOMPEI left/right corrections; 16 TOMPEI-excluded breasts dropped                                   |
| Split               | image-wise 72/18/10 (198 of 260 E0 test images have a sibling image in train)            | patient-wise 70/15/15, one assignment for both stages, stratified incl. TOMPEI class                                           |
| Metadata            | age ≥ 40, tumour class set from the image's folder: benign = 0 for every benign image    | age + real CMMD lesion type for every breast                                                                                   |
| Lesion localisation | none (whole image, 224 px)                                                               | TOMPEI outline → MLO lesion crop and radiomics at a common 0.211 mm pixel size                                                 |
| Benign class        | inside one 5-class model; AUC 1.00 (the metadata gives it away)                          | separate Stage 1 model: AUC 0.787 (0.728–0.843)                                                                                |
| Headline metric     | micro-average AUC (Keras AUC on one-hot labels), last of 10 epochs                       | macro and per-class AUC with patient bootstrap CIs; micro also reported                                                        |
| Result              | 0.889 micro AUC (5 classes)                                                              | E0-paperdata reproduces 0.859; leak removed 0.685; our chained 5-class 0.775 micro / 0.724 macro; subtype-only 0.55–0.64 macro |

Sources: `docs/baseline_paper_notes.md`; `https://github.com/serag-ai/Multimodal-BC-Classifier (checked 2026-10-24)`; `reports/08_e0_eligibility.md`; `reports/ablation_table.md`; `reports/stage1_v2/metrics_test.json`; `PROGRESS.md (tasks 03, 04, 07, 08)`

## Figure notes

- F4: Stage 2 (E5) training logs record training loss and validation AUC but NOT validation loss (`src/stage2.py` never logged it), so panel (c) shows training loss only. Stage 1 v2 logs are complete.
- F5: skipped — E0-clean test predictions are not available.
