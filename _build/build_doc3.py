# -*- coding: utf-8 -*-
"""Build the one-sitting handout PDF (dense A4 layout)."""
import os
import re
import sys

import markdown

sys.path.insert(0, r"_build")
from finish_pdf import stamp  # noqa: E402
from html2pdf import html_to_pdf  # noqa: E402

BUILD = r"_build"
SRC_MD = os.path.join(BUILD, "doc3", "00_handout.md")
HTML_OUT = os.path.join(BUILD, "handout.html")
PDF_RAW = os.path.join(BUILD, "handout_raw.pdf")
PDF_OUT = r"大模型训练与推理\大模型训练与推理_讲义（全天浓缩版）.pdf"

CSS = r"""
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 9.4pt; line-height: 1.58;
       color: #1a1e24; margin: 0; }
h1 { font-size: 14.5pt; color: #0d3548; margin: 0 0 7pt 0; padding: 3pt 0 4pt 8pt;
     border-left: 6pt solid #0d3548; border-bottom: 0.8pt solid #b9c9d4; break-before: page;
     background: #f1f6f9; }
h2 { font-size: 11.4pt; color: #10506b; margin: 11pt 0 4pt; padding-left: 6pt;
     border-left: 3.5pt solid #1f7fa8; }
h3 { font-size: 10pt; color: #1d2b3a; margin: 9pt 0 3pt; }
p { margin: 3.5pt 0; text-align: justify; }
ul, ol { margin: 3pt 0 5pt; padding-left: 15pt; }
li { margin: 1.6pt 0; }
strong { color: #082a3a; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #eef3f6; padding: 0 2pt;
       color: #8a2b52; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt; font-size: 8.5pt;
        line-height: 1.45; }
th, td { border: 0.5pt solid #a9b8c4; padding: 2.6pt 4pt; vertical-align: top; }
th { background: #e3eef4; color: #0d3548; font-weight: 600; }
tr { break-inside: avoid; }
blockquote { margin: 6pt 0; padding: 5pt 8pt; background: #f4f8fa; border-left: 3pt solid #1f7fa8;
             font-size: 8.8pt; color: #2c3a45; }
blockquote p { margin: 1.5pt 0; }
hr { border: none; border-top: 0.5pt solid #c9d2dd; margin: 9pt 0; }
a { color: #10506b; text-decoration: none; }
/* header block on first page */
.hd { border-bottom: 2.5pt solid #0d3548; padding-bottom: 6pt; margin-bottom: 8pt; }
.hd-bar { height: 5mm; background: #0d3548; margin-bottom: 8pt; }
.hd-sub { font-size: 8.6pt; color: #5a7183; letter-spacing: 0.2pt; }
h1.hd-t { font-size: 21pt; border: none; background: none; padding: 0; margin: 4pt 0 0 0;
          color: #0d3548; break-before: auto; }
.hd-en { font-size: 9.4pt; color: #1f7fa8; font-weight: 600; margin-top: 1pt; }
.hd-meta { font-size: 8pt; color: #6b7785; margin-top: 5pt; line-height: 1.5; }
"""


def main():
    with open(SRC_MD, encoding="utf-8") as fh:
        md = fh.read()

    head_md = ""
    m = re.search(r"<!--HEADER-->(.*?)<!--/HEADER-->", md, re.S)
    if m:
        head_md = m.group(1)
        md = md[:m.start()] + md[m.end():]

    body = markdown.markdown(
        md,
        extensions=["tables", "attr_list", "sane_lists", "md_in_html", "fenced_code"],
    )
    # first h1 in body should not force a page break (continues after the header block)
    body = body.replace("<h1>", "<h1 class='first'>", 1)

    html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>大模型训练与推理 · 全天技术讲义</title>
<style>%s
h1.first { break-before: auto; margin-top: 10pt; }
</style></head><body>
%s
%s
</body></html>""" % (CSS, head_md, body)

    with open(HTML_OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    ok, rc, err = html_to_pdf(HTML_OUT, PDF_RAW, extra_wait=25000)
    if not ok:
        print("render FAILED rc=%s\n%s" % (rc, err))
        return 1
    print("raw pdf:", round(os.path.getsize(PDF_RAW) / 1e6, 2), "MB")

    toc = [[1, re.sub(r"[*`]", "", t).strip(), t[:14]]
           for t in re.findall(r"^# +(.+)$", md, flags=re.M)]

    out, total = stamp(
        PDF_RAW, PDF_OUT,
        header_left="大模型训练与推理 · 全天技术讲义",
        header_right="NVIDIA 开发者日 · 2026-10-16",
        footer_left="浓缩版讲义｜详细出处见《内容整理与总结分析》《讲稿整理（录音对照）》",
        footer_right="OCR + 录音转写整理",
        cover_pages=0,
        toc=toc,
    )
    print("stamped:", out, total, "pages,", round(os.path.getsize(out) / 1e6, 2), "MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
