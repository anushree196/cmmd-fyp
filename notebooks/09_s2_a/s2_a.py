# Task 08: Stage 2 ablation, notebook a. Train + val only; the test split is scored later, once, for all
# experiments together. Outputs: /kaggle/working/s2/<experiment>/seed<k>/ (or fold<k>/ for E6).
import json, subprocess, sys, time
from pathlib import Path

t0 = time.time()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "monai"], check=True)
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
from src.stage2 import run

run(["E1"], "/kaggle/working/s2", workers=4)
run(["E1"], "/kaggle/working/s2", workers=4, size=224, suffix="-224")   # Q4: E1 at 224 px, to split the E0 -> E1 jump
run(["E2"], "/kaggle/working/s2", workers=4)
Path("/kaggle/working/s2/notebook_time_a.json").write_text(json.dumps({"notebook_minutes": (time.time() - t0) / 60}))
print(f"done in {(time.time() - t0) / 60:.1f} min")
