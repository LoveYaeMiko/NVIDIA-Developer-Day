# -*- coding: utf-8 -*-
"""Build the facsimile PDF of the 96 lecture photos (with invisible OCR text layer)."""
import glob
import json
import os
import re
from datetime import datetime

import fitz
from PIL import Image, ImageFilter, ImageOps

SRC = r"大模型训练与推理"
OCR = r"_build\ocr"
OUT_PDF = os.path.join(SRC, "大模型训练与推理_图片影印本.pdf")

IMG_W = 1900          # stored image width in px
JPEG_Q = 80
PAGE_W, PAGE_H = 850.0, 658.0
IMG_BOX = fitz.Rect(25.0, 40.0, 825.0, 640.0)   # 800 x 600 pt image area
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
CJK = "cjk"
CJK_B = "cjkb"

TITLE = "大模型训练与推理 · 课堂图片影印本"


def load_pages():
    pages = []
    for jf in sorted(glob.glob(os.path.join(OCR, "page_*.json"))):
        with open(jf, encoding="utf-8") as fh:
            rec = json.load(fh)
        tf = os.path.join(OCR, "text", "%03d_%s.txt" % (rec["index"], os.path.splitext(rec["file"])[0]))
        lines = []
        if os.path.exists(tf):
            with open(tf, encoding="utf-8") as fh:
                body = [ln.rstrip() for ln in fh.read().splitlines()]
            lines = [ln for ln in body[1:] if ln.strip()]
        rec["lines"] = lines
        rec["heading"] = lines[0].strip() if lines else ""
        m = re.search(r"IMG_(\d{8})_(\d{6})", rec["file"])
        rec["shot"] = "%s:%s:%s" % (m.group(2)[:2], m.group(2)[2:4], m.group(2)[4:6]) if m else ""
        rec["date"] = m.group(1) if m else ""
        pages.append(rec)
    pages.sort(key=lambda r: r["file"])
    return pages


def prep_image(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    ow, oh = im.size
    if ow != IMG_W:
        im = im.resize((IMG_W, max(1, round(oh * IMG_W / ow))), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=1)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=3))
    import io
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    return buf.getvalue(), im.size


def text(page, x, y, s, size=9, font=CJK, bold=False, color=(0.25, 0.25, 0.28), align_right_at=None):
    f = CJK_B if bold else CJK
    if align_right_at is not None:
        w = fitz.Font(fontfile=FONT_B if bold else FONT).text_length(s, size)
        x = align_right_at - w
    page.insert_text((x, y), s, fontname=f, fontsize=size, color=color)


