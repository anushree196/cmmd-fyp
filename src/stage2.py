"""Stage 2 (molecular subtype: LumA / LumB / HER2 / TN), experiments E1-E6 of the ablation.

All experiments use the SAME 671 Stage 2 patients (one breast each), the SAME patient-wise split
(469 train / 101 val / 101 test), the same encoder, recipe and seeds. Each experiment adds ONE component:

    E1  MLO view only                                  + clinical (age, lesion type), concatenation
    E2  + CC view, combined with View Attention
    E3  + MLO lesion crop (TOMPEI mask box + 20 px, 224 x 224) through the same encoder
    E4  + radiomics branch (20 features selected on train in task 07, + has_box_only) Dense(21->64)
    E5  concatenation replaced by Gated Fusion
    E6  E5's model trained as a 5-fold cross-validation ensemble (decided by Anu, task 08 Q1)

Recipe (Stage 1's winner R3, fixed, not tuned per experiment): strong augmentation, label smoothing 0.1,
dropout 0.5, weight decay 1e-2, backbone lr 1e-4, head lr 3e-4, 1 warm-up epoch + cosine, up to 25 epochs,
early stopping (patience 6) on validation MACRO AUC, class weights from train.
"""
import json, math, time
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
from monai import transforms as T
from monai.data import CacheDataset
from torch import nn
from torch.utils.data import DataLoader

from src.data import AGE_MEAN, AGE_STD, LoadPair, augmentations, find_data_root
from src.metrics_mc import summary_mc

SUBTYPES = ["LumA", "LumB", "HER2", "TN"]
CLASS_OF = {"Luminal A": 0, "Luminal B": 1, "HER2-enriched": 2, "triple negative": 3}
LESION = ["mass", "calcification", "both"]
CROP_SIZE, CROP_MARGIN = 224, 20
GREY_MEAN, GREY_STD = 0.449, 0.226

EXPERIMENTS = {  # name: (views, crop, radiomics, fusion)
    "E1": ("mlo", False, False, "concat"),
    "E2": ("both", False, False, "concat"),
    "E3": ("both", True, False, "concat"),
    "E4": ("both", True, True, "concat"),
    "E5": ("both", True, True, "gated"),
    "E6": ("both", True, True, "gated"),
}


# ---------------------------------------------------------------- data

def find_features_root():
    kaggle = Path("/kaggle/input")
    if kaggle.exists():
        return next(p.parent for p in kaggle.rglob("radiomics_selected.json"))
    return Path("data/features")


def load_table(data_root, features_root):
    """stage2.csv + the selected radiomics, ready for the model. Radiomics: box-only shapes filled with the TRAIN
    medians saved in task 07, then standardised with the TRAIN mean and standard deviation."""
    s2 = pd.read_csv(Path(data_root) / "splits" / "stage2.csv")
    s2["y"] = s2["subtype"].map(CLASS_OF)
    meta = json.loads((Path(features_root) / "radiomics_selected.json").read_text())
    feats = pd.read_csv(Path(features_root) / "radiomics_features.csv")
    sel = meta["selected"]
    df = s2.merge(feats[["patient_id", "side"] + sel], on=["patient_id", "side"], how="left")
    assert df[sel].notna().any(axis=1).all(), "every Stage 2 breast needs radiomics"
    for c, v in meta["box_only_shape_fill_medians_from_train"].items():
        if c in sel:
            df[c] = df[c].fillna(v)
    tr = df["split"] == "train"
    mu, sd = df.loc[tr, sel].mean(), df.loc[tr, sel].std().replace(0, 1)
    df[sel] = (df[sel] - mu) / sd
    return df, sel


class LoadCrop:
    """The MLO lesion crop: the mask's bounding box + 20 px (as MONAI CropForegroundd(margin=20) does), squashed
    to 224 x 224 (as the master document's lesion pipeline does), values 0..1. Not random, so it is cached."""

    def __init__(self, png_dir, mask_dir):
        self.png_dir, self.mask_dir = Path(png_dir), Path(mask_dir)

    def __call__(self, item):
        import cv2
        item = dict(item)
        img = cv2.imread(str(self.png_dir / item["png_mlo_name"]), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(self.mask_dir / item["mask_name"]), cv2.IMREAD_GRAYSCALE) > 0
        ys, xs = np.where(mask)
        y0, y1 = max(ys.min() - CROP_MARGIN, 0), min(ys.max() + 1 + CROP_MARGIN, mask.shape[0])
        x0, x1 = max(xs.min() - CROP_MARGIN, 0), min(xs.max() + 1 + CROP_MARGIN, mask.shape[1])
        crop = cv2.resize(img[y0:y1, x0:x1], (CROP_SIZE, CROP_SIZE), interpolation=cv2.INTER_AREA)
        item["crop"] = (crop.astype(np.float32) / 255.0)[None]
        return item


