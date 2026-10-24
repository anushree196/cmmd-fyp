"""E0 family: the baseline paper (Ben Rabah et al., Diagnostics 2025), re-implemented in PyTorch from its public
code (github.com/serag-ai/Multimodal-BC-Classifier, notebooks uploaded 2026-04-13; read, not copied: no licence).

One 5-class model: Benign, HER2, LumA, LumB, TN (the paper's class order). Every sample is ONE image.

What the paper's code does, and what we copy:
  image     whole mammogram (no crop, not mirrored) squashed to 224 x 224, values /255 -> 0..1, grey copied into
            3 channels, no other normalisation
  encoder   ImageNet Xception, all layers frozen except the last 20 Keras layers (the exit flow)
  image     global average pool -> Dense 512 + ReLU -> Dropout 0.3
  metadata  2 numbers: age (<40 -> 0, >=40 -> 1) and "tumour class" (0 none, 1 mass, 2 calcification, 3 both),
            -> Dense 32 + ReLU -> Dropout 0.3
  head      concatenate -> Dense 256 + ReLU -> Dense 128 + ReLU -> 5 classes (softmax)
  training  Adam lr 1e-3, cross-entropy with 'balanced' class weights, batch 64, 10 epochs, learning rate halved
            after 5 epochs without a lower val loss; the model of the LAST epoch is used

What the paper's code does that we do NOT copy, and why:
  - Labels per patient: their image count (4,056) matches labelling every image of a subtyped patient with the
    subtype, including the other, unlabelled breast (4,040 images that way). We label each breast with its own
    CMMD row (TOMPEI side corrections, TOMPEI exclusions dropped): 2,590 images.
  - Their "tumour class" is set by the folder an image came from: EVERY benign image gets 0 ("none"), every
    malignant one 1-3. That makes the metadata reveal the benign label. We keep their encoding for the exact
    copy (meta="paper") and add the honest version (meta="true": the CMMD lesion type for benign breasts too).
"""
import json, time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import timm
import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset

CLASSES = ["Benign", "HER2", "LumA", "LumB", "TN"]
CLASS_OF_SUBTYPE = {"HER2-enriched": 1, "Luminal A": 2, "Luminal B": 3, "triple negative": 4}
TUMOUR = {"mass": 1, "calcification": 2, "both": 3}
SIZE = 224


# ---------------------------------------------------------------- data

def build_table(data_root):
    """One row per IMAGE: every CC and MLO of every Stage 1 breast that is benign or has a subtype."""
    root = Path(data_root)
    s1 = pd.read_csv(root / "splits" / "stage1.csv")
    s1["label"] = s1["label"].astype(int)
    keep = s1[(s1["label"] == 0) | s1["subtype"].notna()].copy()
    keep["y"] = [0 if l == 0 else CLASS_OF_SUBTYPE[s] for l, s in zip(keep["label"], keep["subtype"])]
    keep["age_bin"] = (keep["age"] >= 40).astype(np.float32)
    keep["tumour_true"] = keep["abnormality"].map(TUMOUR).astype(np.float32)
    keep["tumour_paper"] = np.where(keep["y"] == 0, 0.0, keep["tumour_true"]).astype(np.float32)
    rows = pd.concat([keep.assign(view="CC", png=keep["png_cc"]), keep.assign(view="MLO", png=keep["png_mlo"])])
    rows = rows.rename(columns={"split": "split_patient"})
    cols = ["png", "patient_id", "side", "view", "y", "age_bin", "tumour_true", "tumour_paper", "split_patient",
            "t_class", "dense", "subtype"]
    return rows[cols].sort_values("png").reset_index(drop=True)


