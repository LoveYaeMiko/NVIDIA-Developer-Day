# -*- coding: utf-8 -*-
"""Batch OCR all lecture photos with RapidOCR (parallel workers).

Outputs per page:
  _build/ocr/page_NNN.json   full boxes with original-image coordinates
  _build/ocr/text/NNN_<name>.txt   reading-order plain text
"""
import glob
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

SRC = r"大模型训练与推理"
OUT = r"_build\ocr"
TXT = os.path.join(OUT, "text")
MAXSIDE = 2600  # OCR working resolution

os.makedirs(TXT, exist_ok=True)

FILES = sorted(glob.glob(os.path.join(SRC, "*.jpg")))


def order_lines(boxes, tol_ratio=0.6):
    """Group boxes into rows by vertical overlap, then left-to-right."""
    items = []
    for box, text, score in boxes:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        top, bot = min(ys), max(ys)
        items.append({"top": top, "bot": bot, "left": min(xs), "right": max(xs),
                      "cy": (top + bot) / 2.0, "h": bot - top, "text": text, "score": score})
    items.sort(key=lambda d: (d["cy"], d["left"]))
    rows = []
    for it in items:
        placed = False
        for row in rows:
            ref = row[0]
            tol = max(ref["h"], it["h"]) * tol_ratio
            if abs(it["cy"] - ref["cy"]) <= tol:
                row.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    rows.sort(key=lambda r: min(i["cy"] for i in r))
    lines = []
    for row in rows:
        row.sort(key=lambda d: d["left"])
        lines.append(row)
    return lines


def work(idx_name):
    idx, path = idx_name
    import numpy as np
    from PIL import Image, ImageOps
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    ow, oh = im.size
    scale = MAXSIDE / max(ow, oh)
    if scale < 1:
        w, h = int(ow * scale), int(oh * scale)
        small = im.resize((w, h), Image.LANCZOS)
    else:
        w, h = ow, oh
        small = im
    arr = np.array(small)[:, :, ::-1]
    t0 = time.time()
    try:
        result, _ = engine(arr)
    except Exception as exc:  # noqa: BLE001
        return idx, path, None, "ERROR %s" % exc, time.time() - t0
    dt = time.time() - t0
    base = os.path.basename(path)
    rec = {"index": idx, "file": base, "orig_size": [ow, oh], "ocr_size": [w, h],
           "elapsed": round(dt, 2), "boxes": []}
    entries = []
    for box, text, score in (result or []):
        # scale boxes back to original image pixels
        sb = [[float(p[0]) / scale, float(p[1]) / scale] for p in box]
        rec["boxes"].append({"box": sb, "text": text, "score": float(score)})
        entries.append((sb, text, float(score)))
    rows = order_lines(entries)
    lines = []
    for row in rows:
        lines.append("  ".join(i["text"].strip() for i in row if i["text"].strip()))
    txt = "\n".join(lines)
    with open(os.path.join(OUT, "page_%03d.json" % idx), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(TXT, "%03d_%s.txt" % (idx, os.path.splitext(base)[0])), "w", encoding="utf-8") as fh:
        fh.write("# %d  %s  (%dx%d)\n" % (idx, base, ow, oh))
        fh.write(txt + "\n")
    return idx, path, len(rec["boxes"]), txt, dt


def is_done(idx):
    jf = os.path.join(OUT, "page_%03d.json" % idx)
    tf = glob.glob(os.path.join(TXT, "%03d_*.txt" % idx))
    if not (os.path.exists(jf) and tf):
        return False
    try:
        with open(jf, encoding="utf-8") as fh:
            rec = json.load(fh)
        return bool(rec.get("boxes") is not None and rec.get("orig_size"))
    except Exception:  # noqa: BLE001
        for p in [jf] + tf:
            try:
                os.remove(p)
            except OSError:
                pass
        return False


def main():
    jobs = [(i + 1, p) for i, p in enumerate(FILES)]
    jobs = [j for j in jobs if not is_done(j[0])]
    only = [a for a in sys.argv[1:] if a.isdigit()]
    if only:
        wanted = set(int(x) for x in only)
        jobs = [j for j in jobs if j[0] in wanted]
    print("todo:", len(jobs), flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=9) as pool:
        for n, (idx, path, cnt, txt, dt) in enumerate(pool.map(work, jobs), 1):
            preview = (txt or "").replace("\n", " | ")[:90]
            print("%3d/%3d  #%03d  boxes=%s  %.1fs  %s" % (n, len(jobs), idx, cnt, dt, preview),
                  flush=True)
    print("done in %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
