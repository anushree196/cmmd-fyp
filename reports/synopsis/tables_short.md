# Synopsis-width tables (shortened T2 and T3; same numbers as tables.md)

## T2 (short): Stage 1 test results, 279 breasts / 265 patients

| measure                                                 | Stage 1 v2 (final)                       |
|:--------------------------------------------------------|:-----------------------------------------|
| Test AUC (95% CI)                                       | 0.787 (0.73–0.84)                        |
| v1 test AUC                                             | 0.767                                    |
| Model                                                   | ensemble of 5 CV fold models (recipe R3) |
| Thresholds chosen on                                    | out-of-fold predictions (1,577 breasts)  |
| Youden: threshold                                       | 0.611                                    |
| Youden: sensitivity (95% CI)                            | 0.609 (0.54–0.68)                        |
| Youden: specificity (95% CI)                            | 0.768 (0.68–0.86)                        |
| ≥90% sensitivity: threshold                             | 0.169                                    |
| ≥90% sensitivity: sensitivity (95% CI)                  | 0.944 (0.91–0.97)                        |
| ≥90% sensitivity: specificity (95% CI)                  | 0.256 (0.15–0.36)                        |
| Subgroup AUC: dense breasts (n=234)                     | 0.790 (0.73–0.85)                        |
| Subgroup AUC: non-dense breasts (n=45)                  | 0.841 (0.70–0.95)                        |
| Subgroup AUC: 'Invisible' cancers vs all benign (n=102) | 0.679 (0.56–0.79)                        |
| Subgroup AUC: visible cancers vs all benign (n=259)     | 0.799 (0.74–0.85)                        |
| Paired difference v2 − v1 in test AUC (95% CI)          | +0.020 (-0.023 to +0.061)                |

Sources: `reports/stage1_v2/metrics_test.json`; `reports/stage1/metrics_test.json` (v1 AUC); `reports/stage1_v2/compare_v1_v2_test.json`

## T3 (short): the leak ladder (5 classes, test, average of 3 seeds)

| run               | micro AUC         | macro AUC         |   Benign AUC |
|:------------------|:------------------|:------------------|-------------:|
| Paper (published) | 0.889             | ≈0.794            |        1     |
| E0-paperdata      | 0.859 (0.83–0.88) | 0.770 (0.74–0.80) |        1     |
| E0                | 0.920 (0.90–0.94) | 0.850 (0.82–0.88) |        1     |
| E0-meta           | 0.902 (0.88–0.93) | 0.850 (0.82–0.88) |        1     |
| E0-truemeta       | 0.685 (0.64–0.73) | 0.632 (0.58–0.68) |        0.738 |
| E0-patient        | 0.904 (0.87–0.93) | 0.810 (0.77–0.85) |        1     |
| E0-clean          | 0.704 (0.66–0.74) | 0.602 (0.55–0.65) |        0.681 |

Sources: `docs/baseline_paper_notes.md` (paper); `reports/stage2/test/metrics_test.json`; `reports/stage2/test_e0clean/metrics_test.json`
