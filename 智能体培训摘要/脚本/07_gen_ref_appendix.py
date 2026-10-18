import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

refs = json.load(open(os.path.join('_extract', '_refs.json'), encoding='utf-8'))['refs']

RNAME = {'01a': '01a 智能体', '01b': '01b ReAct 循环', '01c': '01c 规模化工具',
         '02a': '02a 工作流', '02b': '02b 索引智能体', '02c': '02c 深度智能体',
         '03a': '03a 连接 NemoClaw', '03b': '03b OpenClaw', '03c': '03c 持续运行',
         '04a': '04a OpenShell', '04b': '04b 现代 CLI', '04c': '04c 深入探索',
         '00': '00 课程主页'}

# primary lesson = first non-00 page in list order
ORDER = ['00', '01a', '01b', '01c', '02a', '02b', '02c', '03a', '03b', '03c', '04a', '04b', '04c']
grouped = {}
for r in refs:
    pages = r['pages']
    if len(pages) >= 8:
        grouped.setdefault('通用', []).append(r)
        continue
    primary = next((p for p in ORDER if p in pages and p != '00'), pages[0])
    grouped.setdefault(primary, []).append(r)

lines = ['# 附录 · 外部参考资料清单（按课时归并）', '',
         '本清单从 12 个已保存页面的超链接中提取，去掉了课程内部导航链接与 NVIDIA 隐私/条款类链接，'
         '按“首次引用的课时”归并。同一资料在多个课时被引用时，在“另见”中列出。', '',
         '共 %d 条资料。' % len(refs), '']

for lid in ORDER + ['通用']:
    if lid not in grouped:
        continue
    items = grouped[lid]
    label = '全课程通用（出现在 8 个及以上页面）' if lid == '通用' else RNAME[lid]
    lines.append('## %s（%d 条）' % (label, len(items)))
    lines.append('')
    lines.append('| # | 名称（页面锚文本） | 链接 | 另见 |')
    lines.append('|---|---|---|---|')
    for i, r in enumerate(items, 1):
        name = (r['text'] or '').replace('|', '\\|').strip()
        if len(name) > 60:
            name = name[:57] + '…'
        if not name:
            name = '（无锚文本）'
        others = [p for p in r['pages'] if p != lid]
        see = '、'.join(others) if others else '—'
        lines.append('| %d | %s | <%s> | %s |' % (i, name, r['href'], see))
    lines.append('')

open(os.path.join('智能体解析', '附录', '外部参考资料清单.md'), 'w',
     encoding='utf-8').write('\n'.join(lines))
print('written, items:', len(refs))
print('\n'.join(lines[:14]))
