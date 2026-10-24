# Baseline paper: what it actually did (checked against the PDF, 24 Oct 2026)

Ben Rabah C., Sattar A., Ibrahim A., Serag A. *A Multimodal Deep Learning Model for the Classification of Breast Cancer Subtypes.* Diagnostics 2025, 15, 995. doi:10.3390/diagnostics15080995

## Their setup (copy exactly for E0)
| Item | Paper |
|---|---|
| Task | **5 classes in one model**: benign, LumA, LumB, HER2, TN (not a 4-class subtype model) |
| Data | CMMD, **4,056 images** from 1,775 patients. Images kept if age, "calcification type" and subtype (if malignant) were present (their Fig. 2) |
| Split | **Image-wise**, stratified by class: 72 / 18 / 10 → 2,920 / 730 / 406 images |
| Image | whole mammogram resized to 224×224, scaled to [0,1]. No crop, no lesion ROI |
| Image branch | ImageNet Xception → global average pooling → Dense → ReLU → Dropout → 512 |
| Metadata branch | age binarised (<40 = 0, ≥40 = 1), tumour class 0 none / 1 mass / 2 calcification / 3 both → Dense + ReLU + Dropout → 32 |
| Fusion and head | concatenate (544) → 3 dense layers with ReLU → softmax |
| Training | Adam lr 1e-3, batch 64, 10 epochs, class-weighted cross-entropy, A100 |
| Metrics | ACC, PRE, REC, F1, ROC/AUC |

## Their numbers
| | ACC | AUC | F1 | PRE | REC |
|---|---|---|---|---|---|
| Images only | 31.78% | 61.3% | 26% | 26% | 29% |
| Images + metadata | 63.79% | **88.87%** | 52% | 46% | 64% |

Per class, one-vs-rest:

| Model | Benign | LumA | LumB | HER2 | TN |
|---|---|---|---|---|---|
| Images only (Fig. 8a) | n/a | 54% | 46% | n/a | 69% |
| Multimodal (Fig. 8b + text) | **100%** | 67% | 74% | 78% | 78% |

Other results:
- **Backbones (Table 1):** VGG16 84.45, ResNet50 83.63, EfficientNetB7 84.57, InceptionV3 85.87, Xception 88.87.
- **Resolution test:** accuracy fell to 54.68% at 512 px and 43.6% at 1024 px. They blame overfitting.

## Weak points we can test (these become our paper's contributions)
1. **The image-wise split leaks.** The same patient's CC and MLO, and both breasts, can land in train and test. They chose it because TN is rare.
2. **The headline 88.87% is probably a micro-average.** The macro average of their per-class AUCs is about (100+67+74+78+78)/5 ≈ **79%**. Micro-averaging is pulled up by the easy benign class. We report both, and say which is which.
3. **Benign AUC 100% is a red flag.** No mammography model separates benign from malignant perfectly; our honest Stage 1 is 0.79. A likely cause is a shortcut in the metadata or the cohort: D1 vs D2 patients may be coded differently, or "tumour class = none" may only occur in one group. A **metadata-only model** tests this cheaply.
4. **They say CMMD has no lesion localisation.** TOMPEI-CMMD provides it. That is what makes our lesion crop (E3) and radiomics (E4) possible.
5. **Their future-work list:** breast density, attention mechanisms, explainability (saliency maps), multi-scale/high-res inputs. Our plan covers each of these:
   - View Attention (E2)
   - Grad-CAM/SHAP (task 09)
   - density subgroups from TOMPEI
   - 512 px with crops
6. **Code.** The paper links github.com/serag-ai/Multimodal-BC-Classifier, but the data statement says "shared upon acceptance". Check whether it is public now. If it is, use it for E0.

## How our results should be framed
"Under the baseline's own protocol we reproduce roughly X. Under a patient-wise split the same model drops to Y. Our additions (dual view, lesion crop, radiomics, gated fusion) recover Z, measured honestly."
The drop from X to Y is a finding in itself, not a failure.
