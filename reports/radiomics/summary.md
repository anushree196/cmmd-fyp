# Task 07 — radiomics summary

Stage 2 breasts: 671 (train 469) | features extracted: 67 | box-only (no shape features): 14

Pixel size before resampling: 0.151-0.211 mm; all resampled to 0.211 mm.

Lesion size (traced outlines only, mm²): {'min': 13.8, '25%': 239.3, '50%': 422.6, '75%': 879.2, 'max': 8340.8}

Decisions on the training split: {'dropped': 34, 'SELECTED': 20, 'not in the top k': 13}

| rank | feature | mutual information with subtype (train) |
|---|---|---|
| 1 | glcm_Contrast | 0.0801 |
| 2 | glrlm_GrayLevelNonUniformity | 0.0606 |
| 3 | shape2D_PerimeterSurfaceRatio | 0.0568 |
| 4 | glcm_InverseVariance | 0.0477 |
| 5 | glrlm_LowGrayLevelRunEmphasis | 0.0392 |
| 6 | glcm_Imc1 | 0.0373 |
| 7 | firstorder_90Percentile | 0.0336 |
| 8 | firstorder_Uniformity | 0.0301 |
| 9 | firstorder_Energy | 0.0271 |
| 10 | shape2D_MajorAxisLength | 0.0253 |
| 11 | glrlm_RunEntropy | 0.0252 |
| 12 | shape2D_Perimeter | 0.0247 |
| 13 | glcm_Idmn | 0.0239 |
| 14 | glcm_ClusterShade | 0.0215 |
| 15 | firstorder_10Percentile | 0.0161 |
| 16 | firstorder_Skewness | 0.0089 |
| 17 | shape2D_Elongation | 0.0069 |
| 18 | firstorder_Median | 0.0055 |
| 19 | firstorder_Minimum | 0.0040 |
| 20 | shape2D_Sphericity | 0.0000 |
