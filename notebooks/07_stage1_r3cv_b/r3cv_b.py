# Task 06 v2: 5-fold cross-validation of Stage 1 with recipe R3 (strong augmentation, label smoothing 0.1,
# dropout 0.5, weight decay 1e-2, backbone lr 1e-4, head lr 3e-4). Same folds as the v1 CV (same seed and
# strata, computed by src/folds.py). This notebook trains folds 3, 4. Train + val patients only.
import json, subprocess, sys, time
from pathlib import Path

t0 = time.time()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.train import main

for fold in [3, 4]:
    main(["--stage", "1", "--img-size", "512", "--batch-size", "8", "--epochs", "25", "--patience", "6",
          "--aug", "strong", "--dropout", "0.5", "--label-smoothing", "0.1", "--lr", "3e-4", "--backbone-lr", "1e-4",
          "--weight-decay", "1e-2", "--warmup-epochs", "1", "--workers", "4", "--fold", str(fold), "--n-folds", "5",
          "--out-dir", f"/kaggle/working/r3cv/fold{fold}"])
Path("/kaggle/working/r3cv/notebook_time_b.json").write_text(json.dumps({"notebook_minutes": (time.time() - t0) / 60}))
