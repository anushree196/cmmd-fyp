# Task 01 — inventory summary

Images: 5202  |  patients: 1775  |  D1 patients: 1026  |  D2 patients: 749

## 1. DICOM tags for side and view

| tag | filled | values |
|---|---|---|
| image_laterality | 5202 / 5202 | {'L': 2682, 'R': 2520} |
| laterality | 0 / 5202 | {} |
| view_position | 0 / 5202 | {} |
| view_code_meaning | 5202 / 5202 | {'medio-lateral oblique': 2601, 'cranio-caudal': 2601} |
| series_description | 0 / 5202 | {} |

ImageLaterality and Laterality both filled on 0 images; they disagree on 0.
Images with no side: 0  |  no view: 0
Folder name differs from PatientID tag: 0  |  duplicate SOP UIDs: 0

## 2. Image format

**bits_stored**

| value | count |
|---|---|
| 8 | 5200 |
| 16 | 2 |

Non-8-bit files: [{'patient_id': 'D1-1343', 'side': 'L', 'view': 'MLO'}, {'patient_id': 'D1-1343', 'side': 'L', 'view': 'CC'}]

**manufacturer**

| value | count |
|---|---|
| nan | 5202 |

All images are 2294 x 1914 (rows x cols): True

## 3. Clinical sheet

Columns: ['ID1', 'LeftRight', 'Age', 'number', 'abnormality', 'classification', 'subtype']
Rows: 1872 (one row per labelled breast)  |  patients: 1775
Duplicate (ID1, LeftRight) rows: 0

**labelled breasts per patient**

| value | count |
|---|---|
| 1 | 1678 |
| 2 | 97 |

Patients in the sheet but with no DICOMs: 0  |  patients with DICOMs but not in the sheet: 0
Age: min 17, max 87, mean 47.4, median 46, missing 0
Patients whose two rows give different ages: 0
Patients with one benign breast and one malignant breast: 30
Patients whose two breasts have different subtypes: 0
Malignant rows with no subtype: 567  |  benign rows WITH a subtype: 0

**classification by cohort (rows = breasts)**

| cohort   |   Benign |   Malignant |
|:---------|---------:|------------:|
| D1       |      544 |         563 |
| D2       |       12 |         753 |

**subtype by cohort (rows = breasts)**

| cohort   |   (none) |   HER2-enriched |   Luminal A |   Luminal B |   triple negative |
|:---------|---------:|----------------:|------------:|------------:|------------------:|
| D1       |     1107 |               0 |           0 |           0 |                 0 |
| D2       |       16 |             135 |         152 |         376 |                86 |

## 4. Images without a clinical label

Labelled images: 3744  |  unlabelled images: 1458
Unlabelled images belonging to a patient who has NO labelled image at all: 0
Patients with at least one unlabelled (other-side) breast: 729

**unlabelled images by cohort**

| value | count |
|---|---|
| D2 | 1458 |

## 5. Images per patient and views per breast

**images per patient**

| value | count |
|---|---|
| 2 | 949 |
| 4 | 826 |

**images per (patient, side, view)**

| value | count |
|---|---|
| 1 | 5202 |

Breasts (patient + side): 2601  |  with both CC and MLO: 2601
Labelled breasts: 1872  |  with both CC and MLO: 1872

## 6. Class counts

**classification, per image (labelled images only)**

| value | count |
|---|---|
| Malignant | 2632 |
| Benign | 1112 |

**classification, per breast**

| value | count |
|---|---|
| Malignant | 1316 |
| Benign | 556 |

**classification, per patient (malignant if any breast is malignant)**

| value | count |
|---|---|
| Malignant | 1310 |
| Benign | 465 |

**subtype, per image**

| value | count |
|---|---|
| Luminal B | 752 |
| Luminal A | 304 |
| HER2-enriched | 270 |
| triple negative | 172 |

**subtype, per breast**

| value | count |
|---|---|
| Luminal B | 376 |
| Luminal A | 152 |
| HER2-enriched | 135 |
| triple negative | 86 |

**subtype, per patient**

| value | count |
|---|---|
| Luminal B | 376 |
| Luminal A | 152 |
| HER2-enriched | 135 |
| triple negative | 86 |

Patients with a subtype label: 749

**abnormality, per breast**

| value | count |
|---|---|
| mass | 1149 |
| both | 461 |
| calcification | 262 |