def main():
    pages = load_pages()
    print("pages:", len(pages))
    doc = fitz.open()

    # ---------------- cover ----------------
    cov = doc.new_page(width=PAGE_W, height=PAGE_H)
    cov.insert_font(fontname=CJK, fontfile=FONT)
    cov.insert_font(fontname=CJK_B, fontfile=FONT_B)
    cov.draw_rect(fitz.Rect(0, 0, PAGE_W, 8), color=None, fill=(0.10, 0.28, 0.55))
    text(cov, 60, 120, "大模型训练与推理", size=34, bold=True, color=(0.08, 0.20, 0.42))
    text(cov, 60, 155, "课堂投影片影印本", size=20, bold=True, color=(0.15, 0.30, 0.50))
    text(cov, 60, 190, "Facsimile of On-site Lecture Slides  ·  %d pages" % len(pages), size=11)
    first, last = pages[0], pages[-1]
    meta = [
        ("来源目录", SRC),
        ("图片数量", "%d 张（%s … %s）" % (len(pages), first["file"], last["file"])),
        ("拍摄日期", "%s-%s-%s" % (first["date"][:4], first["date"][4:6], first["date"][6:]) if first["date"] else "-"),
        ("拍摄时段", "%s — %s" % (first["shot"], last["shot"])),
        ("原件规格", "%d×%d px 手机翻拍" % (first["orig_size"][0], first["orig_size"][1])),
        ("PDF 生成", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("文本层", "每页附 OCR 隐形文本层，可全文检索（Ctrl+F）"),
    ]
    y = 250
    for k, v in meta:
        text(cov, 60, y, k + "：", size=10.5, bold=True, color=(0.1, 0.1, 0.12))
        text(cov, 145, y, v, size=10.5)
        y += 24
    text(cov, 60, y + 20, "说明：图片按拍摄时间顺序排列；页脚标注原始文件名、拍摄时刻与该页识别出的标题行。", size=9)

    # ---------------- index pages ----------------
    per_page = 34
    chunks = [pages[i:i + per_page] for i in range(0, len(pages), per_page)]
    for ci, chunk in enumerate(chunks):
        p = doc.new_page(width=PAGE_W, height=PAGE_H)
        p.insert_font(fontname=CJK, fontfile=FONT)
        p.insert_font(fontname=CJK_B, fontfile=FONT_B)
        p.draw_rect(fitz.Rect(0, 0, PAGE_W, 8), color=None, fill=(0.10, 0.28, 0.55))
        text(p, 45, 60, "图片索引" + ("（续）" if ci else ""), size=18, bold=True, color=(0.08, 0.20, 0.42))
        text(p, 45, 80, "序号 / 拍摄时刻 / 该页识别标题", size=9)
        yy = 108
        for rec in chunk:
            no = rec["index"]
            head = rec["heading"] or "（未识别出标题）"
            if len(head) > 58:
                head = head[:57] + "…"
            text(p, 45, yy, "%3d" % no, size=9.5, bold=True, color=(0.10, 0.28, 0.55))
            text(p, 78, yy, rec["shot"], size=9)
            text(p, 128, yy, head, size=9)
            yy += 15.2

    # ---------------- image pages ----------------
    base = len(doc)  # pages already added
    for n, rec in enumerate(pages, 1):
        path = os.path.join(SRC, rec["file"])
        data, (iw, ih) = prep_image(path)
        p = doc.new_page(width=PAGE_W, height=PAGE_H)
        p.insert_font(fontname=CJK, fontfile=FONT)
        p.insert_font(fontname=CJK_B, fontfile=FONT_B)
        p.insert_image(IMG_BOX, stream=data, keep_proportion=True)
        # frame
        p.draw_rect(IMG_BOX, color=(0.72, 0.74, 0.78), width=0.6)
        # header / footer rules
        p.draw_line(fitz.Point(25, 32), fitz.Point(825, 32), color=(0.80, 0.82, 0.86), width=0.5)
        p.draw_line(fitz.Point(25, 646), fitz.Point(825, 646), color=(0.80, 0.82, 0.86), width=0.5)
        text(p, 25, 26, TITLE, size=9, bold=True, color=(0.18, 0.30, 0.50))
        text(p, 25, 26, "第 %d / %d 页" % (n, len(pages)), size=9, align_right_at=825)
        text(p, 25, 655, "%s · 拍摄 %s" % (rec["file"], rec["shot"]), size=8)
        head = rec["heading"] or ""
        if len(head) > 62:
            head = head[:61] + "…"
        if head:
            text(p, 25, 655, head, size=8, align_right_at=825)

        # invisible OCR text layer, mapped from original image pixels onto the page box
        ow, oh = rec["orig_size"]
        sx = IMG_BOX.width / ow
        sy = IMG_BOX.height / oh
        for b in rec["boxes"]:
            txt = (b["text"] or "").strip()
            if not txt:
                continue
            xs = [pt[0] for pt in b["box"]]
            ys = [pt[1] for pt in b["box"]]
            x0 = IMG_BOX.x0 + min(xs) * sx
            y1 = IMG_BOX.y0 + max(ys) * sy
            size = max(4.0, (max(ys) - min(ys)) * sy * 0.82)
            try:
                p.insert_text((x0, y1 - size * 0.18), txt, fontname=CJK, fontsize=size, render_mode=3)
            except Exception:  # noqa: BLE001
                pass

    # ---------------- bookmarks ----------------
    toc = [[1, "封面", 1], [1, "图片索引", 2]]
    for i, rec in enumerate(pages):
        label = "%03d %s %s" % (rec["index"], rec["shot"], (rec["heading"] or "")[:44])
        toc.append([1, label.strip(), base + i + 1])
    doc.set_toc(toc)

    doc.subset_fonts()
    doc.save(OUT_PDF, deflate=True, garbage=4, clean=True)
    doc.close()
    print("saved:", OUT_PDF, "%.1f MB" % (os.path.getsize(OUT_PDF) / 1e6))


if __name__ == "__main__":
    main()
