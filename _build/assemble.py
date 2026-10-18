# -*- coding: utf-8 -*-
"""Assemble final_content.md from authored parts + per-page digests."""
import glob
import os
import re

BUILD = r"_build"
DOC = os.path.join(BUILD, "doc")
NOTES = os.path.join(BUILD, "notes")
TOTAL = 96

CHAPTERS = [
    ("6.1", "第一部分 · MegaMoE：单内核融合的 MoE 算子（第 1–34 页）", 1, 34,
     "这一段是全场的“内核篇”。先看融合能带来多少理论上界（第 1–3 页），再看优化清单如何逐条兑现"
     "（第 4–32 页），最后用 token sweep 给出实测加速比并收束（第 33–34 页）。"
     "阅读时可把第 4–5 页的大纲当成目录：后面每一页都在回答这张清单上的一项。"),
    ("6.2", "第二部分 · 大规模训练优化 playbook（第 35–52 页）", 35, 52,
     "视角从单个内核抬到集群。第 35–38 页先立问题（装得下 / 跑得快）并说明模型特征如何驱动优化，"
     "第 39–43 页确定起点（并行布局、显存策略、代理模型），第 44–51 页按 STEP 1→4 逐步落地，"
     "第 52 页把经验收成可复用配方。"),
    ("6.3", "第三部分 · KV Cache 压缩：TurboQuant / KVTC / nvCOMP-ANS（第 53–67 页）", 53, 67,
     "推理侧的“显存篇”。第 53–56 页说明为什么 KV Cache 是服务瓶颈、压缩在系统中的位置与代价，"
     "第 57–60 页是在线量化（TurboQuant），第 61–64 页是存储/传输压缩（KVTC），"
     "第 65–66 页是无损熵编码（nvCOMP-ANS），第 67 页给出三条路线的取舍要点。"),
    ("6.4", "第四部分 · KV Router 与 Flash Indexer（第 68–78 页）", 68, 78,
     "这一段为中文投影片，讲 Dynamo 体系里的缓存感知路由：第 68–69 页是能力与生产验证，"
     "第 70 页是两类打分信号，第 71–72 页解释索引在链路中的位置，第 73–76 页给出六代索引的吞吐演进，"
     "第 77–78 页把它拆成独立服务。"),
    ("6.5", "第五部分 · 智能体推理与 ThunderAgent（第 79–96 页）", 79, 96,
     "全场收尾，也是最新的一段：第 79–81 页重新定义 SLA 并用真实 trace 量化智能体负载，"
     "第 82–84 页给出三层软件栈与可观测性，第 85–90 页按“容量→命中率→并发→路由”四组目标实测，"
     "第 91–95 页是会话网关 ThunderAgent 及其基准与 RL rollout 集成，第 96 页列资产与后续工作。"),
]


def parse_notes():
    pages = {}
    for nf in sorted(glob.glob(os.path.join(NOTES, "seg*.md"))):
        with open(nf, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        cur = None
        buf = []
        for ln in lines:
            m = re.match(r"^##\s*页\s*(\d+)\s*[｜|]\s*(.+)$", ln)
            if m:
                if cur:
                    pages[cur[0]] = (cur[1], "\n".join(buf).strip())
                cur = (int(m.group(1)), m.group(2).strip())
                buf = []
                continue
            if re.match(r"^##\s*本段主题与脉络", ln):
                if cur:
                    pages[cur[0]] = (cur[1], "\n".join(buf).strip())
                cur = None
                buf = []
                continue
            if re.match(r"^#\s", ln):
                continue  # segment title
            if cur is not None:
                buf.append(ln)
        if cur:
            pages[cur[0]] = (cur[1], "\n".join(buf).strip())
    return pages


def clean_body(body):
    out = []
    for ln in body.splitlines():
        s = ln.rstrip()
        if s.strip() in ("---", "***", "___"):
            continue
        if s.startswith("###"):
            s = "#" + s          # demote inline sub-headings
        out.append(s)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    notes = parse_notes()
    missing = [i for i in range(1, TOTAL + 1) if i not in notes]
    print("parsed pages:", len(notes), "missing:", missing)

    parts = []
    for name in ("00_front.md", "01_thread.md", "02_analysis.md", "03_conclusion.md"):
        with open(os.path.join(DOC, name), encoding="utf-8") as fh:
            parts.append(fh.read().strip())

    detail = ["# 六、逐页要点整理\n",
              "本章按五个部分逐页给出整理稿。每一页给出“推测标题 + 该页要点 + 图表说明”，"
              "数字与英文术语均按幻灯片原样保留；`(?)` 表示识别或归属不确定，"
              "`识别内容不足` 表示该页文字过少或版面被截断。原图见配套影印本的同编号页。"]
    for num, title, lo, hi, intro in CHAPTERS:
        detail.append("\n## %s %s\n" % (num, title))
        detail.append(intro + "\n")
        for i in range(lo, hi + 1):
            if i not in notes:
                continue
            ptitle, body = notes[i]
            detail.append("\n### 第 %d 页｜%s\n" % (i, ptitle))
            detail.append(clean_body(body) + "\n")
    parts.append("\n".join(detail))

    with open(os.path.join(DOC, "04_appendix.md"), encoding="utf-8") as fh:
        parts.append(fh.read().strip())

    out = "\n\n".join(parts) + "\n"
    dst = os.path.join(BUILD, "final_content.md")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote", dst, len(out), "chars")


if __name__ == "__main__":
    main()
