# -*- coding: utf-8 -*-
"""Post-process a Chrome-rendered PDF: stamp header/footer and build bookmarks."""
import os

import fitz

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
CJK, CJK_B = "cjk", "cjkb"


def _len(s, size, bold=False):
    return fitz.Font(fontfile=FONT_B if bold else FONT).text_length(s, size)


def stamp(pdf_in, pdf_out, header_left, header_right="", footer_left="", footer_right="",
          cover_pages=0, toc=None, search_from=None):
    doc = fitz.open(pdf_in)
    accent = (0.10, 0.28, 0.55)
    total = doc.page_count
    body_start = cover_pages + 1
    for pno in range(cover_pages, total):
        page = doc[pno]
        page.insert_font(fontname=CJK, fontfile=FONT)
        page.insert_font(fontname=CJK_B, fontfile=FONT_B)
        w, h = page.rect.width, page.rect.height
        left, right = 51.0, w - 51.0  # 18mm margins
        # header rule + text
        page.draw_line(fitz.Point(left, 44), fitz.Point(right, 44), color=(0.80, 0.83, 0.87), width=0.5)
        page.insert_text((left, 40), header_left, fontname=CJK_B, fontsize=8, color=(0.30, 0.36, 0.45))
        if header_right:
            page.insert_text((right - _len(header_right, 8), 40), header_right,
                             fontname=CJK, fontsize=8, color=(0.30, 0.36, 0.45))
        # footer rule + text
        page.draw_line(fitz.Point(left, h - 44), fitz.Point(right, h - 44), color=(0.80, 0.83, 0.87), width=0.5)
        if footer_left:
            page.insert_text((left, h - 32), footer_left, fontname=CJK, fontsize=8, color=(0.35, 0.38, 0.44))
        num = "第 %d 页 / 共 %d 页" % (pno + 1, total)
        if footer_right:
            page.insert_text((right - _len(footer_right, 8), h - 32), footer_right,
                             fontname=CJK, fontsize=8, color=(0.35, 0.38, 0.44))
        page.insert_text((right - _len(num, 8.5, True), h - 17.5), num,
                         fontname=CJK_B, fontsize=8.5, color=accent)

    # bookmarks: locate each heading's first occurrence (prefix search, tolerant)
    if toc:
        entries = []
        cursor = search_from if search_from is not None else cover_pages
        for item in toc:
            level, text = item[0], item[1]
            probe = item[2] if len(item) > 2 else text.strip()[:14]
            found = None
            for pno in range(cursor, total):
                hits = doc[pno].search_for(probe)
                if hits:
                    found = pno
                    break
            if found is None:
                for pno in range(0, total):
                    if doc[pno].search_for(probe):
                        found = pno
                        break
            if found is None:
                continue
            cursor = found
            entries.append([level, text.strip(), found + 1])
        if entries:
            doc.set_toc(entries)
    try:
        doc.subset_fonts()
    except Exception:  # noqa: BLE001
        pass
    doc.save(pdf_out, deflate=True, garbage=4, clean=True)
    doc.close()
    return pdf_out, total


if __name__ == "__main__":
    import sys
    print(stamp(sys.argv[1], sys.argv[2], "测试页眉", "右侧", "页脚左", ""))
