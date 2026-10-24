"""Task 08: score the TEST split ONCE for every frozen model of the ablation (E0 family, E1-E6, E1-224).

Nothing is chosen here: every model, epoch and setting was fixed on validation by the training notebooks.
For each experiment every seed (or fold) model scores the test samples; the experiment's result is the
average of those probabilities (one prediction per sample), with 95% bootstrap CIs by patient. Each single
seed's metrics are saved too (descriptive). Refuses to run if test results already exist in --out-dir.

    E0 family     test = that configuration's own test part (image-wise 10%, or our patient test for E0-patient)
    E1-E6, E1-224 test = the 101 Stage 2 test patients (one breast each)

Writes into --out-dir: test_<experiment>.csv (per-seed and averaged probabilities) and metrics_test.json.
"""
import argparse, json, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from src import e0, stage2
from src.data import find_data_root
from src.metrics_mc import summary_mc


def per_seed_and_mean(prob_tables, classes, key_cols):
    """prob_tables: {seed_name: DataFrame with key_cols + y + p_<class>}. Returns one table with every seed's
    probabilities and their mean, plus metrics of the mean (with CIs) and of each seed (point values)."""
    names = sorted(prob_tables)
    base = prob_tables[names[0]][key_cols + ["y"]].copy()
    for n in names:
        t = prob_tables[n]
        for c in classes:
            base[f"p_{c}_{n}"] = t[f"p_{c}"].to_numpy()
    for c in classes:
        base[f"p_{c}"] = base[[f"p_{c}_{n}" for n in names]].mean(axis=1)
    base["spread"] = np.mean([base[[f"p_{c}_{n}" for n in names]].std(axis=1) for c in classes], axis=0)
    singles = {n: {k: v for k, v in summary_mc(prob_tables[n], classes, n_boot=0).items()
                   if k.startswith(("auc_", "accuracy", "f1_", "precision_", "recall_"))} for n in names}
    return base, {"models": names, "averaged": summary_mc(base, classes), "single_models": singles}


def score_e0(runs_root, data_root, out, device, only=None):
    results = {}
    png_index = pd.read_csv(Path(data_root) / "index" / "png_index.csv")
    ours = e0.build_table(data_root)
    ours["split_image"] = e0.imagewise_split(ours)
    paper = e0.build_table_paperdata(data_root)
    paper["split_image"] = e0.imagewise_split(paper)
    cache = {}
    for name, (split, use_image, use_meta, meta) in e0.CONFIGS.items():
        if only and name not in only:
            continue
        model_files = sorted(p for p in Path(runs_root).rglob("model.pt") if p.parent.parent.name == name)
        if not model_files:
            print(f"{name}: no trained models found, skipped")
            continue
        rows = paper if name in e0.PAPERDATA else ours
        col = "split_image" if split == "imagewise" else "split_patient"
        test = rows[rows[col] == "test"].reset_index(drop=True)
        key = (name in e0.PAPERDATA, col)
        if key not in cache:
            cache[key] = np.stack(e0.load_images(test, data_root, png_index))
        ds = e0.ImageMetaDataset(test, cache[key], meta)
        dl = DataLoader(ds, batch_size=64, shuffle=False, num_workers=2)
        tables = {}
        for f in model_files:
            model = e0.PaperNet(use_image, use_meta, pretrained=False).to(device)
            model.load_state_dict(torch.load(f, map_location=device))
            tables[f.parent.name] = e0.prob_table(test, e0.predict(model, dl, device))
        table, metrics = per_seed_and_mean(tables, e0.CLASSES, ["png", "patient_id", "side", "view"])
        table.to_csv(out / f"test_{name}.csv", index=False)
        results[name] = metrics
        a = metrics["averaged"]
        print(f"{name}: {len(test)} test images | micro AUC {a['auc_micro']:.3f} | macro {a['auc_macro']:.3f} | "
              f"Benign {a['auc_Benign']:.3f} | acc {a['accuracy']:.3f}", flush=True)
    return results


def score_stage2(runs_root, data_root, out, device):
    results = {}
    df, rad_cols = stage2.load_table(data_root, stage2.find_features_root())
    test = df[df["split"] == "test"].reset_index(drop=True)
    datasets = {}
    for exp_dir in sorted({p.parent.parent for p in Path(runs_root).rglob("best.pt")
                           if p.parent.parent.name.split("-")[0] in stage2.EXPERIMENTS}):
        name = exp_dir.name
        views, crop, radiomics, fusion = stage2.EXPERIMENTS[name.split("-")[0]]
        tables = {}
        for f in sorted(exp_dir.glob("*/best.pt")):
            cfg = json.loads((f.parent / "run_config.json").read_text())
            if (cfg["size"], crop) not in datasets:
                datasets[(cfg["size"], crop)] = stage2.make_dataset(test, data_root, cfg["size"], rad_cols, False, crop)
            dl = DataLoader(datasets[(cfg["size"], crop)], batch_size=8, shuffle=False, num_workers=0)
            model = stage2.Stage2Net(views, crop, radiomics, fusion, n_rad=len(rad_cols) + 1, pretrained=False).to(device)
            model.load_state_dict(torch.load(f, map_location=device))
            tables[f.parent.name] = stage2.predict(model, dl, device)
        table, metrics = per_seed_and_mean(tables, stage2.SUBTYPES, ["patient_id", "side"])
        table.to_csv(out / f"test_{name}.csv", index=False)
        results[name] = metrics
        a = metrics["averaged"]
        print(f"{name}: {len(test)} test patients, {len(tables)} models | macro AUC {a['auc_macro']:.3f} | "
              f"micro {a['auc_micro']:.3f} | acc {a['accuracy']:.3f}", flush=True)
    return results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--only", nargs="*", default=None, help="score only these E0 configurations (no Stage 2)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "metrics_test.json").exists() and not args.force:
        raise SystemExit("Test results already exist here. The test split is scored only once.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_root = find_data_root(args.data_root)
    t0 = time.time()
    results = {"scored_at": time.strftime("%Y-%m-%d %H:%M:%S"), "forced_rerun": args.force,
               "e0": score_e0(args.runs_root, data_root, out, device, args.only),
               "stage2": {} if args.only else score_stage2(args.runs_root, data_root, out, device)}
    results["minutes"] = (time.time() - t0) / 60
    (out / "metrics_test.json").write_text(json.dumps(results, indent=2))
    print(f"done in {results['minutes']:.1f} min")


if __name__ == "__main__":
    main()
