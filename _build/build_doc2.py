# -*- coding: utf-8 -*-
"""Compose the transcript-vs-slide PDF."""
import os
import re
import sys

import markdown

sys.path.insert(0, r"_build")
from finish_pdf import stamp  # noqa: E402
from html2pdf import html_to_pdf  # noqa: E402

BUILD = r"_build"
SRC_MD = os.path.join(BUILD, "final_audio.md")
HTML_OUT = os.path.join(BUILD, "final_audio.html")
PDF_RAW = os.path.join(BUILD, "final_audio_raw.pdf")
PDF_OUT = r"大模型训练与推理\大模型训练与推理_讲稿整理（录音对照）.pdf"

CSS_BASE = open(os.path.join(BUILD, "doc_style.css"), encoding="utf-8").read() if os.path.exists(
    os.path.join(BUILD, "doc_style.css")) else ""

CSS = r"""
@page { size: A4; margin: 22mm 19mm 22mm 19mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 10.2pt; line-height: 1.72;
       color: #1b1f26; margin: 0; }
h1 { font-size: 17pt; color: #123b2c; margin: 0 0 10pt 0; padding: 0 0 6pt 0;
     border-bottom: 2pt solid #123b2c; break-before: page; }
h2 { font-size: 13pt; color: #17614a; margin: 16pt 0 6pt; padding-left: 7pt;
     border-left: 4pt solid #2f8f6f; }
h3 { font-size: 11.2pt; color: #1d2b3a; margin: 12pt 0 4pt; }
h4 { font-size: 10.4pt; color: #34495e; margin: 10pt 0 3pt; }
p { margin: 5pt 0; text-align: justify; }
ul, ol { margin: 4pt 0 6pt; padding-left: 18pt; }
li { margin: 2.5pt 0; }
strong { color: #0e3527; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #eef4f1;
       padding: 0.5pt 3pt; border-radius: 2pt; color: #8a2b52; }
pre { font-family: Consolas, "Courier New", monospace; font-size: 8.2pt; line-height: 1.5;
      background: #f2f7f4; border: 0.5pt solid #cfdcd6; border-left: 3pt solid #2f8f6f;
      padding: 6pt 8pt; margin: 8pt 0; white-space: pre; break-inside: avoid; }
pre code { background: none; color: #1b2b3a; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 10pt; font-size: 9.2pt; }
th, td { border: 0.5pt solid #aeb9c7; padding: 3.5pt 5pt; vertical-align: top; }
th { background: #e4f0ea; font-weight: 600; color: #123b2c; }
tr { break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 7pt 10pt; background: #f3f8f5; border-left: 3pt solid #2f8f6f;
             font-size: 9.6pt; color: #33414f; }
blockquote p { margin: 2pt 0; }
hr { border: none; border-top: 0.5pt solid #c9d2dd; margin: 12pt 0; }
a { color: #17614a; text-decoration: none; }
/* cover */
.cover { height: 240mm; display: flex; flex-direction: column; justify-content: center;
         break-after: page; }
.cover .bar { height: 8mm; background: #123b2c; margin-bottom: 18mm; }
.cover h1.ct { font-size: 27pt; border: none; color: #123b2c; margin: 0; padding: 0;
               break-before: auto; }
.cover h2.sub { font-size: 14.5pt; color: #2f8f6f; margin-top: 6pt; font-weight: 600;
                border: none; padding: 0; }
.cover .en { font-size: 10pt; color: #7b8794; margin-top: 4pt; letter-spacing: 0.4pt; }
.cover table { margin-top: 14mm; font-size: 9.6pt; width: 100%; }
.cover td { border: none; padding: 3pt 0; }
.cover td:first-child { color: #6b7785; width: 26mm; }
.cover .note { margin-top: 10mm; font-size: 8.6pt; color: #6b7785; line-height: 1.6; }
/* toc */
.toc { break-after: page; }
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc ul ul { padding-left: 12pt; }
.toc li { margin: 2.6pt 0; font-size: 9.4pt; }
.toc ul ul li { font-size: 8.8pt; color: #46525f; }
.toc p { font-size: 17pt; color: #123b2c; border-bottom: 2pt solid #123b2c; padding-bottom: 6pt;
         margin: 0 0 10pt 0; font-weight: 700; }
/* timeline table */
.tl { font-size: 7.8pt; }
.tl td, .tl th { padding: 1.7pt 3.5pt; }
.tl td.c { text-align: center; color: #5a6673; }
.tl tr.sep td { border-top: 1.2pt solid #2f8f6f; }
p.meta { font-size: 8.4pt; color: #6b7785; margin: 1pt 0 4pt 0; background: #f2f7f4;
         padding: 2pt 6pt; border-left: 2pt solid #9cc9b8; }
"""


def main():
    with open(SRC_MD, encoding="utf-8") as fh:
        md = fh.read()

    cover_md = ""
    m = re.search(r"<!--COVER-->(.*?)<!--/COVER-->", md, re.S)
    if m:
        cover_md = m.group(1)
        md = md[:m.start()] + md[m.end():]

    html_body = markdown.markdown(
        md,
        extensions=["tables", "toc", "attr_list", "sane_lists", "md_in_html", "fenced_code"],
        extension_configs={"toc": {"title": "目录", "toc_depth": "2"}},
    )
    cover_html = markdown.markdown(cover_md, extensions=["tables", "attr_list"]) if cover_md else ""

    html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>大模型训练与推理 · 现场录音讲稿整理</title>
<style>%s</style></head><body>
<div class="cover"><div class="bar"></div>%s</div>
%s
</body></html>""" % (CSS, cover_html, html_body)

    with open(HTML_OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    ok, rc, err = html_to_pdf(HTML_OUT, PDF_RAW, extra_wait=25000)
    if not ok:
        print("render FAILED rc=%s\n%s" % (rc, err))
        return 1
    print("raw pdf:", round(os.path.getsize(PDF_RAW) / 1e6, 2), "MB")

    import fitz
    probe = fitz.open(PDF_RAW)
    front = 2
    for i in range(1, min(8, probe.page_count)):
        if "录音补充册" in probe[i].get_text():
            front = i
            break
    print("front pages (unnumbered):", front, "of", probe.page_count)
    probe.close()

    ordered = []
    for line in md.splitlines():
        m1 = re.match(r"^(#{1,2}) +(.+)$", line)
        if m1:
            ordered.append((len(m1.group(1)), re.sub(r"[*`]", "", m1.group(2)).strip()))
            continue
        m3 = re.match(r"^### 第 (\d+) 页｜(.+)$", line)
        if m3:
            ordered.append((3, "第 %s 页 · %s" % (m3.group(1), re.sub(r"[*`]", "", m3.group(2)).strip()[:30]),
                            "第 %s 页" % m3.group(1)))

    out, total = stamp(
        PDF_RAW, PDF_OUT,
        header_left="大模型训练与推理 · 现场录音讲稿整理（录音转写 × 投影片对照）",
        header_right="2026-10-16 下午场 · 4 场分享 / 5 位讲者",
        footer_left="音频：录音机-20261016-1331.wav / -1531.wav（讯飞录音文件转写大模型）",
        footer_right="口语转写稿 · 仅供学习参考",
        cover_pages=front,
        toc=ordered,
        search_from=front,
    )
    print("stamped:", out, total, "pages,", round(os.path.getsize(out) / 1e6, 2), "MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
