"""Stage 1 v2: combine the 5 cross-validation fold models into one ensemble and score the TEST split once.

1. Out-of-fold (OOF) predictions: every train+val breast was scored by the one fold model that did NOT train
   on it. Together they cover all train+val breasts exactly once.
2. Both thresholds are chosen on the OOF predictions only:
   youden     - maximum of sensitivity + specificity - 1
   oof_sens90 - the highest threshold that still flags at least 90% of the OOF cancers
3. Test: each of the 5 models scores every test breast; the ensemble probability is their mean. The spread
   between the 5 (standard deviation) is saved too: it is the uncertainty measure for semester 2.

Refuses to run if test results already exist in --out-dir, unless --force.

Usage:
    python -m src.evaluate_ensemble --runs-root /path/with/fold0..fold4 --out-dir outputs/stage1_v2
"""
import argparse, json, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from src.data import find_data_root, make_dataset, read_split
from src.evaluate import subgroups
from src.metrics import auc, bootstrap_ci, summary, threshold_for_sensitivity, youden_threshold
from src.models import DualViewNet
from src.train import predict


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True, help="folder holding fold0/ ... fold4/ (searched recursively)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "metrics_test.json").exists() and not args.force:
        raise SystemExit("Test results already exist here. The test split is scored only once.")

    runs = sorted({p.parent for p in Path(args.runs_root).rglob("best.pt") if p.parent.name.startswith("fold")},
                  key=lambda p: p.name)
    cfgs = [json.loads((r / "run_config.json").read_text()) for r in runs]
    print("fold runs:", [str(r) for r in runs])
    assert sorted(c["fold"] for c in cfgs) == list(range(cfgs[0]["n_folds"])), "need exactly one run per fold"

    # ---- 1. out-of-fold predictions and the per-fold validation AUCs
    oof = pd.concat([pd.read_csv(r / "val_predictions.csv").assign(fold=c["fold"]) for r, c in zip(runs, cfgs)])
    fold_auc = [json.loads((r / "metrics_val.json").read_text())["auc"] for r in runs]
    root = find_data_root(args.data_root)
    df = read_split(root, cfgs[0]["stage"], cfgs[0].get("limit", 0), cfgs[0]["seed"])
    trainval = df[df["split"].isin(["train", "val"])]
    assert len(oof) == len(trainval) and not oof.duplicated(["patient_id", "side"]).any(), \
        "OOF predictions must cover every train+val breast exactly once"

    # ---- 2. thresholds from OOF only
    thresholds = {"youden": youden_threshold(oof), "oof_sens90": threshold_for_sensitivity(oof, 0.90)}
    print(f"fold val AUCs {np.round(fold_auc, 4).tolist()} | mean {np.mean(fold_auc):.4f} +- {np.std(fold_auc, ddof=1):.4f}")
    print(f"OOF AUC {auc(oof):.4f} | thresholds {thresholds}")

    # ---- 3. test, once: every fold model scores every test breast
    test_df = df[df["split"] == "test"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    test = test_df[["patient_id", "side", "label", "t_class", "dense"]].copy()
    for r, c in zip(runs, cfgs):
        model = DualViewNet(c["backbone"], pretrained=False).to(device)
        model.load_state_dict(torch.load(r / "best.pt", map_location=device))
        dl = DataLoader(make_dataset(test_df, root, c["img_size"], train=False, workers=args.workers),
                        batch_size=16, shuffle=False, num_workers=args.workers)
        p = predict(model, dl, device)[["patient_id", "side", "prob"]].rename(columns={"prob": f"prob_fold{c['fold']}"})
        test = test.merge(p, on=["patient_id", "side"])
        print(f"fold {c['fold']} scored the test split")
    fold_cols = [f"prob_fold{k}" for k in range(len(runs))]
    test["prob"] = test[fold_cols].mean(axis=1)           # the ensemble
    test["prob_std"] = test[fold_cols].std(axis=1)        # disagreement between the 5 models
    test.assign(split="test").to_csv(out / "test_predictions.csv", index=False)
    oof.to_csv(out / "oof_predictions.csv", index=False)

    lo, hi, _ = bootstrap_ci(oof, auc)
    metrics = {
        "split": "test", "model": f"ensemble of {len(runs)} CV fold models (mean probability)",
        "scored_at": time.strftime("%Y-%m-%d %H:%M:%S"), "forced_rerun": args.force,
        "recipe": {k: v for k, v in cfgs[0].items() if k not in ("fold", "out_dir")},
        "cv_fold_val_auc": fold_auc, "cv_val_auc_mean": float(np.mean(fold_auc)),
        "cv_val_auc_std": float(np.std(fold_auc, ddof=1)),
        "oof": {"auc": auc(oof), "auc_ci95": [lo, hi], "n_breasts": len(oof)},
        "thresholds_from_oof": thresholds,
        **summary(test, thresholds["youden"]),
        # descriptive only, not used for any choice: each single fold model's test AUC
        "single_fold_test_auc": {c: auc(test.rename(columns={c: "prob_x"}).drop(columns="prob").rename(columns={"prob_x": "prob"}))
                                 for c in fold_cols},
        "operating_points": {name: {"threshold": t, "oof": summary(oof, t), "test": summary(test, t),
                                    "test_subgroups": subgroups(test, t)} for name, t in thresholds.items()},
        "mean_prob_std_test": float(test["prob_std"].mean()),
    }
    (out / "metrics_test.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: metrics[k] for k in ["cv_val_auc_mean", "cv_val_auc_std", "oof", "auc", "auc_ci95",
                                               "single_fold_test_auc"]}, indent=1))
    for name, op in metrics["operating_points"].items():
        print(f"  {name}: thr {op['threshold']:.4f} | OOF sens {op['oof']['sensitivity']:.3f} spec "
              f"{op['oof']['specificity']:.3f} | test sens {op['test']['sensitivity']:.3f} spec {op['test']['specificity']:.3f}")
    return metrics


if __name__ == "__main__":
    main()
