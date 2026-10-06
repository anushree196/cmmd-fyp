# Master plan summary (from Anu's Master Document V2 + the merged plan)

## Data
- **CMMD** (TCIA): 1,775 patients, ~5,202 mammograms (CC + MLO, both breasts for many patients). Patient IDs
  `D1-xxxx` (benign/malignant labels) and `D2-xxxx` (malignant with molecular subtype). Clinical sheet
  `CMMD_clinicaldata_revision.xlsx`: check real column names in task 01 (expected roughly ID1, LeftRight, Age,
  number, abnormality, classification, subtype — verify, do not trust this list).
- **TOMPEI-CMMD** (TCIA analysis result): lesion polygon annotations for 1,385 **MLO-only** images (one per
  breast, 1,773 lesions) from 1,363 patients, plus a corrected per-breast label sheet (2,601 breasts).
  There is **no CC mask**, ever. (Counts measured in task 03; the earlier "~2,436 images" was wrong: 2,436 is
  the number of breasts TOMPEI did not flag with an exclusion reason.)

## Stage 1 — benign vs malignant (all patients)
Inputs: full CC + full MLO (uncropped) + age + lesion type. Shared EfficientNet-B3 encoder, View Attention,
concatenate with clinical MLP, 2-class head.

## Stage 2 — subtype (malignant, with subtype label AND TOMPEI mask)
Inputs: CC + MLO full views, MLO lesion crop (from the real polygon mask), top-20 radiomics from the real mask,
clinical. Gated Fusion of [512 image + 64 radiomics + 32 clinical]. 4 classes: LumA / LumB / HER2 / TN.

## Ablation (Stage 2, ALL on the same fixed subset = subtype label ∩ TOMPEI mask)
| Exp | Change |
|---|---|
| E0 | Reproduce baseline: single-view Xception + age + lesion type, image-wise split, 224×224 |
| E1 | EfficientNet-B3, patient-wise split, single view |
| E2 | + dual view (CC + MLO) with View Attention |
| E3 | + MLO lesion crop |
| E4 | + radiomics branch (real mask) |
| E5 | concatenation → Gated Fusion |
| E6 | full system |

Baseline paper: Ben Rabah et al., Diagnostics 2025, 15, 995 (overall AUC 88.87%, LumA 67%, LumB 74%).
Their code is NOT public — reproduce from the paper text.

Combined score: chain Stage 1 → Stage 2 into one 5-class probability per patient (Benign, LumA, LumB, HER2, TN)
and compute one-vs-rest macro AUC (Master doc §7.1).

## Decisions already made (do not reopen without asking Anu)
- Label source: TOMPEI-CMMD corrected labels for ALL experiments, E0 included.
- Patient-wise stratified splits (except E0, which copies the paper's image-wise split on purpose).
- Grading = molecular subtype (stated as a scope choice in the report).
- Stage 1 trains **per breast**: one sample = the CC + MLO pair of one breast, with that breast's own
  benign/malignant label (30 patients have one benign and one malignant breast, so a patient-level label would
  be wrong for them). Splits stay **per patient**: both breasts of a patient always land in the same split.
  (Anu, 2026-10-07, after task 01.)
- The 1,458 images with no clinical row (the other breast of 729 D2 patients) are **excluded** from training and
  evaluation; nothing says they are benign. They are counted in the data-flow report. (Anu, 2026-10-07.)
- Stage 1 label = CMMD's benign / malignant (the biopsy result), with TOMPEI's left/right corrections applied.
  TOMPEI's "Normal" (benign, no lesion locatable) and "Invisible" (malignant, not locatable) breasts are
  **kept**: they describe visibility, not pathology. Only the 16 labelled breasts TOMPEI recommends excluding
  are dropped → 549 benign / 1,307 malignant breasts. TOMPEI class, breast density and BI-RADS are carried as
  extra columns in the pair table so results can be reported separately for "Invisible" cancers and dense
  breasts. (Anu, 2026-10-07, after task 03.)

## Decisions made in this kit (Claude's defaults; Anu can change them)
- DICOMs are converted **once** on the laptop to 8-bit PNG (1024 px tall, breast-cropped, right breasts mirrored).
  Only the PNGs (~2–3 GB) go to the cloud, never the 21 GB of DICOMs. MONAI is still used on Kaggle for
  transforms, CacheDataset and augmentation on these PNGs. The crop box, scale and flip of every image are saved,
  so TOMPEI polygons (drawn on the original DICOM pixels) can be mapped onto the PNGs exactly.
- One patient split for both stages: every patient is assigned to train / val / test once (70/15/15, seed 42,
  stratified by subtype for Stage 2 patients and by benign / malignant / mixed for the rest). `stage1.csv` and
  `stage2.csv` are both cut from that assignment, so a Stage 2 test patient is never a Stage 1 training patient
  and the chained 5-class score is clean.
- Input size: E0 uses 224 px to match the paper. Our own models (E1+) default to 512 px, because 224 px throws
  away most of the detail in a mammogram. Report both honestly.

## Semester 2 (merged plan)
Temperature scaling + calibration (ECE, reliability diagrams), uncertainty (MC-dropout or deep ensemble),
an abstain / "wait for IHC" option on Stage 2, "benign biopsies avoided at ~98% sensitivity" from Stage 1,
and a Streamlit app on Hugging Face Spaces.
