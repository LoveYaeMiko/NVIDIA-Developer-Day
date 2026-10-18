# -*- coding: utf-8 -*-
"""Scan transcripts for speaker hand-offs, self-introductions and Q&A markers."""
import os
import re

from audio_align import RECORDINGS, parse_srt

OUT = r"_build\audio"
PAT = re.compile(r"(有请|掌声|欢迎|感谢|谢谢|老师|我是|来自|接下来|进入下|问答|提问|举手|合影|休息|茶歇|午餐)")

lines = []
for name, t0 in RECORDINGS:
    segs = parse_srt(os.path.join(r"转写结果", name + ".srt"))
    lines.append("\n" + "=" * 70)
    lines.append("## %s  (起始 %s，%d 句)" % (name, t0.strftime("%H:%M"), len(segs)))
    for i, s in enumerate(segs):
        txt = s["text"]
        if PAT.search(txt) or len(txt) > 400:
            mm = int(s["start"]) // 60
            ss = int(s["start"]) % 60
            lines.append("[%03d:%02d] %s" % (mm, ss, txt[:260]))

out = os.path.join(OUT, "speaker_scan.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("wrote", out, len(lines), "lines")
