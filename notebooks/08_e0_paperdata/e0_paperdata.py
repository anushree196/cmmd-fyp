# Task 08: E0-paperdata, the paper's full protocol (per-patient labels, 4,040 images), 3 seeds, train + val only.
# The test splits are scored later, once, together with E1-E6. Outputs: /kaggle/working/e0/<config>/seed<k>/
import json, sys, time
from pathlib import Path

t0 = time.time()
code_root = next(p.parent.parent for p in Path("/kaggle/input").rglob("src/config.py"))
sys.path.insert(0, str(code_root))
data_root = next(p.parent for p in Path("/kaggle/input").rglob("png1024") if p.is_dir())
from src.e0 import run_family

run_family(data_root, "/kaggle/working/e0", names=["E0-paperdata"], seeds=(42, 43, 44), workers=4)
Path("/kaggle/working/e0/notebook_time_paperdata.json").write_text(json.dumps({"notebook_minutes": (time.time() - t0) / 60}))
print(f"done in {(time.time() - t0) / 60:.1f} min")
