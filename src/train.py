"""Train Stage 1 (benign vs malignant) on TRAIN, choose the epoch and the threshold on VALIDATION.

The test split is never read here. It is scored once, at the end, by src/evaluate.py.

Writes to --out-dir:
    best.pt                  weights of the epoch with the highest validation AUC
    run_config.json          every setting of this run (evaluate.py rebuilds the model from it)
    training_log.csv         one row per epoch: train loss, validation loss and AUC, learning rate, minutes
    training_curves.png      the same as a picture
    val_predictions.csv      validation probabilities of the best epoch
    metrics_val.json         validation AUC (95% CI), chosen threshold, sensitivity and specificity there

Usage:
    python -m src.train --stage 1 --img-size 128 --epochs 1 --limit 32 --workers 0     # tiny CPU test
    python -m src.train --stage 1 --img-size 512 --epochs 20 --out-dir /kaggle/working/stage1_e1
"""
import argparse, json, math, random, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader

from src.data import find_data_root, make_dataset, read_split
from src.folds import make_folds
from src.metrics import auc, summary, threshold_for_sensitivity, youden_threshold
from src.models import DualViewNet


def parse(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1, choices=[1])
    ap.add_argument("--data-root", default=None, help="folder with png1024/ and splits/ (found automatically)")
    ap.add_argument("--out-dir", default="outputs/stage1")
    ap.add_argument("--backbone", default="efficientnet_b3")
    ap.add_argument("--no-pretrained", action="store_true", help="random start (only for offline tests)")
    ap.add_argument("--img-size", type=int, default=512)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-4, help="learning rate of the head (and the backbone unless --backbone-lr)")
    ap.add_argument("--backbone-lr", type=float, default=None, help="lower learning rate for the pretrained encoder")
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--dropout", type=float, default=0.3, help="dropout before the head")
    ap.add_argument("--label-smoothing", type=float, default=0.0)
    ap.add_argument("--aug", default="light", choices=["light", "strong"])
    ap.add_argument("--fold", type=int, default=-1, help="-1: the fixed train/val split; 0..n-1: that CV fold is val")
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--warmup-epochs", type=float, default=1.0)
    ap.add_argument("--patience", type=int, default=5, help="stop after this many epochs without a better val AUC")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0, help="use only N breasts per split (testing)")
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args(argv)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


@torch.no_grad()
def predict(model, loader, device):
    """Probabilities of 'malignant' for every breast in the loader, plus the learned view weights."""
    model.eval()
    rows = []
    for batch in loader:
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            logits, w = model(batch["cc"].to(device), batch["mlo"].to(device), batch["clin"].to(device))
        prob = torch.softmax(logits.float(), dim=1)[:, 1].cpu().numpy()
        w = w.float().cpu().numpy()
        for i in range(len(prob)):
            rows.append({"patient_id": batch["patient_id"][i], "side": batch["side"][i],
                         "label": int(batch["label"][i]), "prob": float(prob[i]),
                         "w_cc": float(w[i, 0]), "w_mlo": float(w[i, 1])})
    return pd.DataFrame(rows)


