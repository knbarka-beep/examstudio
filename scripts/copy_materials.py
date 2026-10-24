"""Copy the course materials into materials/ (read only on the source side).

Mirrors MATERIALS_SRC into materials/, then reports files that failed to copy
or have size 0 (OneDrive cloud-only placeholders).
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(r"C:\Users\knbar\OneDrive\Skrivebord\AI in Accounting and Business\Assignment 2\1. ExamStudio\materials")
DST = ROOT / "materials"

failed = []


def copy(src, dst):
    try:
        return shutil.copy2(src, dst)
    except OSError as e:
        failed.append((src, str(e)))


def main():
    if not SRC.is_dir():
        sys.exit(f"Source not found: {SRC}")
    shutil.copytree(SRC, DST, dirs_exist_ok=True, copy_function=copy)
    empty = [p for p in DST.rglob("*") if p.is_file() and p.stat().st_size == 0]
    n = sum(1 for p in DST.rglob("*") if p.is_file())
    print(f"Copied {n} files into {DST}")
    for src, err in failed:
        print(f"FAILED: {src}: {err}")
    for p in empty:
        print(f"EMPTY: {p.relative_to(DST)}")


if __name__ == "__main__":
    main()
