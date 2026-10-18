# -*- coding: utf-8 -*-
"""Second OCR pass at higher resolution for the weakest pages."""
import glob
import json
import os

import numpy as np
import onnxruntime  # noqa: F401  (ensures package import path is warm)
from PIL import Image, ImageOps
from rapidocr_onnxruntime import RapidOCR

SRC = r"大模型训练与推理"
OUT = r"_build\ocr_hires"
os.makedirs(OUT, exist_ok=True)

TARGETS = [18, 26, 31, 84, 81, 86, 87, 92]
MAXSIDE = 3800

files = sorted(glob.glob(os.path.join(SRC, "*.jpg")))
engine = RapidOCR(intra_op_num_threads=8, inter_op_num_threads=1)

for idx in TARGETS:
    path = files[idx - 1]
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    ow, oh = im.size
    scale = MAXSIDE / max(ow, oh)
    small = im.resize((int(ow * scale), int(oh * scale)), Image.LANCZOS) if scale < 1 else im
    arr = np.array(small)[:, :, ::-1]
    result, _ = engine(arr)
    lines = []
    for box, text, score in (result or []):
        lines.append((min(p[1] for p in box), min(p[0] for p in box), text.strip(), float(score)))
    lines.sort(key=lambda t: (round(t[0] / 45), t[1]))
    out = os.path.join(OUT, "%03d.txt" % idx)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# %03d hi-res re-OCR of %s (%dx%d)\n" % (idx, os.path.basename(path), ow, oh))
        for _, _, t, s in lines:
            fh.write("[%.2f] %s\n" % (s, t))
    print(idx, "boxes:", len(lines), "->", out, flush=True)
