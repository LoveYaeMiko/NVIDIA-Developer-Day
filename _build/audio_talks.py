# -*- coding: utf-8 -*-
"""Label each aligned page with its talk / speaker based on transcript hand-offs."""
import json

AL = r"_build\audio\alignment.json"

# (recording, start_s, end_s, talk_id, talk_title, speaker)
TALKS = [
    ("录音机-20261016-1331", 0, 793, "T1", "MoE 算子实现与通信计算融合（MegaMoE）", "孙方宇"),
    ("录音机-20261016-1331", 793, 2426, "T1", "MoE 算子实现与通信计算融合（MegaMoE）", "张毅"),
    ("录音机-20261016-1331", 2426, 5150, "T2", "结合 Megatron 的 DeepSeek-V4-Pro 大规模训练实践", "白洪潇（NVIDIA Megatron 团队）"),
    ("录音机-20261016-1331", 5150, 7200, "T3", "面向高效 LLM 服务的 KV Cache 压缩", "徐文杰"),
    ("录音机-20261016-1531", 0, 780, "T3", "面向高效 LLM 服务的 KV Cache 压缩", "徐文杰"),
    ("录音机-20261016-1531", 780, 3837, "T4", "Dynamo 为智能体推理基础设施加速", "卢祥龙（NVIDIA 解决方案与工程）"),
]
QA = [("录音机-20261016-1331", 2376, 2426), ("录音机-20261016-1331", 4705, 5126),
      ("录音机-20261016-1531", 0, 760), ("录音机-20261016-1531", 3469, 3640)]

with open(AL, encoding="utf-8") as fh:
    rows = json.load(fh)

for r in rows:
    mid = r["audio_start"] + 8.0
    talk = speaker = "?"
    for rec, a, b, tid, title, spk in TALKS:
        if rec == r["recording"] and a <= mid < b:
            talk, speaker = tid, spk
            r["talk_title"] = title
            break
    r["talk"] = talk
    r["speaker"] = speaker
    r["in_qa"] = any(rec == r["recording"] and a <= mid < b for rec, a, b in QA)

with open(AL, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=1)

prev = None
for r in rows:
    key = (r["talk"], r["speaker"])
    if key != prev:
        print("p%03d %s %s 录音%s@%ss  →  %s / %s%s" % (
            r["index"], r["hms"], r["file"][4:23], r["recording"][-4:], int(r["audio_start"]),
            r["talk"], r["speaker"], "  [Q&A]" if r["in_qa"] else ""))
        prev = key
print("\nQ&A pages:", [r["index"] for r in rows if r["in_qa"]])
