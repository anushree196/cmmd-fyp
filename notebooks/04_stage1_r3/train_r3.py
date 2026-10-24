# Task 06 v2, recipe search run r3: Stage 1 on the fixed train/val split, 512 px. Val only, test untouched.
import json, subprocess, sys, time
from pathlib import Path

t0 = time.time()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], capture_output=True, text=True).stdout)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.train import main

main(["--stage", "1", "--img-size", "512", "--batch-size", "8", "--epochs", "25", "--patience", "6",
      "--aug", "strong", "--dropout", "0.5", "--label-smoothing", "0.1", "--lr", "3e-4", "--backbone-lr", "1e-4",
      "--weight-decay", "1e-2", "--warmup-epochs", "1", "--workers", "4", "--out-dir", "/kaggle/working/r3"])
Path("/kaggle/working/r3/notebook_time.json").write_text(json.dumps({"notebook_minutes": (time.time() - t0) / 60}))
