# -*- coding: utf-8 -*-
"""Compose the analysis PDF: markdown -> styled HTML -> Chrome PDF -> stamped PDF."""
import json
import os
import re
import sys

import markdown

sys.path.insert(0, r"_build")
from finish_pdf import stamp  # noqa: E402
from html2pdf import html_to_pdf  # noqa: E402

BUILD = r"_build"
SRC_MD = os.path.join(BUILD, "final_content.md")
HTML_OUT = os.path.join(BUILD, "final_content.html")
PDF_RAW = os.path.join(BUILD, "final_content_raw.pdf")
PDF_OUT = r"大模型训练与推理\大模型训练与推理_内容整理与总结分析.pdf"

TOTAL_PAGES = 96

CSS = r"""
@page { size: A4; margin: 22mm 19mm 22mm 19mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 10.2pt; line-height: 1.72;
       color: #1b1f26; margin: 0; }
h1 { font-size: 17pt; color: #0f2f52; margin: 0 0 10pt 0; padding: 0 0 6pt 0;
     border-bottom: 2pt solid #0f2f52; break-before: page; string-set: chapter content(); }
h1.first { break-before: auto; }
h2 { font-size: 13pt; color: #14456f; margin: 16pt 0 6pt; padding-left: 7pt;
     border-left: 4pt solid #2f6fb3; }
h3 { font-size: 11.2pt; color: #1d2b3a; margin: 12pt 0 4pt; }
h4 { font-size: 10.4pt; color: #34495e; margin: 10pt 0 3pt; }
p { margin: 5pt 0; text-align: justify; }
ul, ol { margin: 4pt 0 6pt; padding-left: 18pt; }
li { margin: 2.5pt 0; }
strong { color: #0d2b47; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #eef2f7;
       padding: 0.5pt 3pt; border-radius: 2pt; color: #8a2b52; }
pre { font-family: Consolas, "Courier New", monospace; font-size: 8.2pt; line-height: 1.5;
      background: #f4f7fb; border: 0.5pt solid #d5dde7; border-left: 3pt solid #2f6fb3;
      padding: 6pt 8pt; margin: 8pt 0; white-space: pre; break-inside: avoid; }
pre code { background: none; color: #1b2b3a; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 10pt; font-size: 9.2pt;
        break-inside: auto; }
th, td { border: 0.5pt solid #aeb9c7; padding: 3.5pt 5pt; vertical-align: top; }
th { background: #e6eef8; font-weight: 600; color: #0f2f52; }
tr { break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 7pt 10pt; background: #f4f7fb; border-left: 3pt solid #2f6fb3;
             font-size: 9.6pt; color: #33414f; }
blockquote p { margin: 2pt 0; }
hr { border: none; border-top: 0.5pt solid #c9d2dd; margin: 12pt 0; }
a { color: #14456f; text-decoration: none; }
.small { font-size: 9pt; color: #5a6673; }
/* cover */
.cover { height: 240mm; display: flex; flex-direction: column; justify-content: center;
         break-after: page; }
.cover .bar { height: 8mm; background: #0f2f52; margin-bottom: 18mm; }
.cover h1.ct { font-size: 30pt; border: none; color: #0f2f52; margin: 0; padding: 0;
               break-before: auto; }
.cover .sub { font-size: 15pt; color: #2f6fb3; margin-top: 6pt; font-weight: 600; }
.cover .en { font-size: 10pt; color: #7b8794; margin-top: 4pt; letter-spacing: 0.4pt; }
.cover table { margin-top: 16mm; font-size: 9.6pt; width: 100%; }
.cover td { border: none; padding: 3pt 0; }
.cover td:first-child { color: #6b7785; width: 26mm; }
.cover .note { margin-top: 12mm; font-size: 8.8pt; color: #6b7785; line-height: 1.6; }
/* toc */
.tocpage { break-after: page; }
.toc-title { font-size: 17pt; color: #0f2f52; border-bottom: 2pt solid #0f2f52; padding-bottom: 6pt;
             margin-bottom: 10pt; }
.toc { break-after: page; }
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc ul ul { padding-left: 12pt; }
.toc li { margin: 2.6pt 0; font-size: 9.4pt; }
.toc ul ul li { font-size: 8.8pt; color: #46525f; }
.toc a { color: #1b1f26; }
.toc ul ul a { color: #46525f; }
/* status chips */
.chip { display: inline-block; font-size: 8.4pt; padding: 1pt 6pt; border-radius: 8pt;
        background: #e6eef8; color: #14456f; margin-right: 4pt; }
"""


