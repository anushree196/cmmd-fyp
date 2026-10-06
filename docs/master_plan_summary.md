# Master plan summary (from Anu's Master Document V2 + the merged plan)

## Data
- **CMMD** (TCIA): 1,775 patients, ~5,202 mammograms (CC + MLO, both breasts for many patients). Patient IDs
  `D1-xxxx` (benign/malignant labels) and `D2-xxxx` (malignant with molecular subtype). Clinical sheet
  `CMMD_clinicaldata_revision.xlsx`: check real column names in task 01 (expected roughly ID1, LeftRight, Age,
  number, abnormality, classification, subtype — verify, do not trust this list).
- **TOMPEI-CMMD** (TCIA analysis result): lesion polygon annotations for ~2,436 **MLO-only** images from ~1,363
  patients, plus corrected left/right and view labels. There is **no CC mask**, ever.

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

## Decisions made in this kit (Claude's defaults; Anu can change them)
- DICOMs are converted **once** on the laptop to 8-bit PNG (1024 px tall, breast-cropped, right breasts mirrored).
  Only the PNGs (~2–3 GB) go to the cloud, never the 21 GB of DICOMs. MONAI is still used on Kaggle for
  transforms, CacheDataset and augmentation on these PNGs. The crop box, scale and flip of every image are saved,
  so TOMPEI polygons (drawn on the original DICOM pixels) can be mapped onto the PNGs exactly.
- Input size: E0 uses 224 px to match the paper. Our own models (E1+) default to 512 px, because 224 px throws
  away most of the detail in a mammogram. Report both honestly.

## Semester 2 (merged plan)
Temperature scaling + calibration (ECE, reliability diagrams), uncertainty (MC-dropout or deep ensemble),
an abstain / "wait for IHC" option on Stage 2, "benign biopsies avoided at ~98% sensitivity" from Stage 1,
and a Streamlit app on Hugging Face Spaces.
