**20 — ADVANCED MULTIMODAL DEEP LEARNING FRAMEWORK**

**FOR INTEGRATED BREAST CANCER DIAGNOSIS & GRADING**

*(Official Assigned Project Title — Unchanged)*

*VERSION 2 — Corrected, Verified, MONAI-Integrated Master Document*

Computer Engineering \| University of Mumbai (NHITM)

2025–2026

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>WHAT CHANGED IN THIS VERSION</strong></p>
<p>A second technical review surfaced 10 real loopholes in the V1
document — some severe enough to silently break the core novelty claim.
Every one is fixed here. The DICOM/mask pipeline has also been rebuilt
on MONAI, which removes an entire class of manual-preprocessing bugs and
fixes the most serious loophole (Shape2D radiomics being computed on a
fake rectangular mask instead of the real tumour shape). The Streamlit
hosting concern is solved with a free, always-on deployment
path.</p></td>
</tr>
</tbody>
</table>

**0. DOES THE ASSIGNED TITLE MATCH THIS PROJECT?**

Short answer: yes, with no changes needed. Here is the word-by-word
justification so you can defend it to any panel without hesitation.

|                         |                                                                                                                                                                                                                                                                                                                                                         |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Word in Title**       | **What It Maps To in This Project**                                                                                                                                                                                                                                                                                                                     |
| Advanced                | Two-stage hierarchical pipeline, dual-view attention, radiomics fusion, gated multimodal fusion, MONAI-based medical imaging pipeline — not a single off-the-shelf classifier                                                                                                                                                                           |
| Multimodal              | Three true modalities combined: (1) mammography imaging — CC + MLO views, (2) radiomics — quantitative texture features extracted from the lesion, (3) clinical metadata — age, lesion type                                                                                                                                                             |
| Deep Learning Framework | EfficientNet-B3 CNN backbone + View Attention module + Gated Fusion module + two-stage classifier heads, trained end-to-end with transfer learning                                                                                                                                                                                                      |
| Integrated              | Imaging, radiomics, and clinical data are integrated into one fused decision per patient via the Gated Fusion module — not analysed separately and compared after the fact                                                                                                                                                                              |
| Breast Cancer Diagnosis | Stage 1 of the pipeline: Benign vs. Malignant classification from dual-view mammography + clinical data                                                                                                                                                                                                                                                 |
| & Grading               | Stage 2 of the pipeline: molecular subtype classification (Luminal A / Luminal B / HER2 / Triple-Negative) — these four subtypes carry distinct prognostic severity and treatment intensity, which is the accepted interpretation of 'grading' when histopathological Nottingham grade is not available in the dataset (explained fully in Section 1.4) |

|                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| One honest clarification to write into your report's scope section: 'Grading' here refers to molecular subtype classification (a recognised proxy for tumour aggressiveness and treatment planning), not formal histopathological Nottingham grade (1/2/3), which requires a tissue biopsy and is not present in the CMMD dataset. State this explicitly in your methodology — it pre-empts the single question a panel is most likely to ask about the title. |

**1. THE STORY IN PLAIN LANGUAGE**

Breast cancer is not one disease — it is at least five. Two of them,
Luminal A and Luminal B, look almost identical on an X-ray. The real
difference lives inside the cell (a protein called Ki-67 that shows how
fast cells divide). This matters because Luminal A patients typically
need only hormone therapy, while Luminal B patients usually need
chemotherapy too.

In April 2025, a team from Weill Cornell Medicine-Qatar tried to
classify five breast cancer types using a mammogram plus two basic facts
about the patient. Their model did well overall (88.87% AUC) but
specifically failed on Luminal A and Luminal B (67% and 74% AUC — barely
better than guessing).

Our project directly attacks this failure using four upgrades over their
approach:

- Two views of the mammogram (CC + MLO) instead of one

- TOMPEI-CMMD lesion masks — published in 2025, after the baseline paper
  — so we know exactly where the tumour is

- Radiomics — mathematical texture measurements of the tumour's actual
  shape and pattern, not a generic rectangle

- Gated fusion — the model learns how much to trust each information
  source per patient, instead of just adding everything together

Target user: a radiologist or oncologist using this as a
decision-support second opinion — not a patient-facing app, and not a
replacement for biopsy-confirmed diagnosis.

**2. THE BASELINE PAPER — WHAT IT DID, AND A CORRECTION ON ITS CODE**

**2.1 Citation and Verified Facts**

Ben Rabah C., Sattar A., Ibrahim A., Serag A. 'A Multimodal Deep
Learning Model for the Classification of Breast Cancer Subtypes.'
Diagnostics 2025, 15, 995. DOI: 10.3390/diagnostics15080995

