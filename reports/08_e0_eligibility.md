# Task 08 — E0: eligible images vs the baseline paper's 4,056

| rule | images | note |
|---|---|---|
| **A. ours**: each breast labelled by its own CMMD row (TOMPEI side corrections), benign or with a subtype, TOMPEI exclusions dropped | **2590** | 1223 patients; used for E0 |
| B. same with the original CMMD labels, nothing dropped | 2610 | |
| **C. patient level**: every image of a subtyped patient gets the subtype, every image of a benign-only patient is benign | **4040** | closest to the paper's 4,056 (difference 16) |

Under rule C, 1458 images are of a breast with **no** CMMD label of its own (the other breast of a subtyped patient) but are still trained and tested as a subtype. The paper's folder-building step is not in its published code, so rule C is our best explanation, not a certainty; the last 16 images are not explained.

Rule A per class (images): Benign 1098, HER2 270, LumA 300, LumB 750, TN 172
Rule C per class (images): {'Luminal B': 1500, 'Benign': 1052, 'Luminal A': 606, 'HER2-enriched': 538, 'triple negative': 344}

## E0 image-wise split (the paper's procedure: 72%, then 64.28% / 35.72%, stratified by class, seed 42)

| y      |   train |   val |   test |
|:-------|--------:|------:|-------:|
| Benign |     790 |   197 |    111 |
| HER2   |     194 |    49 |     27 |
| LumA   |     216 |    54 |     30 |
| LumB   |     540 |   135 |     75 |
| TN     |     124 |    31 |     17 |

Paper: 2,920 / 730 / 406. Ours: 1864 / 466 / 260.
Leakage of the image-wise split: 576 of 1223 patients have images in more than one part; 198 of 260 test images belong to a patient who also has an image in train.

## The paper's metadata encoding (from its public code, `data_split_publish.ipynb`)

Tumour class is set from the folder each image is read from: every image in the Benign folder gets 0 ("None"), malignant images get 1 mass / 2 calcification / 3 both. In CMMD, benign breasts have a real lesion type too:

| | tumour class 0 | 1 mass | 2 calcification | 3 both |
|---|---|---|---|---|
| benign images, paper encoding | 1098 | 0 | 0 | 0 |
| benign images, true encoding | 0 | 812 | 126 | 160 |

With the paper's encoding, tumour class 0 occurs for 1098 images, all benign (0 malignant): the metadata input reveals the benign label. This explains the paper's benign AUC of 100% and much of the jump from 61.3% (images only) to 88.87% (with metadata).

Also from the code: the reported 88.87% is Keras' `AUC()` on one-hot labels, i.e. a **micro** average; the model used is the last of 10 epochs (early stopping has patience 20 and never triggers).