def main(argv=None):
    args = parse(argv)
    set_seed(args.seed)
    t_start = time.time()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cudnn.benchmark = True
    root = find_data_root(args.data_root)
    print(f"device {device} | data {root} | out {out}")

    df = read_split(root, args.stage, args.limit, args.seed)
    if args.fold < 0:
        train_df, val_df = df[df["split"] == "train"], df[df["split"] == "val"]
    else:
        # cross-validation: train + val patients are cut into n folds; this fold is val, the rest is train.
        # The test patients are not in any fold.
        pool = df[df["split"].isin(["train", "val"])].copy()
        pool["fold"] = pool["patient_id"].map(make_folds(pool, args.n_folds, args.seed))
        train_df, val_df = pool[pool["fold"] != args.fold], pool[pool["fold"] == args.fold]
        pool[["patient_id", "side", "split", "fold", "label"]].to_csv(out / "folds.csv", index=False)
        print(f"fold {args.fold} of {args.n_folds}")
    print(f"train {len(train_df)} breasts ({int(train_df['label'].sum())} malignant) | "
          f"val {len(val_df)} ({int(val_df['label'].sum())} malignant) | test not loaded")

    train_ds = make_dataset(train_df, root, args.img_size, train=True, workers=args.workers, aug=args.aug)
    val_ds = make_dataset(val_df, root, args.img_size, train=False, workers=args.workers)
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.workers,
                          drop_last=len(train_ds) > args.batch_size, pin_memory=device.type == "cuda")
    val_dl = DataLoader(val_ds, batch_size=args.batch_size * 2, shuffle=False, num_workers=args.workers)

    # Class weights: about 70% of breasts are malignant, so each benign breast counts more in the loss.
    # weight of a class = (number of breasts) / (2 x breasts of that class), from TRAIN only.
    counts = np.bincount(train_df["label"], minlength=2)
    class_w = torch.tensor(len(train_df) / (2 * counts), dtype=torch.float32)
    print(f"class weights: benign {class_w[0]:.3f}, malignant {class_w[1]:.3f}")
    # label smoothing: the target is 0.95 / 0.05 instead of 1 / 0 (with 0.1), so the model is not pushed to be
    # 100% certain; this limits overfitting
    loss_fn = nn.CrossEntropyLoss(weight=class_w.to(device), label_smoothing=args.label_smoothing)

    model = DualViewNet(args.backbone, pretrained=not args.no_pretrained, dropout=args.dropout).to(device)
    # two learning rates: the pretrained encoder changes slowly, the new layers (view attention, age, head) faster
    encoder = list(model.encoder.parameters())
    ids = {id(p) for p in encoder}
    rest = [p for p in model.parameters() if id(p) not in ids]
    opt = torch.optim.AdamW([{"params": encoder, "lr": args.backbone_lr or args.lr},
                             {"params": rest, "lr": args.lr}], weight_decay=args.weight_decay)
    steps = args.epochs * len(train_dl)
    warm = max(1, int(args.warmup_epochs * len(train_dl)))
    # learning rate: rises linearly for `warm` steps, then follows a cosine curve down to zero
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm))))
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")  # mixed precision on the GPU

    log, best_auc, best_epoch, bad = [], -1.0, 0, 0
    for epoch in range(1, args.epochs + 1):
        t = time.time()
        model.train()
        total, n = 0.0, 0
        for batch in train_dl:
            y = batch["label"].to(device)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                logits, _ = model(batch["cc"].to(device), batch["mlo"].to(device), batch["clin"].to(device))
                loss = loss_fn(logits.float(), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            total += loss.item() * len(y)
            n += len(y)
        val = predict(model, val_dl, device)
        val_auc = auc(val) if val["label"].nunique() == 2 else float("nan")
        p = torch.tensor(val["prob"].values).clamp(1e-6, 1 - 1e-6)
        y_val = torch.tensor(val["label"].values)
        val_loss = float(loss_fn.cpu()(torch.stack([torch.log(1 - p), torch.log(p)], 1).float(), y_val))
        loss_fn.to(device)
        row = {"epoch": epoch, "train_loss": total / max(n, 1), "val_loss": val_loss, "val_auc": val_auc,
               "lr": opt.param_groups[-1]["lr"], "minutes": (time.time() - t) / 60}
        log.append(row)
        print(f"epoch {epoch:2d} | train loss {row['train_loss']:.4f} | val loss {val_loss:.4f} | "
              f"val AUC {val_auc:.4f} | {row['minutes']:.1f} min", flush=True)
        if val_auc > best_auc:  # model selection uses VALIDATION AUC only
            best_auc, best_epoch, bad = val_auc, epoch, 0
            torch.save(model.state_dict(), out / "best.pt")
        else:
            bad += 1
            if bad >= args.patience:
                print(f"no better val AUC for {args.patience} epochs: stopping")
                break

    pd.DataFrame(log).to_csv(out / "training_log.csv", index=False)
    plot_curves(pd.DataFrame(log), out / "training_curves.png", best_epoch)

    # Best epoch -> validation probabilities -> threshold chosen on validation
    model.load_state_dict(torch.load(out / "best.pt", map_location=device))
    val = predict(model, val_dl, device)
    val = val.merge(val_df[["patient_id", "side", "t_class", "dense"]], on=["patient_id", "side"])
    thr = youden_threshold(val) if val["label"].nunique() == 2 else 0.5
    val.assign(split="val").to_csv(out / "val_predictions.csv", index=False)
    metrics = {"split": "val" if args.fold < 0 else f"cv fold {args.fold} of {args.n_folds}",
               "best_epoch": best_epoch, "epochs_run": len(log),
               "chosen_threshold": thr, "threshold_rule": "Youden J (max sensitivity + specificity - 1) on val",
               "mean_view_weight_cc": float(val["w_cc"].mean()), "mean_view_weight_mlo": float(val["w_mlo"].mean()),
               # second operating point, also from val: keep at least 90% of the cancers flagged
               "threshold_val_sens90": threshold_for_sensitivity(val, 0.90) if (val["label"] == 1).any() else None,
               "class_weights": class_w.tolist(), "train_minutes": (time.time() - t_start) / 60,
               "device": str(device), "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
               **summary(val, thr)}
    (out / "metrics_val.json").write_text(json.dumps(metrics, indent=2))
    (out / "run_config.json").write_text(json.dumps(vars(args), indent=2))
    print(json.dumps({k: metrics[k] for k in ["best_epoch", "chosen_threshold", "auc", "auc_ci95", "sensitivity",
                                               "specificity", "train_minutes"] if k in metrics}, indent=1))
    return metrics


def plot_curves(log, path, best_epoch):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    ax[0].plot(log["epoch"], log["train_loss"], label="train")
    ax[0].plot(log["epoch"], log["val_loss"], label="validation")
    ax[0].set(xlabel="epoch", ylabel="weighted cross-entropy", title="Loss")
    ax[0].legend()
    ax[1].plot(log["epoch"], log["val_auc"], color="C1")
    ax[1].axvline(best_epoch, color="grey", ls="--", label=f"best epoch {best_epoch}")
    ax[1].set(xlabel="epoch", ylabel="AUC", title="Validation AUC")
    ax[1].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
