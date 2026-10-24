# Task 08b: E0-clean = E0 with real lesion types AND our patient-wise split, 3 seeds. Nothing is chosen on
# validation (E0 always keeps the last epoch, as the paper), so after training this notebook scores E0-clean's
# test split once. Outputs: /kaggle/working/e0/E0-clean/seed<k>/ and /kaggle/working/e0_clean_test/
import json, sys, time
from pathlib import Path

t0 = time.time()
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
data_root = next(p.parent for p in Path("/kaggle/input").rglob("png1024") if p.is_dir())
from src.e0 import run_family
from src.evaluate_ablation import main as score

run_family(data_root, "/kaggle/working/e0", names=["E0-clean"], seeds=(42, 43, 44), workers=4)
train_minutes = (time.time() - t0) / 60
score(["--runs-root", "/kaggle/working/e0", "--out-dir", "/kaggle/working/e0_clean_test", "--only", "E0-clean"])
Path("/kaggle/working/e0/notebook_time_clean.json").write_text(json.dumps(
    {"notebook_minutes": (time.time() - t0) / 60, "train_minutes": train_minutes}))
