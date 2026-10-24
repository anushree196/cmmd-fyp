# Task 06 v2: the 5 CV fold models as one ensemble. Thresholds from out-of-fold predictions; TEST scored once
# (the second test evaluation of Stage 1). CPU only: inference of 5 models plus the bootstrap.
import subprocess, sys
from pathlib import Path

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.evaluate_ensemble import main

main(["--runs-root", "/kaggle/input", "--out-dir", "/kaggle/working/stage1_v2_ensemble", "--workers", "4"])
