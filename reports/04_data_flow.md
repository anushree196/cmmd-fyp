# Task 04 — data flow, pairs and splits

## 1. Exclusion flow

| step | breasts | images | patients | what happened |
|---|---|---|---|---|
| All CMMD mammograms | 2601 | 5202 | 1775 | everything downloaded and converted |
| Paired (one CC + one MLO per breast) | 2601 | 5202 | 1775 | 0 breasts lost for a missing view; 0 had more than one image of a view |
| − no CMMD label | −729 | −1458 | | the other breast of 729 D2 patients; not labelled benign or malignant |
| − TOMPEI recommends exclusion | −16 | −32 | | {'Phyllodes tumor': 6, 'Presence of white objects': 2, 'Foreign object at the top': 1, 'Scale is incorrect': 1, 'Image noise': 1, 'Breast augmentation': 1, 'Lower part missing': 1, 'Neurofibromatosis': 1, 'Unclear on image/Pacemaker?': 1, 'Lymphedema': 1} |
| **Stage 1 set** | **1856** | **3712** | **1762** | benign 549 / malignant 1307 breasts |
| Malignant with a subtype label | 749 | 1498 | 749 | one breast per patient |
| − no lesion mask | −78 | −156 | −78 | TOMPEI class: {'Invisible': 75, 'Exclusion': 3} |
| **Stage 2 set** | **671** | **1342** | **671** | Luminal A 140 / Luminal B 335 / HER2-enriched 126 / triple negative 70 |

TOMPEI class of the 729 unlabelled breasts (left out): {'Normal': 712, 'Exclusion': 9, 'Benign': 8}
Patients with no breast in Stage 1 at all: 13

## 2. Stage 1 set (per breast)

| cmmd_class   |   Benign |   Invisible |   Malignant |   Normal |   All |
|:-------------|---------:|------------:|------------:|---------:|------:|
| Benign       |      207 |           0 |           0 |      342 |   549 |
| Malignant    |        0 |         140 |        1167 |        0 |  1307 |
| All          |      207 |         140 |        1167 |      342 |  1856 |

Patients: 1762  |  with two breasts in the set: 94  |  with one benign and one malignant breast: 30
Cohort: {'D1': 1095, 'D2': 761}  |  age 17–87, mean 47.4
Abnormality: {'mass': 1138, 'both': 459, 'calcification': 259}
Breasts with a lesion mask (MLO): 1374
QC-flagged breasts (all 2,601 checked): [{'patient_id': 'D1-0951', 'side': 'R', 'stage1_status': 'excluded: TOMPEI exclusion', 'exclusion_reason': 'Scale is incorrect', 'qc_note': 'MLO source image damaged: black holes inside the tissue, upper strip cut off'}]

## 3. Splits (70 / 15 / 15, per patient, seed 42)

Every patient is assigned once. Strata used for the assignment (patients):

| stratum                           |   train |   val |   test |   all |
|:----------------------------------|--------:|------:|-------:|------:|
| Stage 2: HER2-enriched            |      88 |    19 |     19 |   126 |
| Stage 2: Luminal A                |      98 |    21 |     21 |   140 |
| Stage 2: Luminal B                |     235 |    50 |     50 |   335 |
| Stage 2: triple negative          |      49 |    10 |     11 |    70 |
| benign only                       |     321 |    69 |     69 |   459 |
| malignant, not in Stage 2         |     429 |    92 |     92 |   613 |
| one benign + one malignant breast |      13 |     3 |      3 |    19 |

**Stage 1, breasts per split**

| cmmd_class   | train       | val         | test        | all          |
|:-------------|:------------|:------------|:------------|:-------------|
| Benign       | 375 (29.1%) | 84 (30.0%)  | 90 (31.4%)  | 549 (29.6%)  |
| Malignant    | 914 (70.9%) | 196 (70.0%) | 197 (68.6%) | 1307 (70.4%) |
| total        | 1289        | 280         | 287         | 1856         |

Stage 1 patients per split: {'train': 1233, 'val': 264, 'test': 265}

**Stage 2, patients per split**

| subtype         | train       | val        | test       | all         |
|:----------------|:------------|:-----------|:-----------|:------------|
| HER2-enriched   | 88 (18.7%)  | 19 (19.0%) | 19 (18.8%) | 126 (18.8%) |
| Luminal A       | 98 (20.9%)  | 21 (21.0%) | 21 (20.8%) | 140 (20.9%) |
| Luminal B       | 235 (50.0%) | 50 (50.0%) | 50 (49.5%) | 335 (49.9%) |
| triple negative | 49 (10.4%)  | 10 (10.0%) | 11 (10.9%) | 70 (10.4%)  |
| total           | 470         | 100        | 101        | 671         |

Subgroups for later reporting (Stage 1 breasts):

|                                           |   train |   val |   test |   all |
|:------------------------------------------|--------:|------:|-------:|------:|
| malignant, TOMPEI Invisible               |      92 |    26 |     22 |   140 |
| malignant, TOMPEI Malignant               |     822 |   170 |    175 |  1167 |
| benign, TOMPEI Normal (no visible lesion) |     234 |    45 |     63 |   342 |
| benign, TOMPEI Benign                     |     141 |    39 |     27 |   207 |
| dense breast                              |    1107 |   239 |    251 |  1597 |
| not dense                                 |     182 |    41 |     36 |   259 |
| density missing                           |       0 |     0 |      0 |     0 |

Stage 2 patients by density and split:

| density             |   train |   val |   test |
|:--------------------|--------:|------:|-------:|
| extremely dense     |      83 |    20 |     13 |
| fatty               |       6 |     2 |      3 |
| heterogeneous dense |     308 |    66 |     73 |
| scattered           |      73 |    12 |     12 |

## 4. E0 split (image-wise 72 / 18 / 10, Stage 2 images, copies the baseline paper)


**E0, images per split**

| subtype         | train       | val         | test       | all         |
|:----------------|:------------|:------------|:-----------|:------------|
| HER2-enriched   | 181 (18.7%) | 46 (19.1%)  | 25 (18.5%) | 252 (18.8%) |
| Luminal A       | 202 (20.9%) | 50 (20.7%)  | 28 (20.7%) | 280 (20.9%) |
| Luminal B       | 482 (49.9%) | 120 (49.8%) | 68 (50.4%) | 670 (49.9%) |
| triple negative | 101 (10.5%) | 25 (10.4%)  | 14 (10.4%) | 140 (10.4%) |
| total           | 966         | 241         | 135        | 1342        |

Patients whose two images fall in different splits (leakage, by design in E0 only): 282 of 671
E0 test images whose patient also has an image in E0 train: 95 of 135
