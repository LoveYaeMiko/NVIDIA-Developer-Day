# -*- coding: utf-8 -*-
"""Parse the 讯飞 ASR outputs, align slide photos to transcript windows, and
cut per-slide transcript windows.

Photo capture time (wall clock) -> audio offset:
  13:31:00 <= t < 15:31:00  -> 录音机-20261016-1331.wav, offset = t - 13:31:00
  15:31:00 <= t < 16:35:00  -> 录音机-20261016-1531.wav, offset = t - 15:31:00
"""
import glob
import json
import os
import re
from datetime import datetime, time

ASR = r"转写结果"
SRC = r"大模型训练与推理"
OUT = r"_build\audio"
os.makedirs(os.path.join(OUT, "pages"), exist_ok=True)

RECORDINGS = [
    ("录音机-20261016-0945", time(9, 45)),
    ("录音机-20261016-1103", time(11, 3)),
    ("录音机-20261016-1331", time(13, 31)),
    ("录音机-20261016-1531", time(15, 31)),
]


def parse_srt(path):
    with open(path, encoding="utf-8-sig") as fh:
        raw = fh.read().replace("\r\n", "\n").strip()
    blocks = re.split(r"\n{2,}", raw)
    segs = []
    for b in blocks:
        lines = [ln for ln in b.split("\n") if ln.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(x) for x in m.groups())
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        text = " ".join(lines[2:]).strip()
        segs.append({"start": round(start, 2), "end": round(end, 2), "text": text})
    return segs


def load_all():
    data = {}
    for name, t0 in RECORDINGS:
        srt = os.path.join(ASR, name + ".srt")
        if not os.path.exists(srt):
            print("MISSING", srt)
            continue
        segs = parse_srt(srt)
        data[name] = {"t0": t0, "segments": segs,
                      "duration": max((s["end"] for s in segs), default=0)}
        print("%s: %d segments, %.0f s (%.1f min)" % (name, len(segs), data[name]["duration"],
                                                     data[name]["duration"] / 60))
    return data


def to_sec(t):
    return t.hour * 3600 + t.minute * 60 + t.second


def photo_times():
    out = []
    for p in sorted(glob.glob(os.path.join(SRC, "IMG_*.jpg"))):
        m = re.search(r"IMG_(\d{8})_(\d{6})", os.path.basename(p))
        d, tm = m.group(1), m.group(2)
        hh, mm, ss = int(tm[:2]), int(tm[2:4]), int(tm[4:6])
        out.append({"index": len(out) + 1, "file": os.path.basename(p),
                    "hms": "%02d:%02d:%02d" % (hh, mm, ss), "sec": hh * 3600 + mm * 60 + ss})
    return out


def pick_recording(sec, data):
    for name, _ in RECORDINGS:
        if name not in data:
            continue
        t0 = to_sec(data[name]["t0"])
        span = data[name]["duration"]
        if t0 <= sec < t0 + span:
            return name, sec - t0
    return None, None


def main():
    data = load_all()
    photos = photo_times()
    aligned = []
    for i, ph in enumerate(photos):
        name, off = pick_recording(ph["sec"], data)
        nxt = photos[i + 1] if i + 1 < len(photos) else None
        name2, off2 = pick_recording(nxt["sec"], data) if nxt else (None, None)
        if name2 != name or off2 is None:
            off2 = (data[name]["duration"] if name else off + 40)
        # window: from capture time to next capture (max 90 s), plus 8 s lead-in
        start = max(0.0, off - 8.0)
        end = min(off2, off + 120.0) if off2 > off else off + 40.0
        segs = [s for s in data[name]["segments"] if s["end"] > start and s["start"] < end]
        text = " ".join(s["text"] for s in segs)
        rec = {"index": ph["index"], "file": ph["file"], "hms": ph["hms"],
               "recording": name, "audio_start": round(start, 1), "audio_end": round(end, 1),
               "n_segments": len(segs), "chars": len(text)}
        aligned.append(rec)
        with open(os.path.join(OUT, "pages", "%03d.txt" % ph["index"]), "w", encoding="utf-8") as fh:
            fh.write("# 第 %d 页  %s  拍摄 %s\n" % (ph["index"], ph["file"], ph["hms"]))
            fh.write("# 录音 %s  音频偏移 %s – %s（秒）\n\n" % (name, start, end))
            if not segs:
                fh.write("（该时间窗内无转写文本）\n")
            for s in segs:
                fh.write("[%s] %s\n" % (fmt(s["start"]), s["text"]))
    with open(os.path.join(OUT, "alignment.json"), "w", encoding="utf-8") as fh:
        json.dump(aligned, fh, ensure_ascii=False, indent=1)
    miss = [a["index"] for a in aligned if a["chars"] == 0]
    print("aligned %d pages; empty windows: %s" % (len(aligned), miss))
    print("total transcript chars in windows:", sum(a["chars"] for a in aligned))
    # per-recording coverage
    for name, _ in RECORDINGS:
        n = sum(1 for a in aligned if a["recording"] == name)
        print("  %s -> %d pages" % (name, n))


def fmt(sec):
    return "%02d:%02d:%02d" % (int(sec) // 3600, (int(sec) % 3600) // 60, int(sec) % 60)


if __name__ == "__main__":
    main()
