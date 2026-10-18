# -*- coding: utf-8 -*-
"""Quick OCR quality probe on a couple of sample photos."""
import time

import numpy as np
from PIL import Image, ImageOps
from rapidocr_onnxruntime import RapidOCR

SRC = r"大模型训练与推理"
engine = RapidOCR()

samples = ["IMG_20261016_133219.jpg", "IMG_20261016_133406.jpg", "IMG_20261016_140940.jpg"]
for name in samples:
    path = SRC + "\\" + name
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = im.size
    scale = 2200 / max(w, h)
    if scale < 1:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    arr = np.array(im)[:, :, ::-1]  # RGB -> BGR
    t0 = time.time()
    result, elapse = engine(arr)
    dt = time.time() - t0
    print("=" * 70)
    print(name, "size:", im.size, "elapsed: %.2fs" % dt, "boxes:", 0 if not result else len(result))
    if result:
        # sort by y then x for reading order
        items = []
        for box, text, score in result:
            ys = [p[1] for p in box]
            xs = [p[0] for p in box]
            items.append((min(ys), min(xs), text.strip(), float(score)))
        items.sort(key=lambda t: (round(t[0] / 30), t[1]))
        for _, _, text, score in items:
            print("  [%.2f] %s" % (score, text))