|                           |                                                                    |
|---------------------------|--------------------------------------------------------------------|
| **What They Did**         | **Their Result**                                                   |
| Dataset                   | CMMD — 5,202 mammograms, 1,775 patients (filtered to 4,056 images) |
| Backbone                  | Xception pretrained on ImageNet, fine-tuned                        |
| Clinical data used        | Age (binarized at 40) + Lesion type (0-3 encoded)                  |
| Fusion method             | Simple concatenation: 512 (image) + 32 (clinical) = 544-dim        |
| Split type                | Image-wise (72/18/10), NOT patient-wise                            |
| Overall AUC               | 88.87%                                                             |
| Luminal A / Luminal B AUC | 67% / 74% — the gap we are targeting                               |
| GPU used                  | NVIDIA A100 80GB, 10 epochs, batch size 64                         |

**2.2 CORRECTION: Their GitHub Code Is Not Publicly Available**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>This corrects an error in the previous version of this
document, which told you to reference their GitHub repo as
code.</strong></p>
<p>Verified by direct search: the URL the paper cites —
github.com/serag-ai/Multimodal-BC-Classifier — does not appear in any
search index, while the same lab's other repositories (M3, I-SynMed,
ChatCVD, Multimodal-Synthetic-Medical-Images) all show up normally. The
paper itself contains a contradiction: Section 2.4 states the code 'has
been made available on GitHub' with that exact URL, while the Data
Availability Statement on page 15 says 'the source code will be shared
upon acceptance of this paper.' The second statement is the accurate
one.</p>
<p><em>PRACTICAL IMPACT: budget zero time hoping to find or reference
their code. Implement your E0 reproduction (Section 7) purely from the
paper's written architecture description — Section 2.3 of their paper,
summarised in the table above, is detailed enough to do
this.</em></p></td>
</tr>
</tbody>
</table>

**2.3 What the Paper Itself Admits It Got Wrong**

|                                                  |                                                                               |
|--------------------------------------------------|-------------------------------------------------------------------------------|
| **Their Stated Limitation**                      | **Our Fix**                                                                   |
| No tumour localisation — model sees whole breast | TOMPEI-CMMD masks crop the exact lesion (MLO view only — see Section 3.2)     |
| Only one mammogram view used                     | Both CC and MLO with View Attention (CC has no lesion mask — see Section 3.2) |
| Only age + lesion type as metadata               | Add radiomics texture features extracted from the real lesion shape           |
| Simple concatenation fusion                      | Gated Fusion module — learned per-patient trust weighting                     |
| Image-wise split (data leakage risk)             | Patient-wise stratified split, verified by column name (Section 5.1)          |

**3. CORRECTED ARCHITECTURE — TWO STAGES, MLO-ONLY LESION DATA**

**3.1 The Critical Fix: TOMPEI-CMMD Only Covers the MLO View**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>This is the single most important correction in this
document.</strong></p>
<p>TOMPEI-CMMD's own dataset description states it covers 2,436 MLO-view
mammograms from 1,363 patients — the CC views were excluded entirely
when this annotation set was built. There is no lesion mask for the CC
view. Anywhere. For any patient.</p>
<p>WHAT THIS MEANS FOR THE ARCHITECTURE: Stage 2's 'lesion crop' input
can only ever be built from the MLO image. The CC image is still used —
full, uncropped — in the dual-view branch of both stages. It is never
cropped to the lesion, because no ground-truth mask exists for it. The
diagram and code below reflect this explicitly so nobody on the team
gets stuck looking for a CC lesion mask that does not exist.</p></td>
</tr>
</tbody>
</table>

**3.2 Stage 1 — Screening (Benign vs. Malignant)**

|                    |                                                                        |
|--------------------|------------------------------------------------------------------------|
| **Component**      | **Detail**                                                             |
| Input A — CC View  | Full mammogram, 224x224, NOT cropped (no CC mask exists)               |
| Input B — MLO View | Full mammogram, 224x224, NOT cropped (lesion crop is Stage 2 only)     |
| Input C — Clinical | Age (normalised) + lesion type one-hot (5-dim)                         |
| Image encoder      | EfficientNet-B3 pretrained, shared weights between CC and MLO branches |
| View Attention     | Learns per-patient weighting between CC and MLO feature vectors        |
| Fusion             | Concatenate \[512 image + 32 clinical\] = 544-dim                      |
| Output             | 2 classes: Benign / Malignant                                          |
| Training data      | All 1,775 patients — TOMPEI annotation availability is IRRELEVANT here |

**3.3 Stage 2 — Molecular Subtype Classification (corrected)**

