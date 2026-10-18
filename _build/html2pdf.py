# -*- coding: utf-8 -*-
"""Render an HTML file to PDF with headless Chrome/Edge."""
import os
import subprocess
import sys
import tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def html_to_pdf(html_path, pdf_path, browser=None, extra_wait=15000):
    browser = browser or (CHROME if os.path.exists(CHROME) else EDGE)
    html_path = os.path.abspath(html_path)
    pdf_path = os.path.abspath(pdf_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    profile = os.path.join(tempfile.gettempdir(), "dsh_pdf_profile")
    url = "file:///" + html_path.replace("\\", "/").replace(" ", "%20")
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        "--virtual-time-budget=%d" % extra_wait,
        "--run-all-compositor-stages-before-draw",
        "--user-data-dir=" + profile,
        "--print-to-pdf=" + pdf_path,
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000
    return ok, proc.returncode, (proc.stderr or "")[-1500:]


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    ok, rc, err = html_to_pdf(src, dst)
    print("ok=%s rc=%s size=%s" % (ok, rc, os.path.getsize(dst) if os.path.exists(dst) else -1))
    if not ok:
        print(err)
