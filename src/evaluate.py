"""Score the TEST split once, with the model and threshold chosen on validation by src/train.py.

Nothing is tuned here: the weights (best.pt), the settings (run_config.json) and the threshold
(metrics_val.json) all come from the training run. To keep "test once" honest, the script refuses to run if
the run folder already holds test results, unless --force is given (and then the log will show it).

Writes into the run folder:
    test_predictions.csv     test probabilities
    metrics_test.json        AUC (95% CI), sensitivity, specificity at the val threshold, and the subgroups

Usage:
    python -m src.evaluate --run-dir outputs/stage1_e1 [--out-dir somewhere-writable]
"""
import argparse, json, shutil, time
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader

from src.data import find_data_root, make_dataset, read_split
from src.metrics import summary, threshold_for_sensitivity
from src.models import DualViewNet
from src.train import predict


def subgroups(test, thr):
    """Test results for the groups we report separately (decided by Anu in task 04)."""
    benign = test[test["label"] == 0]
    groups = {
        # AUC of a cancer subgroup = how well those cancers are ranked above ALL benign test breasts
        "invisible_cancers_vs_all_benign": pd.concat([test[(test["label"] == 1) & (test["t_class"] == "Invisible")], benign]),
        "visible_cancers_vs_all_benign": pd.concat([test[(test["label"] == 1) & (test["t_class"] == "Malignant")], benign]),
        "dense_breasts": test[test["dense"].astype(str) == "True"],
        "non_dense_breasts": test[test["dense"].astype(str) == "False"],
        # specificity on the two kinds of benign breast
        "benign_no_visible_lesion": test[(test["label"] == 0) & (test["t_class"] == "Normal")],
        "benign_visible_lesion": test[(test["label"] == 0) & (test["t_class"] == "Benign")],
    }
    return {name: summary(df, thr) for name, df in groups.items() if len(df)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="folder with best.pt, run_config.json, metrics_val.json")
    ap.add_argument("--out-dir", default=None, help="where to write (default: the run folder)")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--force", action="store_true", help="score the test split again (avoid)")
    args = ap.parse_args(argv)
    run = Path(args.run_dir)
    out = Path(args.out_dir or run)
    out.mkdir(parents=True, exist_ok=True)
    if (run / "metrics_test.json").exists() or (out / "metrics_test.json").exists():
        if not args.force:
            raise SystemExit("Test results already exist for this run. The test split is scored only once.")
        print("WARNING: --force given, the test split is being scored AGAIN")

    cfg = json.loads((run / "run_config.json").read_text())
    val_metrics = json.loads((run / "metrics_val.json").read_text())
    thr = val_metrics["chosen_threshold"]
    # Both operating points come from VALIDATION predictions only:
    #   youden     - the rule fixed in the code before any results (max sensitivity + specificity - 1)
    #   val_sens90 - added after seeing the val results (Youden gave only 55% val sensitivity): the highest
    #                threshold that keeps at least 90% of the validation cancers flagged
    val_pred = pd.read_csv(run / "val_predictions.csv")
    thresholds = {"youden": thr, "val_sens90": threshold_for_sensitivity(val_pred, 0.90)}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    root = find_data_root(args.data_root or cfg.get("data_root"))

    df = read_split(root, cfg["stage"], cfg.get("limit", 0), cfg.get("seed", 42))
    test_df = df[df["split"] == "test"]
    print(f"test {len(test_df)} breasts ({int(test_df['label'].sum())} malignant) | threshold from val {thr:.4f}")
    model = DualViewNet(cfg["backbone"], pretrained=False).to(device)
    model.load_state_dict(torch.load(run / "best.pt", map_location=device))
    dl = DataLoader(make_dataset(test_df, root, cfg["img_size"], train=False, workers=args.workers),
                    batch_size=16, shuffle=False, num_workers=args.workers)
    test = predict(model, dl, device).merge(test_df[["patient_id", "side", "t_class", "dense"]], on=["patient_id", "side"])
    test.assign(split="test").to_csv(out / "test_predictions.csv", index=False)

    metrics = {"split": "test", "scored_at": time.strftime("%Y-%m-%d %H:%M:%S"), "forced_rerun": args.force,
               "threshold_from_val": thr, **summary(test, thr), "subgroups": subgroups(test, thr),
               "operating_points": {name: {"threshold": t, "val": summary(val_pred, t), "test": summary(test, t),
                                           "test_subgroups": subgroups(test, t)}
                                    for name, t in thresholds.items()}}
    (out / "metrics_test.json").write_text(json.dumps(metrics, indent=2))
    if out != run:  # keep the training files next to the test results
        for f in ["run_config.json", "metrics_val.json", "val_predictions.csv", "training_log.csv", "training_curves.png"]:
            if (run / f).exists():
                shutil.copy2(run / f, out / f)
    print(json.dumps({k: metrics[k] for k in ["auc", "auc_ci95", "sensitivity", "specificity", "confusion"]}, indent=1))
    for name, op in metrics["operating_points"].items():
        print(f"  operating point {name}: threshold {op['threshold']:.4f} | val sens {op['val']['sensitivity']:.3f} "
              f"spec {op['val']['specificity']:.3f} | test sens {op['test']['sensitivity']:.3f} "
              f"spec {op['test']['specificity']:.3f}")
    for name, s in metrics["subgroups"].items():
        print(f"  {name}: n={s['n_breasts']} AUC={s.get('auc', float('nan')):.3f} {s.get('auc_ci95', '')} "
              f"sens={s.get('sensitivity', float('nan')):.3f} spec={s.get('specificity', float('nan')):.3f}")
    return metrics


if __name__ == "__main__":
    main()