|                           |                                                                                                                       |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Component**             | **Detail**                                                                                                            |
| Input A — CC View         | Full mammogram, 224x224, uncropped (same as Stage 1)                                                                  |
| Input B — MLO View        | Full mammogram, 224x224, uncropped — used for the image-encoder branch                                                |
| Input C — MLO Lesion Crop | MLO image cropped to TOMPEI-CMMD polygon mask bounding box (MLO ONLY — explicit fix for the V1 ambiguity)             |
| Input D — Radiomics       | Top 20 features extracted from Input C using the REAL polygon mask (fix for the rectangle-mask bug — see Section 4)   |
| Input E — Clinical        | Age + lesion type one-hot (5-dim)                                                                                     |
| Image encoder             | EfficientNet-B3 + View Attention (CC + MLO), independently trained from Stage 1                                       |
| Radiomics MLP             | Dense(20→64)→ReLU→Dropout(0.2)                                                                                        |
| Clinical MLP              | Dense(5→32)→ReLU                                                                                                      |
| Gated Fusion              | Combines \[512 image + 64 radiomics + 32 clinical\] = 608-dim with learned trust gate                                 |
| Output                    | 4 classes: Luminal A / Luminal B / HER2 / Triple-Negative                                                             |
| Training data             | ONLY patients with both a confirmed subtype label AND a TOMPEI-CMMD mask — verify exact count in Week 1 (Section 5.2) |

**3.4 The Fair-Comparison Fix for Your Ablation Study**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>PROBLEM: only ~1,363 of ~2,948 malignant patients have a
TOMPEI mask. If E0-E2 train on all 2,948 patients but E3 onward train on
only ~1,363, any AUC change could be caused by the different patient
subset, not by your architecture changes — making the entire ablation
study scientifically invalid.</strong></p>
<p>THE FIX (mandatory, not optional): restrict ALL Stage 2 experiments —
E0 through E6 — to the same fixed subset of patients who have both a
confirmed subtype label and a TOMPEI mask. Yes, this is a smaller
dataset than the original paper used. State this explicitly as a
limitation in your methodology: 'For fair ablation comparison, all Stage
2 experiments use the TOMPEI-CMMD-annotated subset (N=[exact count from
Week 1]), which is smaller than the full CMMD subtype-labelled cohort
used by the baseline paper.' Reviewers respect an honestly-scoped fair
comparison far more than a larger but confounded one.</p></td>
</tr>
</tbody>
</table>

**4. THE MONAI DATA PIPELINE (REPLACES MANUAL PREPROCESSING)**

**4.1 Why MONAI Instead of Manual pydicom/PIL Code**

MONAI is a PyTorch-based medical imaging library built for exactly this
kind of pipeline. It replaces hand-written DICOM windowing and crop
functions with a declarative transform pipeline — you describe what
should happen to the data, MONAI handles when and caches the result for
speed. Three concrete advantages over the manual approach:

- Correct DICOM windowing (VOI LUT) is applied automatically — no need
  to manually read WindowCenter/WindowWidth tags and risk getting the
  MultiValue handling wrong

- Image and mask are loaded and transformed together as a paired
  dictionary, so a crop applied to the image is automatically applied
  identically to the mask — this is what fixes the rectangle-mask bug
  (Section 4.3)

- CacheDataset stores the preprocessed result after the first pass, so a
  laptop with no GPU can still iterate quickly during preprocessing and
  debugging

You are not required to use MONAI — a manual pydicom pipeline works too,
and is documented as a fallback in Section 4.5. But MONAI is the more
correct and significantly less error-prone path, and it is what closes
the most serious loophole found in review.

**4.2 Install**

> pip install monai pydicom SimpleITK

**4.3 Step 1: Convert TOMPEI JSON Polygons to Real NIfTI Masks**

This step turns each TOMPEI-CMMD JSON annotation into an actual binary
mask image (not a rectangle), saved once so MONAI can load it alongside
the DICOM.

> import json, numpy as np, SimpleITK as sitk
>
> from PIL import Image, ImageDraw
>
> def tompei_json_to_mask(json_path, image_width, image_height):
>
> with open(json_path) as f:
>
> data = json.load(f)
>
> mask = Image.new('L', (image_width, image_height), 0)
>
> draw = ImageDraw.Draw(mask)
>
> for annotation in data:
>
> points = \[(pt\['x'\], pt\['y'\]) for pt in annotation\['cgPoints'\]\]
>
> if len(points) \>= 3:
>
> draw.polygon(points, fill=255) \# REAL polygon shape, not a box
>
> return np.array(mask)
>
> \# Save as NIfTI so MONAI can load image + mask as a matched pair
>
> mask_array = tompei_json_to_mask(json_path, img_w, img_h)
>
> mask_img = sitk.GetImageFromArray((mask_array \> 0).astype('uint8'))
>
> sitk.WriteImage(mask_img, f'masks/{patient_id}\_mlo_mask.nii.gz')