def build_table_paperdata(data_root):
    """E0-paperdata: the paper's own data protocol, as far as we can reconstruct it (task 08 eligibility check).

    Labels per PATIENT, from the original CMMD sheet (no TOMPEI corrections, nothing excluded): every image of a
    patient with a subtype gets that subtype (including the other, unlabelled breast); every image of a
    benign-only patient is benign; patients who are malignant without a subtype are left out. -> 4,040 images
    (the paper has 4,056). Metadata as in the paper's code: tumour class 0 for benign, else the lesion type of
    the subtyped CMMD row, given to all of that patient's images."""
    idx = pd.read_csv(Path(data_root) / "index" / "png_index.csv")
    lab = idx[idx["clinical_match"] == "both"]
    pat = lab.groupby("patient_id").agg(
        subtype=("subtype", lambda s: s.dropna().iloc[0] if s.notna().any() else None),
        malignant=("classification", lambda c: (c == "Malignant").any()),
        age=("Age", "first"),
        lesion=("abnormality", lambda a: a.iloc[0]))
    sub_lesion = lab[lab["subtype"].notna()].groupby("patient_id")["abnormality"].first()
    pat["lesion"] = sub_lesion.reindex(pat.index).fillna(pat["lesion"])
    keep = pat[pat["subtype"].notna() | ~pat["malignant"]]
    rows = idx[idx["patient_id"].isin(keep.index)][["png", "patient_id", "side", "view"]].copy()
    p = keep.loc[rows["patient_id"]]
    rows["y"] = [0 if pd.isna(s) else CLASS_OF_SUBTYPE[s] for s in p["subtype"]]
    rows["age_bin"] = (p["age"].to_numpy() >= 40).astype(np.float32)
    rows["tumour_true"] = p["lesion"].map(TUMOUR).to_numpy().astype(np.float32)
    rows["tumour_paper"] = np.where(rows["y"] == 0, 0.0, rows["tumour_true"]).astype(np.float32)
    rows["split_patient"], rows["t_class"], rows["dense"], rows["subtype"] = None, None, None, p["subtype"].to_numpy()
    return rows.sort_values("png").reset_index(drop=True)


def imagewise_split(rows, seed=42):
    """The paper's split, done the way its code does it: 72% train, then the rest 64.28% / 35.72% -> val / test,
    both times stratified by class. Image-wise, so one patient's images can land in different parts."""
    idx = np.arange(len(rows))
    tr, tmp = train_test_split(idx, train_size=0.72, random_state=seed, stratify=rows["y"])
    va, te = train_test_split(tmp, train_size=0.6428, random_state=seed, stratify=rows["y"].iloc[tmp])
    split = np.empty(len(rows), dtype=object)
    split[tr], split[va], split[te] = "train", "val", "test"
    return split


def full_frame(png_path, rec):
    """Rebuild the whole, un-mirrored mammogram (as the paper used it) from our cropped, mirrored PNG.

    Our PNG is the breast crop (crop box from task 02), mirrored if the breast was on the right, and scaled.
    We put it back at its place on a black canvas of the original image size (at PNG scale), undo the mirror,
    then squash to 224 x 224 like the paper (cv2.resize, no aspect ratio kept)."""
    im = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
    if rec["flipped"]:
        im = im[:, ::-1]
    s = rec["scale"]
    canvas = np.zeros((round(rec["orig_h"] * s), round(rec["orig_w"] * s)), np.uint8)
    y0, x0 = round(rec["crop_y0"] * s), round(rec["crop_x0"] * s)
    h, w = min(im.shape[0], canvas.shape[0] - y0), min(im.shape[1], canvas.shape[1] - x0)
    canvas[y0:y0 + h, x0:x0 + w] = im[:h, :w]
    return cv2.resize(canvas, (SIZE, SIZE))  # default bilinear, as in the paper's preprocess_image


