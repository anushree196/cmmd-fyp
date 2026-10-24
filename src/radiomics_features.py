"""Radiomics for Stage 2: hand-crafted features of the lesion, measured inside the REAL TOMPEI mask.

Feature classes (pyradiomics): firstorder (brightness statistics), shape2D (size and outline), glcm and glrlm
(texture: how grey levels sit next to each other / run along lines).

Physical scale: every PNG was resized by its own factor in task 02, so one PNG pixel covers a different
distance in different images (0.151-0.211 mm). Each image is therefore given its true pixel size
(DICOM ImagerPixelSpacing 0.0941 mm / the PNG scale factor), and pyradiomics resamples every lesion to the same
pixel size (0.211 mm, the coarsest present, so no image is enlarged). Shape features are then in millimetres
and comparable between patients.
"""
import numpy as np
import pandas as pd

DETECTOR_MM = 0.094090909  # ImagerPixelSpacing of every CMMD image (task 07 header check)
COMMON_MM = 0.211          # all lesions resampled to this pixel size
MARGIN_PX = 20             # crop the lesion's bounding box plus this margin before extraction

SETTINGS = {
    "force2D": True, "force2Ddimension": 0,           # 2D mammogram: features per slice, one slice
    "resampledPixelSpacing": [COMMON_MM, COMMON_MM, 0], # 0 = leave the (single) slice axis alone
    "interpolator": "sitkBSpline",
    "binWidth": 8,                                    # grey levels grouped in steps of 8 (8-bit image: 32 bins)
    "normalize": False,                               # all PNGs share the same 8-bit scale already
    "label": 1,
    "correctMask": True,                              # keep the mask on the image grid after resampling
}
CLASSES = ["firstorder", "shape2D", "glcm", "glrlm"]


def make_extractor():
    from radiomics import featureextractor, logger
    logger.setLevel(40)  # errors only
    ext = featureextractor.RadiomicsFeatureExtractor(**SETTINGS)
    ext.disableAllFeatures()
    for c in CLASSES:
        ext.enableFeatureClassByName(c)
    return ext


def crop_to_mask(img, mask, margin=MARGIN_PX):
    """Cut out the lesion's bounding box plus a margin (pyradiomics only looks inside the mask anyway)."""
    ys, xs = np.where(mask)
    y0, y1 = max(ys.min() - margin, 0), min(ys.max() + 1 + margin, mask.shape[0])
    x0, x1 = max(xs.min() - margin, 0), min(xs.max() + 1 + margin, mask.shape[1])
    return img[y0:y1, x0:x1], mask[y0:y1, x0:x1]


def extract_one(img, mask, png_scale, extractor):
    """Features of one lesion. img: uint8 PNG, mask: 0/255 PNG of the same size, png_scale from png_index."""
    import SimpleITK as sitk
    img, mask = crop_to_mask(img, mask > 0)
    spacing = DETECTOR_MM / png_scale  # true size of one PNG pixel in mm
    si = sitk.GetImageFromArray(img.astype(np.float32)[None])        # one slice: shape (1, H, W)
    sm = sitk.GetImageFromArray(mask.astype(np.uint8)[None])
    for s in (si, sm):
        s.SetSpacing((spacing, spacing, 1.0))
    out = extractor.execute(si, sm)
    feats = {}
    for k, v in out.items():
        if k.startswith("diagnostics"):
            continue
        v = np.asarray(v)
        # Elongation, Major/MinorAxisLength come from eigenvalues, which numpy returns as complex numbers with a
        # zero imaginary part. Keep the real part, but stop if an imaginary part is ever not zero.
        if np.iscomplexobj(v):
            assert abs(v.imag).max() < 1e-9, f"{k} has a non-zero imaginary part"
            v = v.real
        feats[k.replace("original_", "")] = float(v)
    feats["pixel_mm"] = spacing
    feats["mask_pixels_png"] = int(mask.sum())
    return feats


# ---------------------------------------------------------------- feature selection (TRAINING split only)

def shape_columns(df):
    return [c for c in df.columns if c.startswith("shape2D_")]


def fill_box_only_shapes(df, train_mask):
    """Box-only lesions have no real shape: their shape2D values are empty. Fill them with the median of the
    TRAINING breasts that are not box-only (so nothing is learned from val or test)."""
    cols = shape_columns(df)
    medians = df.loc[train_mask & ~df["has_box_only"], cols].median()
    out = df.copy()
    out[cols] = out[cols].fillna(medians)
    return out, medians.to_dict()


def select_features(train, feature_cols, target, k=20, corr_limit=0.9, constant_share=0.95, seed=42):
    """1. drop near-constant features, 2. rank by mutual information with the subtype, 3. walk down the ranking
    and drop any feature correlated |r| > corr_limit (Spearman) with one already kept, 4. keep the top k.
    Everything is computed on the training rows only. Returns the kept list and a table of every decision."""
    from sklearn.feature_selection import mutual_info_classif
    from sklearn.preprocessing import StandardScaler
    rows = []
    usable = []
    for c in feature_cols:
        v = train[c]
        top_share = v.value_counts(normalize=True).iloc[0]
        if v.std() == 0 or top_share > constant_share:
            rows.append({"feature": c, "decision": f"dropped: near-constant (top value {top_share:.0%} of rows)"})
        else:
            usable.append(c)
    X = StandardScaler().fit_transform(train[usable])
    mi = mutual_info_classif(X, train[target], random_state=seed, n_neighbors=3)
    order = [usable[i] for i in np.argsort(-mi)]
    mi_of = dict(zip(usable, mi))
    corr = train[usable].corr(method="spearman").abs()
    kept = []
    for c in order:
        clash = [o for o in kept if corr.loc[c, o] > corr_limit]
        if clash:
            rows.append({"feature": c, "mi": mi_of[c], "decision": f"dropped: |r| {corr.loc[c, clash[0]]:.2f} with {clash[0]}"})
        elif len(kept) < k:
            kept.append(c)
            rows.append({"feature": c, "mi": mi_of[c], "decision": f"SELECTED (rank {len(kept)})"})
        else:
            rows.append({"feature": c, "mi": mi_of[c], "decision": "not in the top k"})
    return kept, pd.DataFrame(rows)