**4.4 Step 2: Two Transform Pipelines (Full View + Lesion Crop)**

> from monai.transforms import (
>
> LoadImaged, EnsureChannelFirstd, ScaleIntensityd,
>
> Resized, CropForegroundd, RandFlipd, ToTensord, Compose
>
> )
>
> \# Pipeline A — full mammogram, CC and MLO, NO mask (used in both
> stages)
>
> full_view_transforms = Compose(\[
>
> LoadImaged(keys=\['cc_image', 'mlo_image'\]), \# reads DICOM, applies
> VOI LUT automatically
>
> EnsureChannelFirstd(keys=\['cc_image', 'mlo_image'\]),
>
> Resized(keys=\['cc_image', 'mlo_image'\], spatial_size=(224, 224)),
>
> ScaleIntensityd(keys=\['cc_image', 'mlo_image'\]),
>
> RandFlipd(keys=\['cc_image', 'mlo_image'\], prob=0.5, spatial_axis=1),
> \# horizontal only
>
> ToTensord(keys=\['cc_image', 'mlo_image'\]),
>
> \])
>
> \# Pipeline B — MLO lesion crop ONLY, uses the REAL polygon mask
>
> \# Stage 2 only. There is no CC equivalent — see Section 3.1.
>
> lesion_transforms = Compose(\[
>
> LoadImaged(keys=\['mlo_image', 'lesion_mask'\]),
>
> EnsureChannelFirstd(keys=\['mlo_image', 'lesion_mask'\]),
>
> CropForegroundd(keys=\['mlo_image', 'lesion_mask'\],
>
> source_key='lesion_mask', margin=20),
>
> \# crops BOTH image and mask identically to the mask's bounding box +
> 20px padding
>
> Resized(keys=\['mlo_image', 'lesion_mask'\], spatial_size=(224, 224)),
>
> ScaleIntensityd(keys=\['mlo_image'\]),
>
> ToTensord(keys=\['mlo_image', 'lesion_mask'\]),
>
> \])

CropForegroundd is the transform that replaces the old manual
crop_lesion_roi() function. It crops to the mask's bounding box and
carries the resized mask forward — which is exactly what the radiomics
step needs next.

**4.5 Step 3: Radiomics on the REAL Mask (the critical bug fix)**

|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **BUG IN V1 OF THIS DOCUMENT: the previous radiomics code passed np.ones_like(lesion_crop_array) as the mask into PyRadiomics — an all-ones rectangle, not the tumour's real shape. This silently breaks every Shape2D feature (perimeter, sphericity, elongation), which the document itself flagged as relevant to the Luminal A/B distinction. With a rectangular mask, every patient's 'tumour shape' feature just describes a rectangle of slightly different size — meaningless for classification.** |

> import SimpleITK as sitk
>
> from radiomics import featureextractor
>
> extractor = featureextractor.RadiomicsFeatureExtractor(
>
> binWidth=25, normalize=True, normalizeScale=100)
>
> extractor.enableFeatureClassByName('glcm')
>
> extractor.enableFeatureClassByName('glrlm')
>
> extractor.enableFeatureClassByName('shape2D')
>
> extractor.enableFeatureClassByName('firstorder')
>
> \# After the MONAI lesion_transforms pipeline runs, you have BOTH
>
> \# cropped_image and cropped_mask as numpy arrays — same shape, same
> crop.
>
> image_sitk = sitk.GetImageFromArray(cropped_image)
>
> mask_sitk = sitk.GetImageFromArray(cropped_mask.astype('uint8'))
>
> \# ^ THE FIX: real polygon-derived mask, NOT np.ones_like(...)
>
> features = extractor.execute(image_sitk, mask_sitk, label=1)
>
> rad_values = {k: float(v) for k, v in features.items()
>
> if k.startswith(('original_glcm', 'original_glrlm',
>
> 'original_shape2D', 'original_firstorder'))}

This single change — real mask instead of np.ones_like — is what makes
Shape2D radiomics features actually carry tumour-shape information,
which is the entire premise of the Luminal A/B novelty claim. Without
it, you would be running an expensive feature extraction pipeline that
produces a near-useless shape signal.

**4.6 Step 4: CacheDataset for Laptop Speed**

