# -*- coding: utf-8 -*-
"""OCR the keynote video frames to recover the morning slide titles."""
import glob
import json
import os

import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

FRAMES = r"_build\video\frames"
OUT = r"_build\video\slides"
os.makedirs(OUT, exist_ok=True)

engine = RapidOCR(intra_op_num_threads=8, inter_op_num_threads=1)

rows = []
for p in sorted(glob.glob(os.path.join(FRAMES, "*.jpg"))):
    im = Image.open(p).convert("RGB")
    arr = np.array(im)[:, :, ::-1]
    result, _ = engine(arr)
    lines = []
    for box, text, score in (result or []):
        if float(score) < 0.5:
            continue
        lines.append((min(pt[1] for pt in box), min(pt[0] for pt in box), text.strip(), float(score)))
    lines.sort(key=lambda t: (round(t[0] / 40), t[1]))
    texts = [t[2] for t in lines if t[2]]
    base = os.path.splitext(os.path.basename(p))[0]
    with open(os.path.join(OUT, base + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("# %s\n" % base)
        fh.write("\n".join(texts))
    rows.append({"frame": base, "n": len(texts), "title": texts[0] if texts else "", "texts": texts})
    print(base, len(texts), (texts[0][:60] if texts else ""), flush=True)

with open(os.path.join(OUT, "frames.json"), "w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=1)
print("done", len(rows), "frames")
