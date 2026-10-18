# -*- coding: utf-8 -*-
"""Extract the Q&A windows (not covered by slide-aligned page windows)."""
import os

from audio_align import parse_srt

ASR = r"转写结果"
OUT = r"_build\audio\qa"
os.makedirs(OUT, exist_ok=True)

QA = [
    ("qa1", "录音机-20261016-1331", 2370, 2430, "第一场（MegaMoE）问答"),
    ("qa2", "录音机-20261016-1331", 4700, 5130, "第二场（训练实践）问答"),
    ("qa3", "录音机-20261016-1531", 0, 765, "第三场（KV 压缩）问答"),
    ("qa4", "录音机-20261016-1531", 3440, 3660, "第四场（Dynamo）问答与收尾"),
]

for name, rec, a, b, title in QA:
    segs = parse_srt(os.path.join(ASR, rec + ".srt"))
    sel = [s for s in segs if s["end"] > a and s["start"] < b]
    path = os.path.join(OUT, name + ".txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s  录音 %s  时间段 %d–%d 秒（%s）\n\n" % (title, rec, a, b, len(sel)))
        for s in sel:
            fh.write("[%02d:%02d] %s\n" % (int(s["start"]) // 60, int(s["start"]) % 60, s["text"]))
    chars = sum(len(s["text"]) for s in sel)
    print("%s: %d 段, %d 字 -> %s" % (name, len(sel), chars, path))