> from monai.data import CacheDataset, DataLoader
>
> train_ds = CacheDataset(data=train_manifest,
> transform=full_view_transforms, cache_rate=0.5)
>
> train_loader = DataLoader(train_ds, batch_size=16, shuffle=True,
> num_workers=2)

cache_rate=0.5 caches half the dataset in RAM after first pass — tune
down to 0.2-0.3 if your laptop has limited RAM (8GB).

**4.7 Pipeline Summary (for the whole team to memorise)**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p>TOMPEI JSON → real polygon mask → save as NIfTI</p>
<p>→ MONAI loads MLO DICOM + mask together (VOI LUT applied
automatically)</p>
<p>→ CropForegroundd crops both consistently to the lesion bounding
box</p>
<p>→ Radiomics extraction uses the REAL cropped mask, not a
rectangle</p>
<p>→ Model receives clean resized tensors — MONAI's job ends here,
architecture (Section 3) takes over</p></td>
</tr>
</tbody>
</table>

**5. DATA SPLIT, LABEL CONSISTENCY, AND PAIRING — CORRECTED**

**5.1 Verify the Real Column Names Before Writing Split Code**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>V1 BUG: the patient-wise split code stratified by a
column called classification, assumed to hold the 5-class subtype label.
In the real CMMD clinical sheet, classification typically holds only
Benign/Malignant — the molecular subtype is usually a separate column
(commonly named subtype or similar). If you stratify by the wrong
column, your split silently fails to balance subtype classes, and you
will not get an error — just a quietly biased split.</strong></p>
<p>THE FIX: in Week 1, open the downloaded XLSX in Excel and write down
the EXACT column names before touching code: patient ID column,
left/right column, benign/malignant column, AND the separate molecular
subtype column. Update the code below with the real names.</p></td>
</tr>
</tbody>
</table>

> import pandas as pd
>
> df = pd.read_excel('cmmd_clinical.xlsx')
>
> print(df.columns.tolist()) \# \<-- RUN THIS FIRST. Do not guess column
> names.
>
> print(df\['classification'\].unique()) \# confirm: is this
> Benign/Malignant only?
>
> \# Find the actual subtype column — look for something like 'subtype',
> 'molecular_subtype'
>
> \# print(df\['subtype'\].unique()) \# should show: LumA, LumB, HER2,
> TN (and NaN for benign)
>
> \# Once real column names are confirmed, stratify by the SUBTYPE
> column for Stage 2,
>
> \# and by the BENIGN/MALIGNANT column for Stage 1 — they are different
> splits, see 5.3
>
> patient_ids = df\['ID1'\].unique() \# \<-- verify 'ID1' is the real
> column name
>
> patient_subtype =
> df.groupby('ID1')\['ACTUAL_SUBTYPE_COLUMN_NAME'\].first()

**5.2 Week 1 Mandatory Check: Count the Real Stage 2 Dataset Size**

Before any model code: run this and write the resulting number into your
project log. This is the real size of your Stage 2 dataset for E0
through E6 (Section 3.4).

> import os
>
> subtype_patients =
> set(df\[df\['ACTUAL_SUBTYPE_COLUMN_NAME'\].notna()\]\['ID1'\].unique())
>
> tompei_mask_files = os.listdir('tompei_json/')
>
> tompei_patients = set(f.split('\_')\[0\] for f in tompei_mask_files)
> \# adjust parsing to real filenames
>
> usable_patients = subtype_patients & tompei_patients
>
> print(f'Patients with subtype label: {len(subtype_patients)}')
>
> print(f'Patients with TOMPEI mask: {len(tompei_patients)}')
>
> print(f'USABLE for Stage 2 (E0-E6): {len(usable_patients)}') \# \<--
> THE REAL NUMBER

**5.3 CC/MLO Pairing Logic (missing in V1, added here)**

Many patients have multiple images per breast/laterality. Before Stage 1
can take 'one CC + one MLO' as clean inputs, each patient-breast-side
must be paired to exactly one CC and one MLO image. Without this
explicit step, the dataset loader will not know which CC goes with which
MLO.

> def build_cc_mlo_pairs(df):
>
> pairs = \[\]
>
> for (patient_id, side), group in df.groupby(\['ID1', 'LeftRight'\]):
>
> cc_rows = group\[group\['view'\] == 'CC'\] \# verify real column/value
> names
>
> mlo_rows = group\[group\['view'\] == 'MLO'\]
>
> if len(cc_rows) == 0 or len(mlo_rows) == 0:
>
> continue \# incomplete pair — exclude and log this count
>
> \# if multiple images per view exist, take the first (or apply your
> own tie-break rule)
>
> pairs.append({
>
> 'patient_id': patient_id,
>
> 'side': side,
>
> 'cc_path': cc_rows.iloc\[0\]\['image_path'\],
>
> 'mlo_path': mlo_rows.iloc\[0\]\['image_path'\],
>
> })
>
> return pd.DataFrame(pairs)

