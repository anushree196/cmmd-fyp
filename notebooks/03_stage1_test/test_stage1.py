# Task 06: score the Stage 1 TEST split once, with the model and threshold chosen on validation by the
# training notebook (cmmd-02-stage1-train, attached as an input). Writes /kaggle/working/stage1_e1/.
import json, subprocess, sys
from pathlib import Path

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
run_dir = next(p.parent for p in Path("/kaggle/input").rglob("stage1_e1/best.pt"))
print("code from", code_root, "| trained run from", run_dir)

from src.evaluate import main

# the training run's folder is read-only here, so results are written to /kaggle/working
main(["--run-dir", str(run_dir), "--out-dir", "/kaggle/working/stage1_e1", "--workers", "4"])
