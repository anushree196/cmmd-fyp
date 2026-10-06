# Audit of tasks 01–04 (before the Kaggle upload)

Everything below is recounted from the files and the two original spreadsheets by `scripts/05_audit.py`.

## Result

**No problems found.** Every count in PROGRESS.md recounts exactly, there is no leakage, all 2601 breasts trace back to the raw spreadsheets, and every PNG and mask opens and is sane.

Not problems, but worth knowing (details in the sections below):

- 60 TOMPEI annotations are boxes, not traced outlines; all are architectural distortions ('dist'). 14 Stage 2 breasts have only a box. Shape radiomics on those describe the box, not the lesion.
- 6 masks overhang the skin edge (under 90% of the area on breast pixels); they are such boxes, not misplaced masks (`reports/05_audit_masks_off_breast.png`).
- 1 subtyped patient (D2-0220) has an outlined cancer but is correctly not in Stage 2: the subtype belongs to the other breast.
- The splits were redone during this audit so TOMPEI's Normal and Invisible subgroups are spread evenly (section 6 shows before and after). The counts in section 1 are checked against the new split.

## 1. Counts: recounted against PROGRESS.md

| what | PROGRESS.md | recounted | |
|---|---|---|---|
| DICOM files in the CMMD download | 5202 | 5202 | ok |
| PNG files | 5202 | 5202 | ok |
| patients (PNG file names) | 1775 | 1775 | ok |
| breasts (PNG file names) | 2601 | 2601 | ok |
| mask files | 1385 | 1385 | ok |
| patients with a mask | 1363 | 1363 | ok |
| CMMD sheet rows | 1872 | 1872 | ok |
| CMMD benign rows | 556 | 556 | ok |
| CMMD malignant rows | 1316 | 1316 | ok |
| CMMD subtyped patients | 749 | 749 | ok |
| TOMPEI sheet rows | 2601 | 2601 | ok |
| TOMPEI Malignant | 1167 | 1167 | ok |
| TOMPEI Normal | 1054 | 1054 | ok |
| TOMPEI Benign | 215 | 215 | ok |
| TOMPEI Invisible | 140 | 140 | ok |
| TOMPEI Exclusion | 25 | 25 | ok |
| TOMPEI annotation files | 1385 | 1385 | ok |
| TOMPEI lesions | 1773 | 1773 | ok |
| pairs.csv rows | 2601 | 2601 | ok |
| breasts without CMMD label | 729 | 729 | ok |
| labelled breasts TOMPEI excludes | 16 | 16 | ok |
| Stage 1 breasts | 1856 | 1856 | ok |
| Stage 1 patients | 1762 | 1762 | ok |
| Stage 1 benign | 549 | 549 | ok |
| Stage 1 malignant | 1307 | 1307 | ok |
| Stage 1 Invisible cancers | 140 | 140 | ok |
| Stage 1 benign with TOMPEI Normal | 342 | 342 | ok |
| Stage 2 patients | 671 | 671 | ok |
| Stage 2 Luminal A | 140 | 140 | ok |
| Stage 2 Luminal B | 335 | 335 | ok |
| Stage 2 HER2-enriched | 126 | 126 | ok |
| Stage 2 triple negative | 70 | 70 | ok |
| Stage 1 patients per split | (1233, 264, 265) | (1233, 264, 265) | ok |
| Stage 1 breasts per split | (1299, 278, 279) | (1299, 278, 279) | ok |
| Stage 1 benign per split | (385, 82, 82) | (385, 82, 82) | ok |
| Stage 1 malignant per split | (914, 196, 197) | (914, 196, 197) | ok |
| Stage 2 patients per split | (469, 101, 101) | (469, 101, 101) | ok |
| E0 images per split | (966, 241, 135) | (966, 241, 135) | ok |

Cross-checks between files:

