# Task 06, step 0: which packages install on Kaggle today? CPU only, Internet ON. Saves env_result.json.
import json, subprocess, sys, time
from pathlib import Path

result = {"python": sys.version.split()[0]}


def pip(*args):
    """Run pip, return (ok, last lines of its output)."""
    t = time.time()
    p = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *args], capture_output=True, text=True)
    tail = (p.stdout + p.stderr).strip().splitlines()[-8:]
    print(f"pip install {' '.join(args)} -> exit {p.returncode} in {time.time() - t:.0f}s")
    for line in tail:
        print("    ", line[:200])
    return p.returncode == 0, tail


import torch
result["torch"] = torch.__version__
print("Python", result["python"], "| torch", result["torch"])

for pkg in ["monai", "grad-cam"]:
    ok, tail = pip(pkg)
    result[f"install_{pkg}"] = ok
    if not ok:
        result[f"install_{pkg}_error"] = tail

# pyradiomics: first from PyPI, then from its GitHub source if that fails
ok, tail = pip("pyradiomics")
result["install_pyradiomics_pypi"] = ok
if not ok:
    result["install_pyradiomics_pypi_error"] = tail
    ok, tail = pip("git+https://github.com/AIM-Harvard/pyradiomics.git")
    result["install_pyradiomics_github"] = ok
    if not ok:
        result["install_pyradiomics_github_error"] = tail

# does each package import, and which version?
for mod in ["monai", "pytorch_grad_cam", "radiomics", "SimpleITK", "skimage", "timm", "sklearn"]:
    try:
        m = __import__(mod)
        result[f"import_{mod}"] = getattr(m, "__version__", "ok")
    except Exception as e:
        result[f"import_{mod}"] = f"FAILED: {e!r}"[:200]
    print(f"import {mod}: {result[f'import_{mod}']}")

# pyradiomics must also WORK: extract features from a test image with a round "lesion" mask
try:
    import numpy as np
    import SimpleITK as sitk
    from radiomics import featureextractor
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (200, 200)).astype(np.float32)
    yy, xx = np.mgrid[:200, :200]
    mask = ((yy - 100) ** 2 + (xx - 100) ** 2 < 40 ** 2).astype(np.uint8)  # a circle of radius 40
    ext = featureextractor.RadiomicsFeatureExtractor(force2D=True)
    ext.disableAllFeatures()
    for cls in ["firstorder", "shape2D", "glcm", "glrlm"]:
        ext.enableFeatureClassByName(cls)
    feats = ext.execute(sitk.GetImageFromArray(img), sitk.GetImageFromArray(mask))
    feats = {k: float(v) for k, v in feats.items() if not k.startswith("diagnostics")}
    result["pyradiomics_works"] = True
    result["pyradiomics_n_features"] = len(feats)
    # a circle of radius 40 has perimeter about 251 and sphericity about 1: proves the mask is really used
    result["pyradiomics_circle_perimeter"] = feats.get("original_shape2D_Perimeter")
    result["pyradiomics_circle_sphericity"] = feats.get("original_shape2D_Sphericity")
except Exception as e:
    result["pyradiomics_works"] = False
    result["pyradiomics_error"] = repr(e)[:300]
print("pyradiomics works:", result["pyradiomics_works"], {k: v for k, v in result.items() if k.startswith("pyradiomics_")})

Path("/kaggle/working/env_result.json").write_text(json.dumps(result, indent=2, default=str))
print(json.dumps(result, indent=2, default=str))
