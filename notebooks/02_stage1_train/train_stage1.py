# Task 06: train Stage 1 (benign vs malignant) on Kaggle GPU. Train + validation only; the test split is
# scored later, once, by notebooks/03_stage1_test. Outputs go to /kaggle/working/stage1_e1/.
import json, subprocess, sys, time
from pathlib import Path

t0 = time.time()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)  # not preinstalled on Kaggle
print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], capture_output=True, text=True).stdout)

# our code comes from the private dataset cmmd-code (no GitHub token needed)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
print("code from", code_root)

from src.train import main

metrics = main(["--stage", "1", "--img-size", "512", "--epochs", "20", "--batch-size", "8", "--lr", "1e-4",
                "--patience", "5", "--workers", "4", "--out-dir", "/kaggle/working/stage1_e1"])

notebook_minutes = (time.time() - t0) / 60
Path("/kaggle/working/stage1_e1/notebook_time.json").write_text(json.dumps({"notebook_minutes": notebook_minutes}))
print(f"notebook finished in {notebook_minutes:.1f} min")
