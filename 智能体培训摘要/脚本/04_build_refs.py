import os, sys, json, re, glob, collections
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
TITLE_TO_ID = {t: i for i, s, t in LESSON_ORDER}

BOILER = ('privacy-policy', 'privacy-center', 'API%20Trial%20Terms',
          'github-general-privacy-statement')

links = json.load(open(os.path.join('_extract', '_links.json'), encoding='utf-8'))

print('=== 课时导航标签（页面内课程地图里的英文名 + 关键词） ===')
navtags = {}
for p in sorted(glob.glob(os.path.join('智能体', '*.html'))):
    raw = open(p, encoding='utf-8', errors='replace').read()
    for href, txt in re.findall(r'<a[^>]*href="(\d\d[a-c]-[\w-]+\.html)"[^>]*>(.*?)</a>', raw, re.S):
        t = re.sub(r'<[^>]+>', ' ', txt)
        t = re.sub(r'\s+', ' ', t).replace('✓', '').replace('★', '').strip()
        if t and href not in navtags:
            navtags[href] = t

for lid, slug, title in LESSON_ORDER:
    fn = '%s-%s.html' % (lid, slug)
    print('  %-22s %-40s %s' % (fn, title, navtags.get(fn, '（未在这一页出现）')))

refs = collections.OrderedDict()
for name, lst in links.items():
    title = name.replace(' · 安全智能体', '').strip()
    lid = '00' if 'NVIDIA DLI' in title else TITLE_TO_ID.get(title, '??')
    for href, txt in lst:
        if re.match(r'^\d\d[a-c]-', href):
            continue
        if any(b in href for b in BOILER):
            continue
        refs.setdefault(href, {'text': txt, 'pages': []})
        if lid not in refs[href]['pages']:
            refs[href]['pages'].append(lid)

print('\n=== 课程引用的外部资料（跨页聚合） ===')
order = ['00', '01a', '01b', '01c', '02a', '02b', '02c', '03a', '03b', '03c', '04a', '04b', '04c']
refs_sorted = sorted(refs.items(),
                     key=lambda kv: (min(order.index(p) if p in order else 99 for p in kv[1]['pages']), kv[0]))
for href, info in refs_sorted:
    print('  [%s] %s\n        %s' % (','.join(info['pages']), info['text'][:95], href))

out = [{'href': h, 'text': i['text'], 'pages': i['pages']} for h, i in refs_sorted]
json.dump({'navtags': navtags, 'refs': out},
          open(os.path.join('_extract', '_refs.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n-> _extract/_refs.json  (%d 条外部资料)' % len(out))
