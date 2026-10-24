# Task 07 — radiomics summary

Stage 2 breasts: 671 (train 469) | features extracted: 67 | box-only (no shape features): 14

Pixel size before resampling: 0.151-0.211 mm; all resampled to 0.211 mm.

Lesion size (traced outlines only, mm²): {'min': 13.8, '25%': 239.3, '50%': 422.6, '75%': 879.2, 'max': 8340.8}

Decisions on the training split: {'dropped': 38, 'SELECTED': 20, 'not in the top k': 9}

| rank | feature | mutual information with subtype (train) |
|---|---|---|
| 1 | glrlm_RunEntropy | 0.0702 |
| 2 | glrlm_RunVariance | 0.0642 |
| 3 | glrlm_LongRunLowGrayLevelEmphasis | 0.0609 |
| 4 | shape2D_PerimeterSurfaceRatio | 0.0568 |
| 5 | firstorder_Range | 0.0460 |
| 6 | glrlm_GrayLevelNonUniformity | 0.0396 |
| 7 | glrlm_ShortRunHighGrayLevelEmphasis | 0.0350 |
| 8 | firstorder_RootMeanSquared | 0.0265 |
| 9 | shape2D_MajorAxisLength | 0.0253 |
| 10 | shape2D_Perimeter | 0.0247 |
| 11 | glcm_DifferenceEntropy | 0.0233 |
| 12 | shape2D_MinorAxisLength | 0.0229 |
| 13 | glcm_Idmn | 0.0222 |
| 14 | firstorder_Minimum | 0.0215 |
| 15 | glcm_InverseVariance | 0.0180 |
| 16 | glrlm_ShortRunLowGrayLevelEmphasis | 0.0152 |
| 17 | glrlm_LongRunHighGrayLevelEmphasis | 0.0141 |
| 18 | firstorder_Entropy | 0.0098 |
| 19 | firstorder_Skewness | 0.0089 |
| 20 | glcm_JointEnergy | 0.0087 |
