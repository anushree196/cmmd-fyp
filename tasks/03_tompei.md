# Task 03 — TOMPEI-CMMD masks + the real Stage 2 size  (runs on: laptop)

Goal: lesion masks aligned to our PNGs, and the **exact usable-patient count** for Stage 2 (Master doc §5.2).

## Steps
1. **[ANU]** Download TOMPEI-CMMD from cancerimagingarchive.net (search "TOMPEI-CMMD"; it is an "analysis result"
   for CMMD). It is small compared to CMMD. Put it in the folder set as `tompei_dir` in config.yaml.
2. Inspect the files with a script (print the file list, one example annotation's keys, 3 example points).
   Do NOT assume the format in the master doc (`cgPoints`, x/y) is right — confirm it. Find how an annotation
   links to a CMMD image (SOP Instance UID? patient + side + view? file name?) and record it.
3. Read the corrected left/right and view labels TOMPEI provides; compare with ours from task 01 and count
   disagreements. Decision already made: TOMPEI's corrected labels win, for all experiments.
4. Write `scripts/03_tompei_masks.py`: for each annotated MLO image, draw the **real polygon** (filled) on a
   canvas the size of the ORIGINAL DICOM, then apply the SAME crop box, flip and resize from `png_index.csv`.
   Save `data/masks1024/{same name as the PNG}_mask.png` (0/255).
5. QC: `reports/03_mask_overlay.png` — 16 random PNGs with the mask outline drawn in red. **[ANU]** check it.
6. Compute and print: patients with subtype label; patients with a TOMPEI mask; **intersection = Stage 2 set**;
   class counts in that set (LumA / LumB / HER2 / TN).

## Done when
- Masks line up with lesions on the overlay montage.
- `data/index/stage2_patients.csv` exists; PROGRESS.md records all counts (these numbers go into the report and PPT).
