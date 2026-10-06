# Task 03 — lesion masks and the Stage 2 set

Annotation files: 1385 (all MLO)  |  patients: 1363  |  masks made: 1385  |  failed: 0
Lesions outlined: 1773  |  lesions per breast: {1: 1069, 2: 271, 3: 26, 4: 14, 5: 3, 6: 1, 7: 1}
Lesion types present per breast: {'mass': 746, 'calc': 287, 'calc,mass': 238, 'FAD': 29, 'dist': 29, 'dist,mass': 18, 'FA': 17, 'calc,dist,mass': 8, 'calc,dist': 3, 'FAD,calc': 2, 'FA,mass': 2, 'FA,calc': 2, 'FAD,dist': 2, 'FA,calc,mass': 1, 'lipoma': 1}
Outlines of type 'Polyline' (treated as closed shapes like the rest): 53
Empty masks (outline entirely outside the PNG): 0
Outlined area cut off by the PNG crop box: none on 1380 masks, up to 1% on 0, 1-10% on 4, over 10% on 1 (max 0.131)
   most cut off: [('D1-1057 L', 0.1314), ('D1-0992 L', 0.0727), ('D2-0463 R', 0.0567), ('D2-0326 L', 0.0552), ('D2-0163 R', 0.0207)]
Mask area as a share of the PNG: min 0.0004, median 0.0264, max 0.368

## Stage 2 set

Patients with a subtype label: 749 (749 breasts, one per patient)
Patients with at least one TOMPEI mask (any class): 1363

Subtyped breasts by TOMPEI class and whether a mask exists:

| t_class   |   mask |   no mask |   All |
|:----------|-------:|----------:|------:|
| Exclusion |      0 |         3 |     3 |
| Invisible |      0 |        75 |    75 |
| Malignant |    671 |         0 |   671 |
| All       |    671 |        78 |   749 |

**Stage 2 set = subtype label AND mask AND TOMPEI class Malignant: 671 patients**
Subtyped breasts with a mask that TOMPEI recommends excluding (left out): 0 []
Stage 2 breasts with no CC image: 0

| subtype | patients with subtype | in Stage 2 set | lost |
|---|---|---|---|
| Luminal A | 152 | 140 | 12 |
| Luminal B | 376 | 335 | 41 |
| HER2-enriched | 135 | 126 | 9 |
| triple negative | 86 | 70 | 16 |
| **total** | 749 | 671 | 78 |

Why the 78 subtyped patients are lost: {'Invisible': 75, 'Exclusion': 3}
Stage 2 lesion types: {'mass': 363, 'calc,mass': 148, 'calc': 116, 'dist': 14, 'FAD': 8, 'dist,mass': 7, 'calc,dist,mass': 6, 'calc,dist': 3, 'FA,calc': 2, 'FAD,dist': 2, 'FA,mass': 1, 'FAD,calc': 1}
Stage 2 abnormality (CMMD): {'mass': 364, 'both': 219, 'calcification': 88}
Stage 2 age: 21 to 87, mean 50.2
Stage 2 patients whose subtype was moved to the other breast by TOMPEI's correction: 6 ['D2-0048', 'D2-0132', 'D2-0212', 'D2-0282', 'D2-0458', 'D2-0637']
