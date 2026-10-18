# -*- coding: utf-8 -*-
"""Probe source photos: size, EXIF orientation, and build preview thumbnails."""
import glob
import os

from PIL import Image, ImageOps

SRC = r"大模型训练与推理"
WORK = r"_build\thumbs"
os.makedirs(WORK, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC, "*.jpg")))
print("count:", len(files))
for i, p in enumerate(files):
    im = Image.open(p)
    exif = im.getexif()
    orient = exif.get(274, 1)
    print(i + 1, os.path.basename(p), im.size, "orient=", orient, "mode=", im.mode)

# thumbnails for vision reading
for i, p in enumerate(files):
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im.thumbnail((1500, 1500))
    out = os.path.join(WORK, "t%03d.jpg" % (i + 1))
    im.save(out, quality=88)
print("thumbs done")
