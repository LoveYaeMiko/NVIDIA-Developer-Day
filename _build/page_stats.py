# -*- coding: utf-8 -*-
"""Quality/duplicate analysis of the OCR set -> _build/page_stats.json + report text."""
import glob
import json
import os
import re
from difflib import SequenceMatcher

OCR = r"_build\ocr"

recs = []
for jf in sorted(glob.glob(os.path.join(OCR, "page_*.json"))):
    with open(jf, encoding="utf-8") as fh:
        rec = json.load(fh)
    tf = os.path.join(OCR, "text", "%03d_%s.txt" % (rec["index"], os.path.splitext(rec["file"])[0]))
    lines = []
    if os.path.exists(tf):
        with open(tf, encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()[1:] if ln.strip()]
    scores = [b["score"] for b in rec["boxes"]] or [0]
    rec["n_boxes"] = len(rec["boxes"])
    rec["mean_score"] = round(sum(scores) / len(scores), 3)
    rec["low_score_boxes"] = sum(1 for s in scores if s < 0.6)
    rec["chars"] = sum(len(ln) for ln in lines)
    rec["heading"] = lines[0] if lines else ""
    rec["lines"] = lines
    recs.append(rec)

recs.sort(key=lambda r: r["index"])

# near-duplicate detection by feature text overlap
def norm(t):
    return re.sub(r"[\s\W_]+", "", t).lower()


dups = []
for i in range(len(recs)):
    for j in range(i + 1, len(recs)):
        a, b = norm("\n".join(recs[i]["lines"])), norm("\n".join(recs[j]["lines"]))
        if not a or not b:
            continue
        if abs(len(a) - len(b)) / max(len(a), len(b)) > 0.5:
            continue
        r = SequenceMatcher(None, a, b).quick_ratio()
        if r > 0.75:
            r2 = SequenceMatcher(None, a, b).ratio()
            if r2 > 0.72:
                dups.append((recs[i]["index"], recs[j]["index"], round(r2, 3)))

out = {
    "count": len(recs),
    "total_chars": sum(r["chars"] for r in recs),
    "mean_score": round(sum(r["mean_score"] for r in recs) / len(recs), 3),
    "weak_pages": [{"index": r["index"], "boxes": r["n_boxes"], "chars": r["chars"],
                    "mean_score": r["mean_score"], "heading": r["heading"]}
                   for r in recs if r["chars"] < 60 or r["mean_score"] < 0.80],
    "dups": dups,
    "pages": [{k: r[k] for k in ("index", "file", "heading", "n_boxes", "chars", "mean_score",
                                 "low_score_boxes", "orig_size")} for r in recs],
}
with open(r"_build\page_stats.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

print("pages:", out["count"], "total chars:", out["total_chars"], "mean score:", out["mean_score"])
print("\n-- weak pages (chars<60 or score<0.80) --")
for w in out["weak_pages"]:
    print(w)
print("\n-- near duplicates --")
for d in dups:
    print(d)
print("\n-- all headings --")
for r in recs:
    print("%3d %s | %s" % (r["index"], r["file"][4:19], r["heading"][:80]))