Log how many patients get excluded for incomplete pairs — report this
number in your data flow diagram, same as the 2025 paper's own exclusion
flowchart (their Figure 2).

**5.4 Label Consistency: Pick ONE Source, Use It Everywhere**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p>ISSUE: TOMPEI-CMMD provides 'corrected' left/right and view
labels. If E0 (reproduction) uses original CMMD labels while E3 onward
uses TOMPEI's corrected labels, the ablation study compares against a
shifting ground truth — confounding architecture changes with label
changes.</p>
<p><strong>THE FIX: decide in Week 1 — use TOMPEI-CMMD's corrected
labels for ALL experiments, E0 through E6, including the baseline
reproduction. This is defensible because TOMPEI's corrections fix
genuine errors (mislabeled L/R and CC/MLO orientation), so your E0
reproduction will be on slightly cleaner data than the original paper —
note this honestly as a minor methodological difference in your results
discussion.</strong></p></td>
</tr>
</tbody>
</table>

**6. ALWAYS-ON DEPLOYMENT — FIXING THE STREAMLIT SLEEP PROBLEM**

**6.1 Why Streamlit Community Cloud Sleeps**

Streamlit Community Cloud puts apps to sleep after a period of
inactivity (commonly reported around 3-7 days idle) to conserve
free-tier resources. A 'wake up' click is needed to bring it back, which
is unacceptable for a live demo link you want to show a panel or
recruiter at any time without warning.

**6.2 The Fix: Hugging Face Spaces (Free, Does Not Sleep the Same Way)**

Hugging Face Spaces offers free CPU hosting (2 vCPU, 16GB RAM) with the
Docker SDK, which runs your Streamlit app inside a container you fully
control. This is the recommended fix for three reasons specific to this
project:

- Spaces on the free CPU tier remain accessible far more reliably than
  Streamlit Community Cloud's sleep policy — there is no equivalent
  aggressive inactivity sleep for standard Spaces usage

- Because you control the Dockerfile, you avoid the pyradiomics build
  failures that plague Streamlit Cloud's locked-down build environment —
  you specify the exact base image and system packages PyRadiomics needs
  to compile

- Deployment is git-based: push to your Space's repo, it rebuilds and
  redeploys automatically — clean for a final-year project demo you'll
  update repeatedly

**6.3 Step-by-Step: Deploying to Hugging Face Spaces**

1.  Create a free account at huggingface.co

2.  Click 'New Space' → choose a name → select License (MIT is fine for
    an academic project)

3.  For SDK, click 'Docker' → select the 'Streamlit' Docker template

4.  Hardware: leave as default 'CPU basic · 2 vCPU · 16GB · FREE' —
    sufficient for inference with a pretrained EfficientNet-B3, no GPU
    needed for demo-speed predictions

5.  Clone the Space repo locally: git clone
    https://huggingface.co/spaces/yourusername/your-space-name

6.  Copy your app.py, requirements.txt, trained model weights (.pth),
    and the Dockerfile (template below) into this folder

7.  git add . && git commit -m 'deploy' && git push — the Space rebuilds
    automatically

**6.4 Dockerfile (Solves the PyRadiomics Build Problem Mentioned in
Review)**

The reviewer correctly flagged that pyradiomics (a compiled C-extension)
often fails to build on Streamlit Cloud's default environment. A custom
Dockerfile on Hugging Face Spaces solves this because you control the
exact build steps:

> FROM python:3.10-slim
>
> RUN apt-get update && apt-get install -y \\
>
> build-essential gcc g++ \\
>
> && rm -rf /var/lib/apt/lists/\*
>
> WORKDIR /app
>
> COPY requirements.txt .
>
> RUN pip install --no-cache-dir -r requirements.txt
>
> COPY . .
>
> EXPOSE 7860
>
> CMD \["streamlit", "run", "app.py", "--server.port=7860",
> "--server.address=0.0.0.0"\]

Note: Hugging Face Spaces expects the app to listen on port 7860, not
Streamlit's default 8501 — the CMD above handles this.

**6.5 requirements.txt — Pinned Versions to Avoid Build Conflicts**

> streamlit==1.38.0
>
> torch==2.2.0
>
> torchvision==0.17.0
>
> monai==1.3.2
>
> pydicom==2.4.4
>
> SimpleITK==2.3.1
>
> pyradiomics==3.1.0
>
> numpy==1.26.4
>
> pillow==10.3.0
>
> pandas==2.2.2
>
> shap==0.45.1
>
> grad-cam==1.5.2
>
> matplotlib==3.8.4

