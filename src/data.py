"""Data for training: read a split CSV, load the CC and MLO PNGs of each breast, augment, batch.

One sample = one breast = {"cc": image, "mlo": image, "clin": [age], "label": 0 benign / 1 malignant}.
Images are 1 x size x size, values 0..1. MONAI's CacheDataset keeps the loaded images in memory, so the PNGs
are read from disk only once per run; the random augmentations are applied fresh every epoch.
"""
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from monai import transforms as T
from monai.data import CacheDataset

# Age is centred with fixed numbers (not fitted on any split, so nothing leaks): CMMD ages are 17-87, mean ~47.
AGE_MEAN, AGE_STD = 50.0, 12.0
VIEWS = ["cc", "mlo"]


def find_data_root(given=None):
    """The folder that holds png1024/ and splits/: given on the command line, found on Kaggle, or data/."""
    if given:
        return Path(given)
    kaggle = Path("/kaggle/input")
    if kaggle.exists():
        for p in kaggle.rglob("png1024"):
            if p.is_dir():
                return p.parent
    return Path("data")


def load_view(path, size):
    """One PNG -> float32 array (1, size, size), values 0..1.

    The image is scaled to `size` pixels tall with its shape kept (no stretching), then padded with black on the
    right to make it square. After task 02 every breast faces the same way with the chest wall on the left, so
    the breast always starts at the left edge.
    """
    im = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if im is None:
        raise FileNotFoundError(path)
    width = min(size, max(1, round(im.shape[1] * size / im.shape[0])))
    im = cv2.resize(im, (width, size), interpolation=cv2.INTER_AREA)
    out = np.zeros((size, size), np.float32)
    out[:, :width] = im / 255.0
    return out[None]  # add the channel axis: (1, size, size)


class LoadPair:
    """First transform: turn the two PNG paths of a sample into images. Not random, so CacheDataset caches it."""

    def __init__(self, png_dir, size):
        self.png_dir, self.size = Path(png_dir), size

    def __call__(self, item):
        item = dict(item)
        for v in VIEWS:
            item[v] = load_view(self.png_dir / item[v], self.size)
        return item


def augmentations(size, strength="light"):
    """Random changes for TRAINING images only. No flips: orientation was standardised in task 02.
    Each view gets its own random values (the CC and MLO are different pictures).

    light  = Stage 1 v1 (task 06): rotation up to ~10 degrees, +-10% size, +-20 px shift, mild contrast.
    strong = Stage 1 v2 recipe search: random resized crop keeping 80-100% of the area, rotation up to
             +-15 degrees, stronger contrast, and brightness changes.
    """
    out = []
    for v in VIEWS:
        if strength == "light":
            out += [
                T.RandAffined(keys=v, prob=0.7, rotate_range=0.17, scale_range=0.10, translate_range=(20, 20),
                              padding_mode="zeros"),
                T.RandAdjustContrastd(keys=v, prob=0.5, gamma=(0.8, 1.25)),
                T.RandScaleIntensityd(keys=v, prob=0.5, factors=0.10),
            ]
        else:
            out += [
                # random resized crop: each side keeps 89.4-100% (area 80-100%), then back to size x size
                T.RandScaleCropd(keys=v, roi_scale=0.894, max_roi_scale=1.0, random_size=True),
                T.Resized(keys=v, spatial_size=(size, size)),
                T.RandAffined(keys=v, prob=0.7, rotate_range=0.26, translate_range=(0.04 * size, 0.04 * size),
                              padding_mode="zeros"),        # rotation up to +-15 degrees, shift up to 4%
                T.RandAdjustContrastd(keys=v, prob=0.5, gamma=(0.7, 1.4)),   # contrast (gamma curve)
                T.RandScaleIntensityd(keys=v, prob=0.5, factors=0.15),      # contrast (x 0.85-1.15)
                T.RandShiftIntensityd(keys=v, prob=0.5, offsets=0.08),      # brightness (+-0.08)
            ]
    return out


def to_records(df):
    """Split CSV rows -> the list of dicts MONAI datasets take."""
    return [{"cc": r.png_cc, "mlo": r.png_mlo, "clin": np.array([(r.age - AGE_MEAN) / AGE_STD], np.float32),
             "label": int(r.label), "patient_id": r.patient_id, "side": r.side} for r in df.itertuples()]


def make_dataset(df, data_root, size, train, cache_rate=1.0, workers=0, aug="light"):
    steps = [LoadPair(Path(data_root) / "png1024", size)]
    if train:
        steps += augmentations(size, aug)
    steps += [T.EnsureTyped(keys=VIEWS, track_meta=False)]  # plain torch tensors
    return CacheDataset(to_records(df), T.Compose(steps), cache_rate=cache_rate, num_workers=workers or None,
                        progress=False)


def read_split(data_root, stage, limit=0, seed=42):
    """The split CSV of a stage. With --limit N (local testing) keep N breasts per split, half of each class."""
    df = pd.read_csv(Path(data_root) / "splits" / f"stage{stage}.csv")
    if "label" in df:
        df["label"] = df["label"].astype(int)  # stored as 0.0 / 1.0 in the CSV
    if limit:
        k = max(1, limit // 2)
        df = pd.concat([g.sample(min(len(g), k), random_state=seed) for _, g in df.groupby(["split", "label"])])
    return df.reset_index(drop=True)
