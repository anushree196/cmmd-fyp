# Task 08 — Stage 2 ablation (E0–E6)

Baseline: Ben Rabah et al., *Diagnostics* 2025, 15, 995. Their code: https://github.com/serag-ai/Multimodal-BC-Classifier (public; checked 2026-10-24; read for the method, no code copied — it has no licence).
Test scored once for all experiments at 2026-10-24 11:58:57 (forced re-run: False). All numbers below are TEST unless marked validation. 95% CIs: bootstrap over patients.

## 1. The leak ladder (E0 runs, 5 classes, test; average of 3 seeds)

| run | what changes | test images | micro AUC | macro AUC | Benign | LumA | LumB | HER2 | TN | ACC | F1 (macro) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *paper (published)* | their protocol, full data | 406 | *0.889* | *≈0.794* | *1.00* | *0.67* | *0.74* | *0.78* | *0.78* | *0.638* | *0.52* |
| **E0-paperdata** | their full protocol: per-patient labels (4,040 img), leaky metadata, image-wise split | 405 | 0.859 (0.83–0.88) | 0.770 (0.74–0.80) | 1.000 | 0.714 | 0.755 | 0.735 | 0.646 | 0.548 | 0.452 |
| **E0** | our correct per-breast labels (2,590 img); still their leaky metadata and image-wise split | 260 | 0.920 (0.90–0.94) | 0.850 (0.82–0.88) | 1.000 | 0.821 | 0.826 | 0.830 | 0.773 | 0.638 | 0.469 |
| **E0-truemeta** | + real lesion types for benign (metadata leak removed) | 260 | 0.685 (0.64–0.73) | 0.632 (0.58–0.68) | 0.738 | 0.618 | 0.514 | 0.713 | 0.577 | 0.365 | 0.270 |
| **E0-patient** | E0 on our patient-wise split (leaky metadata kept) | 388 | 0.904 (0.87–0.93) | 0.810 (0.77–0.85) | 1.000 | 0.728 | 0.795 | 0.807 | 0.721 | 0.621 | 0.423 |

Controls (same test parts):

| run | micro AUC | macro AUC | Benign | ACC | F1 (macro) | precision (macro) | recall (macro) |
|---|---|---|---|---|---|---|---|
| *paper, images only* | *0.613* | | | *0.318* | *0.26* | *0.26* | *0.29* |
| E0-images | 0.689 (0.65–0.73) | 0.615 (0.56–0.67) | 0.643 | 0.369 | 0.276 | 0.267 | 0.302 |
| E0-meta | 0.902 (0.88–0.93) | 0.850 (0.82–0.88) | 1.000 | 0.577 | 0.382 | 0.341 | 0.485 |
| E0-meta-true | 0.614 (0.57–0.66) | 0.627 (0.58–0.67) | 0.638 | 0.242 | 0.180 | 0.203 | 0.335 |

Full metric set for every E0 run (test; ACC, precision / recall / F1 macro and weighted):

| run | ACC | P macro | R macro | F1 macro | P weighted | R weighted | F1 weighted |
|---|---|---|---|---|---|---|---|
| E0 | 0.638 | 0.470 | 0.481 | 0.469 | 0.656 | 0.638 | 0.642 |
| E0-truemeta | 0.365 | 0.275 | 0.281 | 0.270 | 0.406 | 0.365 | 0.379 |
| E0-images | 0.369 | 0.267 | 0.302 | 0.276 | 0.375 | 0.369 | 0.367 |
| E0-meta | 0.577 | 0.341 | 0.485 | 0.382 | 0.497 | 0.577 | 0.520 |
| E0-meta-true | 0.242 | 0.203 | 0.335 | 0.180 | 0.332 | 0.242 | 0.220 |
| E0-patient | 0.621 | 0.426 | 0.426 | 0.423 | 0.637 | 0.621 | 0.627 |
| E0-paperdata | 0.548 | 0.452 | 0.456 | 0.452 | 0.561 | 0.548 | 0.553 |

## 2. Stage 2 ablation E1–E6 (4 subtypes, same 671 patients, test = the same 101 patients)

