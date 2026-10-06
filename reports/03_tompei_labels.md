# Task 03 — TOMPEI-CMMD labels compared with CMMD

TOMPEI sheet: TOMPEI-CMMD_clinical_data_v01_20250121.xlsx
TOMPEI rows (breasts): 2601  |  patients: 1775

## 1. TOMPEI classes (per breast)

| class | breasts | meaning (from TOMPEI's README) |
|---|---|---|
| Malignant | 1167 | confirmed malignant lesion, located on the image |
| Normal | 1054 | normal, OR benign with no identifiable lesion on the image |
| Benign | 215 | only benign lesions, located on the image |
| Invisible | 140 | malignant, but the lesion cannot be located on the image |
| Exclusion | 25 | TOMPEI recommends excluding the breast (reason given) |

Exclusion reasons: {'CV port': 7, 'Phyllodes tumor': 6, 'Presence of white objects': 3, 'Neurofibromatosis': 2, 'Foreign object at the top': 1, 'Scale is incorrect': 1, 'Image noise': 1, 'Breast augmentation': 1, 'Lower part missing': 1, 'Unclear on image/Pacemaker?': 1, 'Lymphedema': 1}
Breasts with at least one outlined lesion: 1385  |  outlined lesions in total: 1773

## 2. Image sides

Images whose DICOM side tag disagrees with the pixels: 15
Images whose side was corrected: 16 (8 patients)

| patient | view | DICOM tag | corrected | why |
|---|---|---|---|---|
| D1-0252 | CC | R | L | TOMPEI: reversed left and right |
| D1-0252 | MLO | R | L | TOMPEI: reversed left and right |
| D1-0690 | CC | R | L | TOMPEI: reversed left and right |
| D1-0690 | MLO | R | L | TOMPEI: reversed left and right |
| D1-0711 | CC | L | R | TOMPEI: reversed left and right |
| D1-0711 | MLO | L | R | TOMPEI: reversed left and right |
| D1-0999 | MLO | L | R | tags of the two images swapped (pixels) |
| D1-0999 | MLO | R | L | tags of the two images swapped (pixels) |
| D2-0041 | CC | L | R | tags of the two images swapped (pixels) |
| D2-0041 | CC | R | L | tags of the two images swapped (pixels) |
| D2-0224 | MLO | L | R | tags of the two images swapped (pixels) |
| D2-0224 | MLO | R | L | tags of the two images swapped (pixels) |
| D2-0229 | MLO | L | R | tags of the two images swapped (pixels) |
| D2-0229 | MLO | R | L | tags of the two images swapped (pixels) |
| D2-0642 | MLO | L | R | tags of the two images swapped (pixels) |
| D2-0642 | MLO | R | L | tags of the two images swapped (pixels) |

Tag disagrees with pixels but left unchanged (image looks stored mirrored; tag kept): ['D2-0112 L CC']
After correction: duplicate (patient, side, view) = 0  |  our breasts = 2601, TOMPEI breasts = 2601, in both = 2601

## 3. CMMD labels that belong to the other breast

CMMD rows moved to the other side: 10

| patient | CMMD side | corrected side | CMMD class | subtype | TOMPEI on CMMD side | TOMPEI on other side |
|---|---|---|---|---|---|---|
| D1-0252 | R | L | Benign | - | (no such side) | Normal |
| D1-0690 | R | L | Benign | - | (no such side) | Normal |
| D1-0711 | L | R | Benign | - | (no such side) | Normal |
| D2-0048 | L | R | Malignant | HER2-enriched | Normal | Malignant |
| D2-0132 | R | L | Malignant | Luminal A | Normal | Malignant |
| D2-0153 | R | L | Malignant | triple negative | Normal | Invisible |
| D2-0212 | R | L | Malignant | Luminal A | Normal | Malignant |
| D2-0282 | R | L | Malignant | Luminal B | Normal | Malignant |
| D2-0458 | R | L | Malignant | Luminal A | Normal | Malignant |
| D2-0637 | L | R | Malignant | Luminal A | Normal | Malignant |

## 4. CMMD class against TOMPEI class (per breast, after moving those rows)

| cmmd_class    |   Benign |   Exclusion |   Invisible |   Malignant |   Normal |   All |
|:--------------|---------:|------------:|------------:|------------:|---------:|------:|
| (no CMMD row) |        8 |           9 |           0 |           0 |      712 |   729 |
| Benign        |      207 |           7 |           0 |           0 |      342 |   556 |
| Malignant     |        0 |           9 |         140 |        1167 |        0 |  1316 |
| All           |      215 |          25 |         140 |        1167 |     1054 |  2601 |

Subtype against TOMPEI class (per breast):

| subtype         |   Benign |   Exclusion |   Invisible |   Malignant |   Normal |   All |
|:----------------|---------:|------------:|------------:|------------:|---------:|------:|
| (no subtype)    |      215 |          22 |          65 |         496 |     1054 |  1852 |
| HER2-enriched   |        0 |           0 |           9 |         126 |        0 |   135 |
| Luminal A       |        0 |           2 |          10 |         140 |        0 |   152 |
| Luminal B       |        0 |           1 |          40 |         335 |        0 |   376 |
| triple negative |        0 |           0 |          16 |          70 |        0 |    86 |
| All             |      215 |          25 |         140 |        1167 |     1054 |  2601 |

Age differs between TOMPEI and CMMD on 0 breasts: [] (patient, CMMD, TOMPEI). TOMPEI's age is used.
Breasts with no age in either sheet after filling per patient: 0

Breasts with no CMMD row: 729  |  TOMPEI class of these: {'Normal': 712, 'Exclusion': 9, 'Benign': 8}

Breast density (TOMPEI): {'heterogeneous dense': 1671, 'extremely dense': 551, 'scattered': 340, 'fatty': 30, nan: 9}
BI-RADS category (TOMPEI): {1.0: 1055, 2.0: 79, 3.0: 252, 4.0: 399, 5.0: 665, nan: 151}
