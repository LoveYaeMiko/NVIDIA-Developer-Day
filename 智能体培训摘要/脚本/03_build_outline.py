import os, sys, re, json, glob, collections
sys.stdout.reconfigure(encoding='utf-8')

LESSON_ORDER = [
    ('01a', 'loop', '智能体'),
    ('01b', 'react', 'ReAct 循环'),
    ('01c', 'tools', '规模化工具'),
    ('02a', 'routing', '工作流'),
    ('02b', 'rag', '索引智能体'),
    ('02c', 'deep', '深度智能体'),
    ('03a', 'kickstart', '连接 NemoClaw'),
    ('03b', 'openclaw', 'OpenClaw'),
    ('03c', 'always-on', '持续运行'),
    ('04a', 'safety', 'OpenShell'),
    ('04b', 'modern-clis', '现代 CLI'),
    ('04c', 'going-further', '深入探索'),
]
refs = json.load(open(os.path.join('_extract', '_refs.json'), encoding='utf-8'))
navtags = refs['navtags']

rows = []
for lid, slug, title in LESSON_ORDER:
    fn = '%s-%s.html' % (lid, slug)
    src = os.path.join('智能体', title + ' · 安全智能体.html')
    md = None
    for cand in glob.glob(os.path.join('_extract', 'lessons', lid + '-*.md')):
        md = cand
    info = {'id': lid, 'file': fn, 'title': title,
            'nav': navtags.get(fn, ''), 'exists': os.path.exists(src)}
    if not info['exists']:
        info['md'] = None
        rows.append(info)
        continue
    raw = open(src, encoding='utf-8', errors='replace').read()
    txt = open(md, encoding='utf-8').read() if md else ''
    # module/lesson counter
    m = re.search(r'class="eyebrow"[^>]*>(.*?)</div>', raw, re.S)
    info['eyebrow'] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    info['h2'] = [t for t in re.findall(r'<h2[^>]*>(.*?)</h2>', raw, re.S)]
    info['h2'] = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip() for t in info['h2']]
    info['h2'] = [t for t in info['h2'] if t]
    info['h3'] = [t for t in re.findall(r'<h3[^>]*>(.*?)</h3>', raw, re.S)]
    info['h3'] = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip() for t in info['h3']]
    info['h3'] = [t for t in info['h3'] if t]
    info['code_cells'] = len(re.findall(r'cell-code-body', raw))
    info['md_chars'] = len(txt)
    info['md'] = os.path.basename(md) if md else None
    rows.append(info)

for r in rows:
    print('%-4s %-14s %-8s 代码单元=%-2s md=%6s 字符  %s'
          % (r['id'], r['title'], '有页面' if r['exists'] else '缺页面',
             r.get('code_cells', '-'), r.get('md_chars', '-'), r['nav']))
    if r.get('eyebrow'):
        print('     eyebrow:', r['eyebrow'])
    for h in r.get('h2', []):
        print('     ##', h)
    for h in r.get('h3', []):
        print('        ###', h)

json.dump(rows, open(os.path.join('_extract', '_outline.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n-> _extract/_outline.json')
