# -*- coding: utf-8 -*-
"""Extract quantitative / result-style claims per page for grounded synthesis."""
import glob
import json
import os
import re

OCR = r"_build\ocr"
KEYS = re.compile(r"(\d+(?:\.\d+)?\s*[xX×]|\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*(?:GB|GiB|TB|TiB|MB|KB|"
                  r"ms|us|µs|s\b|tokens?|T\b|B\b|K\b)|speedup|faster|throughput|TTFT|TPOT|TPF|"
                  r"hit rate|perf|speed|带宽|加速|吞吐|命中|时延)", re.I)

rows = []
for jf in sorted(glob.glob(os.path.join(OCR, "page_*.json"))):
    with open(jf, encoding="utf-8") as fh:
        rec = json.load(fh)
    tf = os.path.join(OCR, "text", "%03d_%s.txt" % (rec["index"], os.path.splitext(rec["file"])[0]))
    if not os.path.exists(tf):
        continue
    with open(tf, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines()[1:] if ln.strip()]
    hits = [ln for ln in lines if KEYS.search(ln) and len(ln) > 8]
    if hits:
        rows.append((rec["index"], lines[0] if lines else "", hits[:6]))

out = []
for idx, head, hits in rows:
    out.append("== 页 %d | %s" % (idx, head[:70]))
    for h in hits:
        out.append("   - " + h[:200])
text = "\n".join(out)
with open(r"_build\numeric_claims.txt", "w", encoding="utf-8") as fh:
    fh.write(text)
print("pages with numeric claims:", len(rows), "chars:", len(text))