def page_index_table():
    with open(os.path.join(BUILD, "page_stats.json"), encoding="utf-8") as fh:
        stats = json.load(fh)
    dup = {}
    for a, b, r in stats["dups"]:
        dup.setdefault(b, a)
    rows = []
    for p in stats["pages"]:
        head = re.sub(r"\s+", " ", p["heading"] or "（未识别出标题）")
        note = ""
        if p["index"] in dup:
            note = "与第 %d 页为同一张投影片的重复拍摄" % dup[p["index"]]
        elif p["chars"] < 80:
            note = "识别文字较少"
        rows.append(
            "<tr><td class='c'>%d</td><td>%s</td><td>%s</td><td class='c'>%d</td><td>%s</td></tr>"
            % (p["index"], re.search(r"_(\d{6})", p["file"]).group(1)[:2] + ":"
               + re.search(r"_(\d{6})", p["file"]).group(1)[2:4] + ":"
               + re.search(r"_(\d{6})", p["file"]).group(1)[4:], head, p["chars"], note))
    return ("<table class='idx'><thead><tr><th>序</th><th>拍摄</th><th>该页识别标题</th>"
            "<th>字数</th><th>备注</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


def main():
    with open(SRC_MD, encoding="utf-8") as fh:
        md = fh.read()

    cover_md = ""
    m = re.search(r"<!--COVER-->(.*?)<!--/COVER-->", md, re.S)
    if m:
        cover_md = m.group(1)
        md = md[:m.start()] + md[m.end():]

    if "{{PAGE_INDEX}}" in md:
        md = md.replace("{{PAGE_INDEX}}", page_index_table())

    html_body = markdown.markdown(
        md,
        extensions=["tables", "toc", "attr_list", "sane_lists", "md_in_html", "fenced_code"],
        extension_configs={"toc": {"title": "目录", "toc_depth": "2"}},
    )
    cover_html = markdown.markdown(cover_md, extensions=["tables", "attr_list"]) if cover_md else ""
    cover_html = cover_html.replace("<table>", "<table class='cover-meta'>", 1)

    html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>大模型训练与推理 · 内容整理与总结分析</title>
<style>%s
.cover-meta { margin-top: 14mm; }
.idx td.c { text-align: center; color: #5a6673; }
.idx { font-size: 8.6pt; }
.idx td, .idx th { padding: 2.6pt 4pt; }
</style></head><body>
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

    # detect where the numbered body starts (cover + TOC are unnumbered)
    import fitz
    probe = fitz.open(PDF_RAW)
    front = 2
    for i in range(1, min(8, probe.page_count)):
        if "这 96 张照片记录" in probe[i].get_text():
            front = i
            break
    print("front pages (unnumbered):", front, "of", probe.page_count)
    probe.close()

    # bookmarks: every h1/h2 heading, plus per-page h3 entries, in document order
    ordered = []
    for line in md.splitlines():
        m1 = re.match(r"^(#{1,2}) +(.+)$", line)
        if m1:
            ordered.append((len(m1.group(1)), re.sub(r"[*`]", "", m1.group(2)).strip()))
            continue
        m3 = re.match(r"^### 第 (\d+) 页｜(.+)$", line)
        if m3:
            ordered.append((3, "第 %s 页 · %s" % (m3.group(1), re.sub(r"[*`]", "", m3.group(2)).strip()[:34]),
                            "第 %s 页" % m3.group(1)))
    toc = ordered

    out, total = stamp(
        PDF_RAW, PDF_OUT,
        header_left="大模型训练与推理 · 内容整理与总结分析",
        header_right="96 张课堂投影片 · 2026-10-16",
        footer_left="来源：大模型训练与推理（IMG_20261016_*.jpg）",
        footer_right="OCR 整理稿 · 仅供学习参考",
        cover_pages=front,
        toc=toc,
        search_from=front,
    )
    print("stamped:", out, total, "pages,", round(os.path.getsize(out) / 1e6, 2), "MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
