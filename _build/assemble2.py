# -*- coding: utf-8 -*-
"""Assemble the transcript-vs-slide document."""
import glob
import json
import os
import re

BUILD = r"_build"
DOC = os.path.join(BUILD, "doc2")
AUD = os.path.join(BUILD, "audio")
NOTES = os.path.join(AUD, "notes")
TOTAL = 96


def timeline_table():
    with open(os.path.join(AUD, "alignment.json"), encoding="utf-8") as fh:
        rows = json.load(fh)
    with open(os.path.join(BUILD, "page_stats.json"), encoding="utf-8") as fh:
        stats = {p["index"]: p for p in json.load(fh)["pages"]}
    out = ["<table class='tl'><thead><tr><th>页</th><th>拍摄</th><th>音频偏移</th>"
           "<th>场次/讲者</th><th>该页投影片标题（OCR）</th><th>窗口字数</th></tr></thead><tbody>"]
    prev = None
    for r in rows:
        head = (stats[r["index"]]["heading"] or "").replace("|", "/")
        if len(head) > 46:
            head = head[:45] + "…"
        talk = r.get("talk", "?")
        spk = r.get("speaker", "?")
        spk_short = spk.split("（")[0]
        off = "%d:%02d" % (int(r["audio_start"]) // 60, int(r["audio_start"]) % 60)
        cls = ""
        if (talk, spk_short) != prev:
            cls = " class='sep'"
            prev = (talk, spk_short)
        out.append(
            "<tr%s><td class='c'>%d</td><td class='c'>%s</td><td class='c'>%s</td>"
            "<td>%s · %s</td><td>%s</td><td class='c'>%d</td></tr>"
            % (cls, r["index"], r["hms"][:5], off, talk, spk_short, head, r["chars"]))
    out.append("</tbody></table>")
    return "\n".join(out)


def parse_audio_notes():
    pages = {}
    for nf in sorted(glob.glob(os.path.join(NOTES, "seg*.md"))):
        with open(nf, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        cur, buf = None, []
        for ln in lines:
            m = re.match(r"^##\s*第\s*(\d+)\s*页\s*[｜|]\s*(.+)$", ln)
            if m:
                if cur:
                    pages[cur[0]] = (cur[1], "\n".join(buf).strip())
                cur = (int(m.group(1)), m.group(2).strip())
                buf = []
                continue
            if re.match(r"^#{1,2}\s", ln):
                continue
            if cur is not None:
                buf.append(ln)
        if cur:
            pages[cur[0]] = (cur[1], "\n".join(buf).strip())
    return pages


def main():
    with open(os.path.join(AUD, "alignment.json"), encoding="utf-8") as fh:
        align = {r["index"]: r for r in json.load(fh)}
    notes = parse_audio_notes()
    print("audio notes pages:", len(notes), "missing:", [i for i in range(1, TOTAL + 1) if i not in notes])

    with open(os.path.join(DOC, "03_increment.md"), encoding="utf-8") as fh:
        increment = fh.read().strip()
    increment = increment.replace("{{TIMELINE}}", timeline_table())

    parts = []
    with open(os.path.join(DOC, "00_front.md"), encoding="utf-8") as fh:
        parts.append(fh.read().strip())
    parts.append(increment)

    detail = ["# 五、逐页口头要点（96 页）\n",
              "本章按场次顺序给出每一页的“讲者口头要点”。每页的结构固定为：**口头要点**（讲者实际讲述的内容，"
              "已按上下文纠正 ASR 术语）、**口头补充**（幻灯片上没有写、只出现在口头的信息）、**ASR 存疑**。"
              "页码与投影片影印本、以及《内容整理与总结分析》第六章的逐页条目一一对应。"]
    chapters = [
        ("5.1", "第 1 场（孙方宇 / 张毅）：MegaMoE，第 1–34 页", 1, 34,
         "投影片讲“怎么做”，口头更多地讲“为什么这么做”和“踩过什么坑”。"),
        ("5.2", "第 2 场（白洪潇）：大规模训练实践，第 35–52 页", 35, 52,
         "口头补充了大量“为什么这样排序优化”的判断依据，以及问答中对精度与显存代价的追问。"),
        ("5.3", "第 3 场（徐文杰）：KV Cache 压缩，第 53–67 页", 53, 67,
         "投影片给结论，口头给了选型顺序；问答部分（15:31 后 13 分钟）信息量最大。"),
        ("5.4", "第 4 场（卢祥龙）：Dynamo 与智能体推理，第 68–96 页", 68, 96,
         "口头补充了不少落地经验（版本要求、缓存分层建议、三级存储的取舍）。"),
    ]
    for num, title, lo, hi, intro in chapters:
        detail.append("\n## %s %s\n" % (num, title))
        detail.append(intro + "\n")
        for i in range(lo, hi + 1):
            if i not in notes:
                detail.append("\n### 第 %d 页｜（缺口头要点稿）\n" % i)
                continue
            ptitle, body = notes[i]
            r = align.get(i, {})
            detail.append("\n### 第 %d 页｜%s\n" % (i, ptitle))
            detail.append("<p class='meta'>拍摄 %s ｜ 音频 %s 段偏移 %s ｜ 讲者 %s</p>\n" % (
                r.get("hms", "-"), r.get("recording", "")[-4:], int(r.get("audio_start", 0)),
                r.get("speaker", "-")))
            body = "\n".join(("#" + ln) if ln.startswith("###") else ln for ln in body.splitlines())
            detail.append(body + "\n")
    parts.append("\n".join(detail))

    with open(os.path.join(DOC, "05_tail.md"), encoding="utf-8") as fh:
        tail = fh.read().strip()
    morning_path = os.path.join(AUD, "notes", "morning.md")
    if os.path.exists(morning_path):
        with open(morning_path, encoding="utf-8") as fh:
            morning = fh.read().strip()
        mlines = morning.splitlines()
        if mlines and mlines[0].startswith("# "):
            mlines = mlines[1:]
        morning = "\n".join(("#" + ln) if ln.startswith("# ") else ln for ln in mlines)
        tail = tail.replace("{{MORNING}}", morning)
    else:
        tail = tail.replace("{{MORNING}}", "（上午场纪要未生成）")
    parts.append(tail)

    out = "\n\n".join(parts) + "\n"
    dst = os.path.join(BUILD, "final_audio.md")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote", dst, len(out), "chars")


if __name__ == "__main__":
    main()