def make_dataset(df, data_root, size, rad_cols, train, crop, workers=0):
    recs = [{"cc": r.png_cc, "mlo": r.png_mlo, "png_mlo_name": r.png_mlo, "mask_name": r.mask,
             "clin": np.array([(r.age - AGE_MEAN) / AGE_STD] + [float(r.abnormality == k) for k in LESION], np.float32),
             "rad": np.array([getattr(r, c) for c in rad_cols] + [float(r.has_box_only)], np.float32),
             "label": int(r.y), "patient_id": r.patient_id, "side": r.side} for r in df.itertuples()]
    root = Path(data_root)
    steps = [LoadPair(root / "png1024", size)]
    if crop:
        steps.append(LoadCrop(root / "png1024", root / "masks1024"))
    if train:
        steps += augmentations(size, "strong", keys=["cc", "mlo"])
        if crop:
            steps += augmentations(CROP_SIZE, "strong", keys=["crop"])
    keys = ["cc", "mlo"] + (["crop"] if crop else [])
    steps.append(T.EnsureTyped(keys=keys, track_meta=False))
    return CacheDataset(recs, T.Compose(steps), cache_rate=1.0, num_workers=workers or None, progress=False)


# ---------------------------------------------------------------- model

class Stage2Net(nn.Module):
    def __init__(self, views, crop, radiomics, fusion, n_rad=21, pretrained=True, dropout=0.5, backbone="efficientnet_b3"):
        super().__init__()
        self.views, self.use_crop, self.use_rad, self.fusion = views, crop, radiomics, fusion
        self.encoder = timm.create_model(backbone, pretrained=pretrained, num_classes=0, in_chans=1)
        d = self.encoder.num_features
        if views == "both":
            self.view_score = nn.Linear(d, 1)                      # View Attention, as in Stage 1
        self.img = nn.Sequential(nn.Linear(d * (2 if crop else 1), 512), nn.ReLU(), nn.Dropout(0.3))
        self.clin = nn.Sequential(nn.Linear(4, 32), nn.ReLU())     # age + lesion type (3)
        dims = [512, 32]
        if radiomics:
            self.rad = nn.Sequential(nn.Linear(n_rad, 64), nn.ReLU(), nn.Dropout(0.2))
            dims.append(64)
        if fusion == "gated":
            # Gated Fusion: from all modalities together, one weight (0..1) per modality; each modality's vector
            # is multiplied by its weight before the head. The model learns, per patient, how much to trust each.
            self.gate = nn.Sequential(nn.Linear(sum(dims), len(dims)), nn.Sigmoid())
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(sum(dims), 4))

    def encode(self, x):
        return self.encoder((x - GREY_MEAN) / GREY_STD).float()

    def forward(self, batch):
        b = batch["mlo"].shape[0]
        images = [batch["mlo"]] + ([batch["cc"]] if self.views == "both" else []) + ([batch["crop"]] if self.use_crop else [])
        same_size = [im for im in images if im.shape[-1] == images[0].shape[-1]]
        feats = self.encode(torch.cat(same_size))                 # views share one pass (same size)
        f_mlo = feats[:b]
        out = {}
        with torch.autocast(device_type=f_mlo.device.type, enabled=False):  # small layers in 32-bit
            if self.views == "both":
                v = torch.stack([feats[b:2 * b], f_mlo], 1)         # (batch, [cc, mlo], d)
                w = torch.softmax(self.view_score(v).squeeze(-1), 1)
                img = (w.unsqueeze(-1) * v).sum(1)
                out["view_w"] = w
            else:
                img = f_mlo
            if self.use_crop:
                img = torch.cat([img, self.encode(batch["crop"])], 1)
            parts = [self.img(img), self.clin(batch["clin"].float())]
            if self.use_rad:
                parts.append(self.rad(batch["rad"].float()))
            if self.fusion == "gated":
                g = self.gate(torch.cat(parts, 1))
                parts = [p * g[:, i:i + 1] for i, p in enumerate(parts)]
                out["gate"] = g
            out["logits"] = self.head(torch.cat(parts, 1))
        return out


