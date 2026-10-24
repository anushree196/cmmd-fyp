# Task 08: score the TEST split ONCE for every frozen ablation model (E0 family incl. E0-paperdata, E1-E6, E1-224).
# CPU only. The trained models come from the attached training notebooks' outputs.
import subprocess, sys
from pathlib import Path

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.evaluate_ablation import main

main(["--runs-root", "/kaggle/input", "--out-dir", "/kaggle/working/ablation_test"])