- ok: every PNG file name matches {patient}_{L|R}_{CC|MLO}_...
- ok: PNG folder holds exactly the files listed in png_index.csv
- ok: mask folder holds exactly the files listed in pairs.csv
- ok: every DICOM path in png_index.csv exists and is used once
- ok: every PNG is used by exactly one breast in pairs.csv
- ok: stage1.csv is exactly the in_stage1 rows of pairs.csv
- ok: stage2.csv is exactly the in_stage2 rows of pairs.csv
- ok: every Stage 2 breast is also a Stage 1 breast
- ok: Stage 2 has one breast per patient, each with a mask and a subtype
- ok: E0 images are exactly the CC + MLO of the Stage 2 breasts
- ok: Stage 1 has no missing label, age, CC or MLO
- ok: no Stage 1 breast is a TOMPEI Exclusion
- ok: git tracks no data, DICOM, mask or weight files

Stage 2 recounted another way: subtyped patients with any outlined TOMPEI-Malignant breast = 672; Stage 2 has 671. Difference: ['D2-0220']
  - D2-0220: CMMD rows and TOMPEI class per side (side, CMMD class, subtype, TOMPEI) = [('L', 'Malignant', nan, 'Malignant'), ('R', 'Malignant', 'Luminal B', 'Exclusion')]. The subtype belongs to a breast with no outline; the outlined malignant breast is a second cancer with no subtype label, so leaving the patient out is correct.

## 2. Leakage

- Stage 1 patients in more than one split: 0
- Stage 2 patients in more than one split: 0
- Patients shared between the train, val and test sets (Stage 1): 0
- Stage 2 patients found in stage1.csv: 671 of 671; with a different split there: 0
- Splits used: Stage 1 ['test', 'train', 'val'], rows with no split: 0; Stage 2 rows with no split: 0
- Images appearing in two Stage 1 splits: 0
- E0 (image-wise on purpose): 282 of 671 patients have images in different splits. Expected and intended for E0 only.

## 3. Labels: raw spreadsheets → pairs.csv

20 random breasts (seed 2026), each compared field by field with the raw CMMD and TOMPEI sheets:

| breast | CMMD sheet (class / subtype / age / abnormality) | TOMPEI sheet (class / density / BI-RADS / lesions) | annotation file | pairs.csv (class / subtype / TOMPEI / mask / Stage 1 / Stage 2 / split) | result |
|---|---|---|---|---|---|
| D1-0161 L | Malignant / – / 38 / calcification | Malignant / heterogeneous dense / 3 / 1 | yes | Malignant / – / Malignant / yes / yes / no / train | match |
| D1-0388 L | Malignant / – / 74 / both | Malignant / fatty / 5 / 2 | yes | Malignant / – / Malignant / yes / yes / no / train | match |
| D1-0606 R | Malignant / – / 39 / both | Malignant / heterogeneous dense / 5 / 1 | yes | Malignant / – / Malignant / yes / yes / no / val | match |
| D1-0744 R | Benign / – / 43 / mass | Benign / heterogeneous dense / 4 / 1 | yes | Benign / – / Benign / yes / yes / no / train | match |
| D1-0754 R | Benign / – / 42 / mass | Normal / heterogeneous dense / 1 / 0 | no | Benign / – / Normal / no / yes / no / val | match |
| D1-0783 L | Benign / – / 39 / mass | Normal / extremely dense / 1 / 0 | no | Benign / – / Normal / no / yes / no / train | match |
| D1-0839 L | Benign / – / 48 / mass | Normal / heterogeneous dense / 1 / 0 | no | Benign / – / Normal / no / yes / no / train | match |
| D1-0947 R | Benign / – / 33 / mass | Normal / extremely dense / 1 / 0 | no | Benign / – / Normal / no / yes / no / train | match |
| D1-1545 L | Malignant / – / 41 / mass | Malignant / extremely dense / 4 / 1 | yes | Malignant / – / Malignant / yes / yes / no / val | match |
| D2-0059 L | no row for this side | Exclusion / heterogeneous dense / 1 / 0 | no | – / – / Exclusion / no / no / no / val | match |
| D2-0106 L | Malignant / Luminal B / 43 / both | Malignant / heterogeneous dense / 5 / 2 | yes | Malignant / Luminal B / Malignant / yes / yes / yes / train | match |
| D2-0107 R | Malignant / Luminal B / 42 / both | Malignant / heterogeneous dense / 5 / 2 | yes | Malignant / Luminal B / Malignant / yes / yes / yes / train | match |
| D2-0286 L | Malignant / Luminal A / 47 / both | Malignant / extremely dense / 3 / 1 | yes | Malignant / Luminal A / Malignant / yes / yes / yes / train | match |
| D2-0461 L | no row for this side | Normal / extremely dense / 1 / 0 | no | – / – / Normal / no / no / no / train | match |
| D2-0476 L | Malignant / HER2-enriched / 46 / mass | Malignant / heterogeneous dense / 5 / 2 | yes | Malignant / HER2-enriched / Malignant / yes / yes / yes / train | match |
| D2-0481 L | Malignant / Luminal B / 42 / mass | Malignant / heterogeneous dense / 4 / 1 | yes | Malignant / Luminal B / Malignant / yes / yes / yes / train | match |
| D2-0629 R | Malignant / HER2-enriched / 55 / mass | Malignant / heterogeneous dense / 4 / 1 | yes | Malignant / HER2-enriched / Malignant / yes / yes / yes / train | match |
| D2-0653 L | no row for this side | Normal / heterogeneous dense / 1 / 0 | no | – / – / Normal / no / no / no / train | match |
| D2-0732 R | Malignant / Luminal B / 33 / mass | Malignant / extremely dense / 5 / 1 | yes | Malignant / Luminal B / Malignant / yes / yes / yes / train | match |
| D2-0743 L | no row for this side | Normal / heterogeneous dense / 1 / 0 | no | – / – / Normal / no / no / no / train | match |

