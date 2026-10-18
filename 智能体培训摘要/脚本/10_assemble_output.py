import os, sys, shutil, json, glob
sys.stdout.reconfigure(encoding='utf-8')

OUT = '智能体解析'
dirs = {
    'lessons': os.path.join(OUT, '课时全文'),
    'subs': os.path.join(OUT, '字幕转录'),
    'appendix': os.path.join(OUT, '附录'),
    'data': os.path.join(OUT, '数据'),
    'scripts': os.path.join(OUT, '脚本'),
}
for d in dirs.values():
    os.makedirs(d, exist_ok=True)

# 1) lessons
LESSON_ORDER = ['00', '01a', '01b', '01c', '02a', '02b', '02c',
                '03a', '03b', '03c', '04a', '04b']
NAME_MAP = {
    '00': '00-课程主页',
    '01a': '01a-智能体',
    '01b': '01b-ReAct循环',
    '01c': '01c-规模化工具',
    '02a': '02a-工作流',
    '02b': '02b-索引智能体',
    '02c': '02c-深度智能体',
    '03a': '03a-连接NemoClaw',
    '03b': '03b-OpenClaw',
    '03c': '03c-持续运行',
    '04a': '04a-OpenShell',
    '04b': '04b-现代CLI',
}
n = 0
for lid in LESSON_ORDER:
    cands = glob.glob(os.path.join('_extract', 'lessons', lid + '-*.md'))
    if not cands:
        print('MISSING lesson extract:', lid)
        continue
    dst = os.path.join(dirs['lessons'], NAME_MAP[lid] + '.md')
    shutil.copy2(cands[0], dst)
    n += 1
print('lessons copied:', n)

# 2) transcripts
subs = {
    '【原始字幕】录音机-20261015-0935-B 接口-英语（转录）.md': '录音一-0935（约120分钟）.md',
    '【原始字幕】录音机-20261015-1135-B 接口-英语（转录）.md': '录音二-1135（约59分钟）.md',
}
for src, dst in subs.items():
    p = os.path.join('_extract', src)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dirs['subs'], dst))
        print('transcript:', dst)
    else:
        print('MISSING transcript:', src)

# 3) appendix: helpers API + module digests
shutil.copy2(os.path.join('_extract', 'helpers-API.md'),
             os.path.join(dirs['appendix'], 'helpers-API速查表.md'))
for i in (1, 2, 3, 4):
    p = os.path.join('_extract', 'digests', 'module-%d.md' % i)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dirs['appendix'], '模块%d-详细摘要.md' % i))

# 4) data
for f in ('_outline.json', '_refs.json', '_terms.json', '_links.json', '_inventory.json'):
    p = os.path.join('_extract', f)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dirs['data'], f.lstrip('_')))

# 5) scripts
for f in glob.glob(os.path.join('_tools', '*.py')):
    shutil.copy2(f, os.path.join(dirs['scripts'], os.path.basename(f)))

print('\n--- 输出目录树 ---')
for dp, dn, fn in os.walk(OUT):
    depth = dp.replace(OUT, '').count(os.sep)
    print('  ' * depth + os.path.basename(dp) + '/')
    for f in sorted(fn):
        sz = os.path.getsize(os.path.join(dp, f))
        print('  ' * (depth + 1) + '%-40s %8.1f KB' % (f, sz / 1024.0))
