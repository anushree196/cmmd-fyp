"""Wrap a plain Python file into a one-cell Jupyter notebook (.ipynb) for `kaggle kernels push`.

The .py file is the source we read, edit and commit; the .ipynb is generated from it.

Usage:
    python scripts/make_kaggle_notebook.py notebooks/01_env/env_check.py notebooks/01_env/cmmd_01_env.ipynb
"""
import json, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
code = src.read_text(encoding="utf-8")
compile(code, str(src), "exec")  # stop here if the file has a syntax error
nb = {
    "cells": [{"cell_type": "code", "execution_count": None, "id": "main", "metadata": {}, "outputs": [],
               "source": code.splitlines(keepends=True)}],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python"}},
    "nbformat": 4, "nbformat_minor": 5,
}
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {out} from {src}")
