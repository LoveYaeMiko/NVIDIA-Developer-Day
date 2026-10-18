# -*- coding: utf-8 -*-
import fitz

p = r"大模型训练与推理\大模型训练与推理_内容整理与总结分析.pdf"
d = fitz.open(p)
t = "\n".join(d[i].get_text() for i in range(d.page_count))
fence = "`" * 3
print("triple-backticks:", t.count(fence))
print("cost formula present:", "Cost = Prefill" in t)
for line in t.splitlines():
    if "Cost = Prefill" in line:
        print("  ->", line)
print("total chars:", len(t), "pages:", d.page_count)