Mismatches in the 20: 0
Same comparison on all 2601 breasts: 0 mismatches.

Breasts whose CMMD label comes from the other side's row (10; these are the only labels that do not come from the breast's own CMMD row):
- label read from D1-0252 R (moved: TOMPEI note 'Reversed left and right', class there no such side)
- label read from D1-0690 R (moved: TOMPEI note 'Reversed left and right', class there no such side)
- label read from D1-0711 L (moved: TOMPEI note 'Reversed left and right', class there no such side)
- label read from D2-0048 L (moved: TOMPEI note 'Reversed left and right', class there Normal)
- label read from D2-0132 R (moved: TOMPEI note 'Reversed left and right', class there Normal)
- label read from D2-0153 R (moved: TOMPEI note 'Reversed left and right', class there Normal)
- label read from D2-0212 R (moved: TOMPEI note 'Reversed left and right', class there Normal)
- label read from D2-0282 R (moved: TOMPEI note 'nan', class there Normal)
- label read from D2-0458 R (moved: TOMPEI note 'nan', class there Normal)
- label read from D2-0637 L (moved: TOMPEI note 'Reversed left and right', class there Normal)

CMMD rows: 1872; breasts in pairs.csv carrying a CMMD label: 1872 (every CMMD row is used exactly once).
Images whose side differs from the DICOM tag: 16 in 8 patients (['D1-0252', 'D1-0690', 'D1-0711', 'D1-0999', 'D2-0041', 'D2-0224', 'D2-0229', 'D2-0642']).

## 4. Files: every PNG and mask opened

PNGs opened: 5202

- do not open: 0
- not 8-bit greyscale: 0
- size differs from png_index.csv: 0
- blank (all black): 0
- all white, or nearly (mean above 250): 0
- flat (almost no contrast, std below 2): 0
- less than 10% of the image is breast: 0
- brightness (mean grey level) across PNGs: min 14.8, median 42.2, max 117.1
- brightest pixel per PNG: lowest 116, median 228
- share of each PNG that is breast (non-black): min 0.29, median 0.68, max 0.92
- three dimmest PNGs (lowest brightest-pixel): [('D2-0720_L_MLO', 116), ('D2-0700_L_MLO', 124), ('D2-0697_R_MLO', 130)]