# ---------------------------------------------------------------- training

@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    rows = []
    for batch in loader:
        gpu = {k: v.to(device) for k, v in batch.items() if torch.is_tensor(v)}
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            out = model(gpu)
        if not torch.isfinite(out["logits"]).all():
            out = model(gpu)
        P = torch.softmax(out["logits"].float(), 1).cpu().numpy()
        for i in range(len(P)):
            r = {"patient_id": batch["patient_id"][i], "side": batch["side"][i], "y": int(batch["label"][i])}
            r.update({f"p_{c}": float(P[i, k]) for k, c in enumerate(SUBTYPES)})
            if "gate" in out:
                r.update({f"gate_{n}": float(out["gate"][i, k]) for k, n in enumerate(["image", "clinical", "radiomics"][:out["gate"].shape[1]])})
            if "view_w" in out:
                r["w_cc"], r["w_mlo"] = float(out["view_w"][i, 0]), float(out["view_w"][i, 1])
            rows.append(r)
    return pd.DataFrame(rows)


def train_one(exp, train_df, val_df, rad_cols, data_root, out_dir, seed=42, size=512, epochs=25, patience=6,
              batch_size=8, workers=2, pretrained=True, lr=3e-4, backbone_lr=1e-4, weight_decay=1e-2,
              label_smoothing=0.1, dropout=0.5, warmup_epochs=1.0):
    views, crop, radiomics, fusion = EXPERIMENTS[exp]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = {k: v for k, v in locals().items() if k in ("exp", "seed", "size", "epochs", "patience", "batch_size", "lr",
                                                       "backbone_lr", "weight_decay", "label_smoothing", "dropout",
                                                       "warmup_epochs", "views", "crop", "radiomics", "fusion")}
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    ds_tr = make_dataset(train_df, data_root, size, rad_cols, True, crop, workers)
    ds_va = make_dataset(val_df, data_root, size, rad_cols, False, crop, workers)
    dl_tr = DataLoader(ds_tr, batch_size=batch_size, shuffle=True, num_workers=workers, drop_last=len(ds_tr) > batch_size)
    dl_va = DataLoader(ds_va, batch_size=batch_size * 2, shuffle=False, num_workers=workers)

    counts = np.bincount(train_df["y"], minlength=4)
    w = torch.tensor(len(train_df) / (4 * np.maximum(counts, 1)), dtype=torch.float32)
    loss_fn = nn.CrossEntropyLoss(weight=w.to(device), label_smoothing=label_smoothing)
    model = Stage2Net(views, crop, radiomics, fusion, n_rad=len(rad_cols) + 1, pretrained=pretrained, dropout=dropout).to(device)
    enc = {id(p) for p in model.encoder.parameters()}
    opt = torch.optim.AdamW([{"params": list(model.encoder.parameters()), "lr": backbone_lr},
                             {"params": [p for p in model.parameters() if id(p) not in enc], "lr": lr}],
                            weight_decay=weight_decay)
    steps, warm = epochs * len(dl_tr), max(1, int(warmup_epochs * len(dl_tr)))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm))))
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    log, best, best_epoch, bad = [], -1.0, 0, 0
    for epoch in range(1, epochs + 1):
        t = time.time()
        model.train()
        total, n, skipped = 0.0, 0, 0
        for batch in dl_tr:
            gpu = {k: v.to(device) for k, v in batch.items() if torch.is_tensor(v)}
            bn_before = [x.detach().clone() for x in model.buffers()]
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                loss = loss_fn(model(gpu)["logits"].float(), gpu["label"])
            if not torch.isfinite(loss):  # bad-step guard, as in Stage 1
                with torch.no_grad():
                    for x, s in zip(model.buffers(), bn_before):
                        x.copy_(s)
                skipped += 1
                sched.step()
                continue
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            total += loss.item() * len(gpu["label"])
            n += len(gpu["label"])
        val = predict(model, dl_va, device)
        m = summary_mc(val, SUBTYPES, n_boot=0) if np.isfinite(val[[f"p_{c}" for c in SUBTYPES]].to_numpy()).all() else None
        if m is None:
            raise SystemExit("validation predictions are not finite: stopping")
        log.append({"epoch": epoch, "train_loss": total / max(n, 1), "val_auc_macro": m["auc_macro"],
                    "val_auc_micro": m["auc_micro"], "val_acc": m["accuracy"], "skipped_steps": skipped,
                    "minutes": (time.time() - t) / 60})
        print(f"  {exp} seed {seed} epoch {epoch:2d} | train loss {log[-1]['train_loss']:.4f} | val macro AUC "
              f"{m['auc_macro']:.4f} | val acc {m['accuracy']:.3f} | skipped {skipped} | {log[-1]['minutes']:.1f} min", flush=True)
        if m["auc_macro"] > best:  # chosen on VALIDATION macro AUC only
            best, best_epoch, bad = m["auc_macro"], epoch, 0
            torch.save(model.state_dict(), out / "best.pt")
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(torch.load(out / "best.pt", map_location=device))
    val = predict(model, dl_va, device)
    val.to_csv(out / "val_predictions.csv", index=False)
    pd.DataFrame(log).to_csv(out / "training_log.csv", index=False)
    metrics = {"split": "val", "best_epoch": best_epoch, "epochs_run": len(log), "minutes": (time.time() - t0) / 60,
               "class_weights": w.tolist(), **summary_mc(val, SUBTYPES)}
    (out / "metrics_val.json").write_text(json.dumps(metrics, indent=2))
    (out / "run_config.json").write_text(json.dumps(cfg, indent=2))
    print(f"{exp} seed {seed}: best epoch {best_epoch} | val macro AUC {metrics['auc_macro']:.4f} "
          f"{np.round(metrics.get('auc_macro_ci95', [np.nan, np.nan]), 3).tolist()} | {metrics['minutes']:.1f} min", flush=True)
    return metrics