Pinning exact versions (not just package names) is what prevents the
'works locally, fails on deploy' problem the reviewer flagged —
SimpleITK and numpy version mismatches are the most common pyradiomics
build failure cause.

**6.6 Keeping It 'Always Warm' (Optional Extra Layer)**

Hugging Face Spaces' free CPU tier is far more reliable than Streamlit
Cloud's sleep policy, but for absolute certainty before a panel demo or
interview, add a simple uptime ping as a safety net:

- Use a free service like UptimeRobot or cron-job.org to ping your
  Space's URL every few hours — this is the basic 'AIOps-style'
  monitoring approach: lightweight, free, and requires no infrastructure
  of your own

- This is optional insurance on top of Hugging Face's already-reliable
  hosting — not a replacement for choosing the right platform

**7. ABLATION STUDY — CORRECTED FOR FAIR COMPARISON**

All Stage 2 experiments (E0-E6) now use the SAME fixed patient subset —
those with both subtype labels and TOMPEI masks (counted in Section
5.2). This is the corrected, scientifically fair version of the ablation
table.

|                          |                                                                     |                                             |
|--------------------------|---------------------------------------------------------------------|---------------------------------------------|
| **Experiment**           | **What Changes**                                                    | **Dataset Used**                            |
| E0 — Exact Reproduction  | Single-view Xception + age + lesion type, image-wise split, 224x224 | TOMPEI-annotated subset only (for fairness) |
| E1 — Our Baseline        | EfficientNet-B3, patient-wise split, single view                    | Same fixed subset                           |
| E2 — Dual-View           | Add MLO+CC with View Attention (both uncropped)                     | Same fixed subset                           |
| E3 — Lesion Localisation | Add MLO lesion crop (real mask via MONAI CropForegroundd)           | Same fixed subset                           |
| E4 — +Radiomics          | Add radiomics branch from real-mask crop (Section 4.5 fix)          | Same fixed subset                           |
| E5 — +Gated Fusion       | Replace concatenation with Gated Fusion module                      | Same fixed subset                           |
| E6 — Full System         | All components together                                             | Same fixed subset                           |

|                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Note the deliberate change from V1: E0 also now runs on the TOMPEI-annotated subset, not the full dataset. This means your E0 AUC number may differ slightly from the published 88.87% purely due to the smaller, different patient subset — note this in your results table as 'E0 (re-run on fair subset)' vs. 'Published baseline (full dataset, for reference)' so both numbers are visible and the comparison stays honest. |

**7.1 Stage 1 + Stage 2 Combined AUC — Defined Calculation Method**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>V1 GAP: the target table presented 'Overall AUC ≥ 89%' as
if directly comparable to the baseline's single 5-class AUC, without
defining how two separate stage outputs combine into one
number.</strong></p>
<p>THE FIX — defined chaining procedure: for every test patient, run
Stage 1 first. If predicted Benign, the final label is Benign. If
predicted Malignant, feed the same patient into Stage 2 and take its
4-class prediction as the final label. This produces one 5-class
probability distribution per patient across the full label space
(Benign, LumA, LumB, HER2, TN), from which you compute one-vs-rest macro
AUC exactly as the baseline paper did. Use this chained number as your
single 'Overall AUC' to report against their 88.87% baseline.</p></td>
</tr>
</tbody>
</table>

> def get_chained_prediction(patient, stage1_model, stage2_model):
>
> stage1_probs = stage1_model.predict_proba(patient) \# \[P(benign),
> P(malignant)\]
>
> if stage1_probs\[0\] \> stage1_probs\[1\]:
>
> \# Benign — full probability mass on Benign class, 0 elsewhere
>
> return {'Benign': stage1_probs\[0\], 'LumA': 0, 'LumB': 0, 'HER2': 0,
> 'TN': 0}
>
> else:
>
> stage2_probs = stage2_model.predict_proba(patient) \# 4-class
>
> \# scale by stage1 malignant confidence for a calibrated joint
> probability
>
> return {
>
> 'Benign': stage1_probs\[0\],
>
> 'LumA': stage1_probs\[1\] \* stage2_probs\[0\],
>
> 'LumB': stage1_probs\[1\] \* stage2_probs\[1\],
>
> 'HER2': stage1_probs\[1\] \* stage2_probs\[2\],
>
> 'TN': stage1_probs\[1\] \* stage2_probs\[3\],
>
> }

**8. REVISED TIMELINE — WITH SLACK BUILT IN**

