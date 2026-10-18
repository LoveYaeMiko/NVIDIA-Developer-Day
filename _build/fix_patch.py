# -*- coding: utf-8 -*-
import io
import re

p = r"_build\patch_main.py"
src = io.open(p, encoding="utf-8-sig").read()

# every PATCHES.append(( ... )) tuple must close with ))
src = src.replace("实现与参数不可平移。）'),", "实现与参数不可平移。）')),")
src = src.replace("见配套《讲稿整理》第六章。）'),", "见配套《讲稿整理》第六章。）')),")
src = src.replace("而 TPOT 未必改善甚至可能退化'),", "而 TPOT 未必改善甚至可能退化')),")
io.open(p, "w", encoding="utf-8", newline="\n").write(src)

import ast
ast.parse(src)
print("syntax OK;", len(re.findall(r"PATCHES\.append\(", src)), "appends")