def stage2_folds(df, n_folds=5, seed=42):
    """E6: 5 folds over the train + val patients (one breast each), stratified by subtype."""
    from sklearn.model_selection import StratifiedKFold
    pool = df[df["split"].isin(["train", "val"])].reset_index(drop=True)
    fold = np.empty(len(pool), int)
    for k, (_, idx) in enumerate(StratifiedKFold(n_folds, shuffle=True, random_state=seed).split(pool, pool["y"])):
        fold[idx] = k
    return pool.assign(fold=fold)


def run(exps, out_root, seeds=(42, 43, 44), data_root=None, limit=0, workers=2, pretrained=True, suffix="", **kw):
    """Train the given experiments (train + val only; test is never loaded here). `suffix` names a variant
    (e.g. "-224" for E1 at 224 px), so its outputs go to their own folder."""
    data_root = find_data_root(data_root)
    df, rad_cols = load_table(data_root, find_features_root())
    if limit:  # local testing
        df = df.groupby(["split", "y"], group_keys=False).sample(n=limit, random_state=0, replace=True).drop_duplicates(["patient_id", "side"])
    tr, va = df[df["split"] == "train"], df[df["split"] == "val"]
    print(f"Stage 2: train {len(tr)} / val {len(va)} breasts | radiomics {len(rad_cols)} + has_box_only | test not loaded")
    results = {}
    for exp in exps:
        if exp == "E6":
            pool = stage2_folds(df)
            Path(out_root).mkdir(parents=True, exist_ok=True)
            pool[["patient_id", "side", "split", "fold", "y"]].to_csv(Path(out_root) / "E6_folds.csv", index=False)
            for k in range(5):
                results[("E6", k)] = train_one("E6", pool[pool.fold != k], pool[pool.fold == k], rad_cols, data_root,
                                               Path(out_root) / "E6" / f"fold{k}", seed=42, workers=workers,
                                               pretrained=pretrained, **kw)
        else:
            for seed in seeds:
                results[(exp + suffix, seed)] = train_one(exp, tr, va, rad_cols, data_root, Path(out_root) / f"{exp}{suffix}" / f"seed{seed}",
                                                 seed=seed, workers=workers, pretrained=pretrained, **kw)
    return results