Masks opened: 1385

- do not open: 0
- size differs from their MLO PNG: 0
- contain values other than 0 and 255: 0
- empty (no lesion pixels): 0
- all white, or more than half the image: 0
- less than 90% of the lesion area lies on breast pixels: 6
- lesion area as a share of the image: min 0.0004, median 0.0264, max 0.368
- share of lesion area lying on breast pixels: min 0.683, median 1.000
- masks under 90% on breast: [('D1-1057_L', 0.683), ('D2-0463_R', 0.825), ('D2-0667_L', 0.86), ('D2-0554_R', 0.871), ('D2-0622_R', 0.888), ('D2-0078_L', 0.893)]
  Picture of these: `reports/05_audit_masks_off_breast.png`.

Box-shaped annotations (6 points or fewer, a rectangle instead of a traced outline): 60 of 1773 lesions, in 60 of 1385 annotated breasts.
- lesion types of the boxes: {'dist': 60}
- Stage 2 breasts with at least one box: 32 of 671; where every lesion is a box: 14 (train / val / test: [10, 2, 2])

## 5. Picture

`reports/05_audit_montage.png`: 16 random Stage 2 **test** breasts (seed 2026). Each cell is CC | MLO with the lesion outline in red | the mask itself, titled patient, side (corrected) and subtype.
Breasts shown: [('D2-0739', 'R', 'Luminal B'), ('D2-0074', 'L', 'Luminal B'), ('D2-0014', 'L', 'Luminal B'), ('D2-0132', 'L', 'Luminal A'), ('D2-0675', 'L', 'Luminal B'), ('D2-0096', 'R', 'Luminal B'), ('D2-0064', 'L', 'Luminal B'), ('D2-0620', 'R', 'HER2-enriched'), ('D2-0578', 'R', 'triple negative'), ('D2-0173', 'R', 'Luminal B'), ('D2-0565', 'R', 'Luminal A'), ('D2-0728', 'R', 'Luminal B'), ('D2-0342', 'R', 'HER2-enriched'), ('D2-0283', 'L', 'Luminal B'), ('D2-0337', 'R', 'Luminal A'), ('D2-0737', 'R', 'Luminal B')]

## 6. How evenly the subgroups are spread over the splits (Stage 1 breasts)

| subgroup | train | val | test | all |
|---|---|---|---|---|
| benign breasts that are TOMPEI Normal (no visible lesion) | 242 of 385 (62.9%) | 50 of 82 (61.0%) | 50 of 82 (61.0%) | 342 of 549 (62.3%) |
| malignant breasts that are TOMPEI Invisible | 99 of 914 (10.8%) | 21 of 196 (10.7%) | 20 of 197 (10.2%) | 140 of 1307 (10.7%) |
| breasts that are dense | 1120 of 1299 (86.2%) | 243 of 278 (87.4%) | 234 of 279 (83.9%) | 1597 of 1856 (86.0%) |

The same shares in the split as it was BEFORE the re-split:

| subgroup | train | val | test |
|---|---|---|---|
| benign breasts that are TOMPEI Normal | 234 of 375 (62.4%) | 45 of 84 (53.6%) | 63 of 90 (70.0%) |
| malignant breasts that are TOMPEI Invisible | 92 of 914 (10.1%) | 26 of 196 (13.3%) | 22 of 197 (11.2%) |

Patients whose split changed in the re-split: 610 of 1762. Nothing had been trained yet, so no result depends on the old split.

| Stage 2 subtype | train | val | test |
|---|---|---|---|
| Luminal A | 98 | 21 | 21 |
| Luminal B | 234 | 50 | 51 |
| HER2-enriched | 88 | 19 | 19 |
| triple negative | 49 | 11 | 10 |
