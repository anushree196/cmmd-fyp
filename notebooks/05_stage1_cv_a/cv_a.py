# Task 06 v2: 5-fold cross-validation of Stage 1 with the chosen recipe (v1's: light augmentation, lr 1e-4,
# dropout 0.3, weight decay 1e-4). This notebook trains folds 0, 1, 2. Train + val patients only; test untouched.
import json, subprocess, sys, time
from pathlib import Path

t0 = time.time()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.train import main

for fold in [0, 1, 2]:
    main(["--stage", "1", "--img-size", "512", "--epochs", "20", "--batch-size", "8", "--lr", "1e-4",
          "--patience", "5", "--workers", "4", "--fold", str(fold), "--n-folds", "5",
          "--out-dir", f"/kaggle/working/fold{fold}"])
Path("/kaggle/working/notebook_time_a.json").write_text(json.dumps({"notebook_minutes": (time.time() - t0) / 60}))