class ImageMetaDataset(Dataset):
    """Images are kept in memory as uint8 224 x 224 (about 50 KB each)."""

    def __init__(self, rows, images, meta):
        self.y = torch.tensor(rows["y"].to_numpy(), dtype=torch.long)
        self.images = images
        self.meta = torch.tensor(np.stack([rows["age_bin"], rows[f"tumour_{meta}"]], 1), dtype=torch.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        x = torch.from_numpy(self.images[i]).float().div(255).unsqueeze(0).expand(3, -1, -1)  # 0..1, 3 channels
        return x, self.meta[i], self.y[i]


def load_images(rows, data_root, png_index):
    idx = png_index.set_index("png")
    return [full_frame(Path(data_root) / "png1024" / p, idx.loc[p]) for p in rows["png"]]


# ---------------------------------------------------------------- model

# The last 20 Keras Xception layers = the last separable conv of block 12 + block 13 + block 14 (exit flow).
# In timm's port of the same network: block11's last SepConv + BN, block12, conv3/bn3, conv4/bn4.
TRAINABLE = ["block12", "conv3", "bn3", "conv4", "bn4"]


class PaperNet(nn.Module):
    def __init__(self, use_image=True, use_meta=True, pretrained=True, n_classes=5):
        super().__init__()
        self.use_image, self.use_meta = use_image, use_meta
        d = 0
        if use_image:
            self.encoder = timm.create_model("legacy_xception", pretrained=pretrained, num_classes=0)
            for p in self.encoder.parameters():
                p.requires_grad = False
            self.trainable = [getattr(self.encoder, n) for n in TRAINABLE] + list(self.encoder.block11.rep[-2:])
            for m in self.trainable:
                for p in m.parameters():
                    p.requires_grad = True
            self.img = nn.Sequential(nn.Linear(self.encoder.num_features, 512), nn.ReLU(), nn.Dropout(0.3))
            d += 512
        if use_meta:
            self.meta = nn.Sequential(nn.Linear(2, 32), nn.ReLU(), nn.Dropout(0.3))
            d += 32
        self.head = nn.Sequential(nn.Linear(d, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, n_classes))

    def train(self, mode=True):
        """Frozen batch-norm layers stay in inference mode while training (as Keras does for frozen layers)."""
        super().train(mode)
        if self.use_image and mode:
            trainable_ids = {id(m) for t in self.trainable for m in t.modules()}
            for m in self.encoder.modules():
                if isinstance(m, nn.BatchNorm2d) and id(m) not in trainable_ids:
                    m.eval()
        return self

    def forward(self, x, meta):
        parts = []
        if self.use_image:
            parts.append(self.img(self.encoder(x)))
        if self.use_meta:
            parts.append(self.meta(meta))
        return self.head(torch.cat(parts, 1))


# ---------------------------------------------------------------- training

@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    out = []
    for x, m, _ in loader:
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            logits = model(x.to(device), m.to(device))
        out.append(torch.softmax(logits.float(), 1).cpu().numpy())
    return np.concatenate(out)


def prob_table(rows, P):
    t = rows[["png", "patient_id", "side", "view", "y", "t_class", "dense"]].copy().reset_index(drop=True)
    for i, c in enumerate(CLASSES):
        t[f"p_{c}"] = P[:, i]
    return t


def train_one(rows, images, cfg, out_dir, device):
    """Train one E0-family model on rows[split == train], record val every epoch, keep the LAST epoch (as the
    paper). Saves model.pt, val_predictions.csv, metrics_val.json, training_log.csv, run_config.json."""
    from src.metrics_mc import summary_mc
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    t0 = time.time()
    tr, va = (rows["split"] == "train").to_numpy(), (rows["split"] == "val").to_numpy()
    imgs = np.stack(images)
    ds_tr = ImageMetaDataset(rows[tr], imgs[tr], cfg["meta"])
    ds_va = ImageMetaDataset(rows[va], imgs[va], cfg["meta"])
    dl_tr = DataLoader(ds_tr, batch_size=64, shuffle=True, num_workers=cfg.get("workers", 2))
    dl_va = DataLoader(ds_va, batch_size=128, shuffle=False, num_workers=cfg.get("workers", 2))

    model = PaperNet(cfg["use_image"], cfg["use_meta"], pretrained=cfg.get("pretrained", True)).to(device)
    # 'balanced' class weights as sklearn computes them in the paper: n / (n_classes x n_class), from TRAIN
    counts = np.bincount(rows.loc[tr, "y"], minlength=5)
    w = torch.tensor(len(ds_tr) / (5 * counts), dtype=torch.float32, device=device)
    loss_fn = nn.CrossEntropyLoss(weight=w)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=1e-3)
    plateau = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=5)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    log = []
    for epoch in range(1, cfg.get("epochs", 10) + 1):
        model.train()
        total, n = 0.0, 0
        for x, m, y in dl_tr:
            x, m, y = x.to(device), m.to(device), y.to(device)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                logits = model(x, m)
            loss = loss_fn(logits.float(), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            total += loss.item() * len(y)
            n += len(y)
        P = predict(model, dl_va, device)
        yv = rows.loc[va, "y"].to_numpy()
        val_loss = float(nn.functional.nll_loss(torch.log(torch.tensor(P).clamp_min(1e-7)), torch.tensor(yv), weight=w.cpu()))
        plateau.step(val_loss)
        log.append({"epoch": epoch, "train_loss": total / n, "val_loss": val_loss,
                    "val_acc": float((P.argmax(1) == yv).mean()), "lr": opt.param_groups[0]["lr"]})
        print(f"  {cfg['name']} seed {cfg['seed']} epoch {epoch:2d} | train loss {total / n:.4f} | "
              f"val loss {val_loss:.4f} | val acc {log[-1]['val_acc']:.3f}", flush=True)

    torch.save(model.state_dict(), out / "model.pt")  # the LAST epoch, as in the paper
    val = prob_table(rows[va], P)
    val.to_csv(out / "val_predictions.csv", index=False)
    pd.DataFrame(log).to_csv(out / "training_log.csv", index=False)
    metrics = {"split": "val", "minutes": (time.time() - t0) / 60, "class_weights": w.tolist(),
               **summary_mc(val, CLASSES)}
    (out / "metrics_val.json").write_text(json.dumps(metrics, indent=2))
    (out / "run_config.json").write_text(json.dumps(cfg, indent=2))
    return metrics


# ---------------------------------------------------------------- the family of runs

CONFIGS = {
    # name: (split, use_image, use_meta, meta encoding)
    "E0":            ("imagewise", True,  True,  "paper"),   # exact copy of the paper's code
    "E0-truemeta":   ("imagewise", True,  True,  "true"),    # same, but benign keeps its real lesion type
    "E0-images":     ("imagewise", True,  False, "paper"),   # images only (paper's "unimodal")
    "E0-meta":       ("imagewise", False, True,  "paper"),   # metadata only, paper's encoding
    "E0-meta-true":  ("imagewise", False, True,  "true"),    # metadata only, real lesion types
    "E0-patient":    ("patient",   True,  True,  "paper"),   # exact copy on our patient-wise split
    "E0-paperdata":  ("imagewise", True,  True,  "paper"),   # the paper's full protocol: per-patient labels too
}
PAPERDATA = {"E0-paperdata"}  # these use build_table_paperdata (4,040 images) instead of our 2,590


def run_family(data_root, out_root, names=None, seeds=(42, 43, 44), limit=0, workers=2, pretrained=True, epochs=10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = build_table(data_root)
    if limit:  # local testing: a few images per class
        rows = rows.groupby("y", group_keys=False).sample(n=limit, random_state=0, replace=False).sort_values("png").reset_index(drop=True)
    rows["split_image"] = imagewise_split(rows)
    png_index = pd.read_csv(Path(data_root) / "index" / "png_index.csv")
    print(f"E0 family: {len(rows)} images, {rows['patient_id'].nunique()} patients | per class "
          f"{rows['y'].map(dict(enumerate(CLASSES))).value_counts().to_dict()} | device {device}")
    t = time.time()
    images = load_images(rows, data_root, png_index)
    print(f"loaded {len(images)} full-frame 224 px images in {time.time() - t:.0f} s")
    Path(out_root).mkdir(parents=True, exist_ok=True)
    rows.to_csv(Path(out_root) / "e0_rows.csv", index=False)  # every image, its class and both splits
    results = {}
    paper = None
    for name in names or CONFIGS:
        split, use_image, use_meta, meta = CONFIGS[name]
        if name in PAPERDATA:  # the paper's own labelling, its own image-wise split and images
            if paper is None:
                prow = build_table_paperdata(data_root)
                prow["split_image"] = imagewise_split(prow)
                prow.to_csv(Path(out_root) / "e0_paperdata_rows.csv", index=False)
                print(f"E0-paperdata: {len(prow)} images, {prow['patient_id'].nunique()} patients | per class "
                      f"{prow['y'].map(dict(enumerate(CLASSES))).value_counts().to_dict()}")
                paper = (prow, load_images(prow, data_root, png_index))
            r, imgs = paper[0].assign(split=paper[0]["split_image"]), paper[1]
        else:
            r, imgs = rows.assign(split=rows["split_image"] if split == "imagewise" else rows["split_patient"]), images
        for seed in seeds:
            cfg = {"name": name, "seed": seed, "split": split, "use_image": use_image, "use_meta": use_meta,
                   "meta": meta, "workers": workers, "pretrained": pretrained, "epochs": epochs}
            m = train_one(r, imgs, cfg, Path(out_root) / name / f"seed{seed}", device)
            results[(name, seed)] = m
            print(f"{name} seed {seed}: val acc {m['accuracy']:.3f} | macro AUC {m['auc_macro']:.3f} | "
                  f"micro AUC {m['auc_micro']:.3f} | Benign AUC {m['auc_Benign']:.3f} | {m['minutes']:.1f} min", flush=True)
    return results
