# -*- coding: utf-8 -*-
"""打包合并版交付物（排除 runtime、缓存、临时输出）。"""
import os
import zipfile
from pathlib import Path

ROOT = Path(r"D:\Program Files\Deepseek\作业\智慧图书馆数字资源平台-合并版")
ZIP = Path(r"D:\Program Files\Deepseek\作业\24数科3班-202414870324-王睿昌-智慧图书馆数字资源平台.zip")
SKIP_DIRS = {"runtime", "__pycache__", ".git", "node_modules", "_archive"}
SKIP_FILES = {"_lab_out.txt", "_extra_out.txt", "_main_fixed.docx"}

count = 0
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES or f.endswith(".pyc"):
                continue
            p = Path(root) / f
            z.write(p, Path("智慧图书馆数字资源平台") / p.relative_to(ROOT))
            count += 1
print("zip", ZIP, round(ZIP.stat().st_size / 1048576, 2), "MB,", count, "files")
