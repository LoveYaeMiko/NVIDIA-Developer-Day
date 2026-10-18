# -*- coding: utf-8 -*-
"""Probe PyMuPDF CJK font embedding + invisible text support."""
import fitz

cands = [
    r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\Deng.ttf",
]
for p in cands:
    try:
        f = fitz.Font(fontfile=p)
        print("OK  ", p, "| name:", f.name, "| glyph for 训:", f.has_glyph(ord("训")))
    except Exception as exc:  # noqa: BLE001
        print("FAIL", p, "|", exc)

doc = fitz.open()
page = doc.new_page(width=420, height=200)
try:
    page.insert_font(fontname="cjk", fontfile=cands[0])
    page.insert_text((20, 60), "训练 与 推理 测试 MegaMoE", fontname="cjk", fontsize=14)
    page.insert_text((20, 90), "不可见文本层 hidden text 测试", fontname="cjk", fontsize=12, render_mode=3)
    doc.subset_fonts()
    doc.save(r"_build\font_test.pdf", deflate=True, garbage=4)
    d2 = fitz.open(r"_build\font_test.pdf")
    print("text extracted:", repr(d2[0].get_text()))
    import os
    print("size:", os.path.getsize(r"_build\font_test.pdf"))
except Exception as exc:  # noqa: BLE001
    print("render FAIL:", exc)