| exp | adds | val macro AUC (mean ± std) | **test macro AUC** | test micro AUC | test LumA | test LumB | test HER2 | test TN |
|---|---|---|---|---|---|---|---|---|
| E1-224 | E1 at 224 px (bridge to E0) | 0.586 ± 0.014 (n=3) | **0.502 (0.41–0.60)** | 0.530 (0.46–0.61) | 0.581 (0.43–0.72) | 0.505 (0.39–0.62) | 0.551 (0.40–0.70) | 0.370 (0.17–0.60) |
| E1 | EfficientNet-B3, MLO, patient split, 512 px | 0.611 ± 0.043 (n=3) | **0.551 (0.47–0.64)** | 0.639 (0.56–0.71) | 0.558 (0.42–0.70) | 0.489 (0.37–0.61) | 0.688 (0.56–0.80) | 0.467 (0.29–0.66) |
| E2 | + CC with View Attention | 0.622 ± 0.013 (n=3) | **0.586 (0.49–0.68)** | 0.670 (0.60–0.74) | 0.545 (0.39–0.70) | 0.541 (0.43–0.66) | 0.635 (0.49–0.78) | 0.625 (0.40–0.85) |
| E3 | + MLO lesion crop | 0.586 ± 0.011 (n=3) | **0.590 (0.51–0.67)** | 0.561 (0.50–0.63) | 0.604 (0.44–0.75) | 0.485 (0.37–0.60) | 0.669 (0.54–0.79) | 0.602 (0.43–0.77) |
| E4 | + radiomics (20 + box flag) | 0.576 ± 0.017 (n=3) | **0.618 (0.54–0.69)** | 0.559 (0.49–0.63) | 0.615 (0.47–0.75) | 0.507 (0.39–0.62) | 0.687 (0.54–0.81) | 0.663 (0.48–0.84) |
| E5 | Gated Fusion | 0.590 ± 0.002 (n=3) | **0.644 (0.57–0.72)** | 0.605 (0.54–0.67) | 0.624 (0.49–0.76) | 0.509 (0.40–0.62) | 0.693 (0.56–0.81) | 0.751 (0.58–0.89) |
| E6 | E5 as 5-fold CV ensemble | 0.643 ± 0.034 (n=5) | **0.587 (0.51–0.66)** | 0.569 (0.50–0.64) | 0.611 (0.47–0.75) | 0.459 (0.35–0.57) | 0.675 (0.54–0.79) | 0.603 (0.42–0.79) |
| *paper (5-class model)* | | | | | *0.67* | *0.74* | *0.78* | *0.78* |

Test class sizes: LumA 21, LumB 51, HER2 19, TN 10 patients — per-class CIs are wide, TN especially.

Reading: best on validation is E6, best on test is E5; the validation and test rankings do not agree, and every E1–E6 test interval overlaps the others. On 101 test patients no single component is shown to help or hurt. The paper's per-class numbers come from its 5-class model under the leaky protocol (benign included as negatives), so they are not directly comparable with these 4-class AUCs.

## 3. Chained Stage 1 → Stage 2, one 5-class probability per breast (test)

Stage 1 = the frozen v2 ensemble (task 06); Stage 2 = E6. Soft chaining for every breast: P(benign) = 1 − p(malignant); P(subtype) = p(malignant) × Stage 2's subtype probability (master doc §7.1 without the hard gate, as decided). Benign breasts have no lesion mask, so their subtype probabilities are 1/4 each.
Set: 82 benign test breasts + 101 subtyped test patients. The other 96 Stage 1 test breasts (malignant with no subtype or no mask) cannot be given a 5-class label and are left out.

| | micro AUC | macro AUC | Benign | LumA | LumB | HER2 | TN |
|---|---|---|---|---|---|---|---|
| **ours, chained (test)** | 0.775 (0.72–0.82) | 0.724 (0.67–0.77) | 0.822 (0.76–0.88) | 0.707 (0.58–0.82) | 0.636 (0.55–0.72) | 0.799 (0.69–0.89) | 0.658 (0.53–0.79) |
| *paper (leaky protocol)* | *0.889* | *≈0.794* | *1.00* | *0.67* | *0.74* | *0.78* | *0.78* |

Caution: in this 5-class setting the 82 benign breasts are negatives for every subtype, and Stage 1 already pushes most of them down, so the chained subtype AUCs are higher than the 4-class ones in section 2 (same Stage 2 model). Compare like with like: section 2 against section 2, this table against the paper's 5-class numbers — which also benefit from the metadata leak (section 1).