The reviewer correctly noted the original 10-week plan was tight,
especially around an internship starting in parallel. Weeks 3 (E0
reproduction) and 6-7 (radiomics + gated fusion) are the likely overflow
points — this version builds in slack explicitly rather than pretending
the schedule is fixed.

|          |                                                                                                                                                                     |                                                                                                                           |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Week** | **Tasks**                                                                                                                                                           | **Slack Note**                                                                                                            |
| Week 1   | TCIA account, download CMMD + TOMPEI-CMMD. Verify real XLSX column names (5.1). Run the Week 1 usable-patient count (5.2). Build CC/MLO pairing (5.3).              | Do not skip the column-name and patient-count verification — it changes downstream code                                   |
| Week 2   | Build MONAI pipeline (Section 4): JSON→mask→NIfTI, transform pipelines, CacheDataset. Patient-wise splits using verified subtype column. Decide label source (5.4). | —                                                                                                                         |
| Week 3   | E0: Reproduce baseline architecture from the paper's written description (no GitHub code available — Section 2.2). Run on the TOMPEI-annotated subset.              | BUFFER WEEK — if E0 isn't matching expected AUC by end of week, debug here before moving on, do not carry the bug forward |
| Week 4   | E1-E2: patient-wise split baseline + dual-view attention.                                                                                                           | —                                                                                                                         |
| Week 5   | Radiomics extraction using the REAL mask (Section 4.5) on the fixed subset only. Feature selection (top 20).                                                        | —                                                                                                                         |
| Week 6-7 | E3-E6: lesion crop, radiomics branch, gated fusion, full system. Complete ablation table.                                                                           | TWO-WEEK BUFFER — this is the most complex implementation block, expect it to run long                                    |
| Week 8   | GradCAM + SHAP. Generate figures including Luminal A vs B side-by-side comparison.                                                                                  | —                                                                                                                         |
| Week 9   | Write paper draft. Submit to MDPI Diagnostics.                                                                                                                      | —                                                                                                                         |
| Week 10  | Build and deploy Streamlit app to Hugging Face Spaces (Section 6). Record demo video.                                                                               | If earlier weeks slipped, simplify demo scope rather than rushing the paper                                               |

**9. QUICK REFERENCE**

**9.1 Key URLs**

- CMMD dataset: cancerimagingarchive.net/collection/cmmd/

- TOMPEI-CMMD dataset:
  cancerimagingarchive.net/analysis-result/tompei-cmmd/

- MONAI docs: docs.monai.io

- PyRadiomics docs: pyradiomics.readthedocs.io

- Hugging Face Spaces: huggingface.co/spaces

- 2025 baseline paper: doi.org/10.3390/diagnostics15080995 (code NOT
  public — see Section 2.2)

**9.2 Complete Install Command**

> pip install torch torchvision monai pydicom SimpleITK
>
> pillow numpy pandas scikit-learn tqdm
>
> pyradiomics shap grad-cam streamlit matplotlib openpyxl

**9.3 All Loopholes — Fixed Status**

|        |                                                                       |                        |
|--------|-----------------------------------------------------------------------|------------------------|
| **\#** | **Loophole**                                                          | **Fixed In**           |
| 1      | TOMPEI-CMMD is MLO-only, architecture didn't specify this             | Section 3.1, 3.2, 3.3  |
| 2      | Unfair ablation comparison (different patient subsets per experiment) | Section 3.4, Section 7 |
| 3      | Radiomics used a rectangle mask instead of real tumour shape          | Section 4.3-4.5        |
| 4      | No defined method to combine Stage 1+2 into one comparable AUC        | Section 7.1            |
| 5      | GitHub repo cited as reference doesn't actually exist publicly        | Section 2.2            |
| 6      | Split code assumed wrong column name for subtype label                | Section 5.1            |
| 7      | No CC/MLO pairing logic specified                                     | Section 5.3            |
| 8      | Label source inconsistency between original and corrected CMMD labels | Section 5.4            |
| 9      | PyRadiomics build failures on Streamlit Cloud                         | Section 6.2-6.5        |
| 10     | Tight 10-week timeline with no slack                                  | Section 8              |
| —      | Streamlit Community Cloud sleeps after inactivity                     | Section 6 (entire)     |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>FINAL NOTE</strong></p>
<p>This document reflects two full rounds of technical review. The
remaining unknowns are genuinely empirical — exactly how many patients
survive the TOMPEI-mask filter, exactly what AUC numbers the corrected
ablation study produces — and those can only be answered by running the
Week 1 verification steps and the experiments themselves. Everything
that could be caught on paper has been caught. From here, the work is
execution, not more re-planning.</p></td>
</tr>
</tbody>
</table>
