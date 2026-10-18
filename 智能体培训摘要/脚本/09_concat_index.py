import os, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

order = ['part1.md', 'part2.md', 'part2b.md', 'part3.md', 'part4.md', 'part5.md', 'part6.md']
chunks = []
for f in order:
    p = os.path.join('_gen', f)
    t = open(p, encoding='utf-8').read().rstrip()
    chunks.append(t)
doc = '\n\n'.join(chunks) + '\n'

dst = os.path.join('智能体解析', '索引.md')
open(dst, 'w', encoding='utf-8').write(doc)
print('索引.md written:', len(doc), 'chars,', doc.count('\n') + 1, 'lines')

# copy transcripts digest into appendix
src = os.path.join('_extract', 'digests', 'transcripts.md')
if os.path.exists(src):
    shutil.copy2(src, os.path.join('智能体解析', '附录', '授课字幕脉络.md'))
    print('appendix: 授课字幕脉络.md copied')

print('\n--- 索引.md 目录结构 ---')
for i, line in enumerate(doc.split('\n'), 1):
    if line.startswith('#'):
        print('%5d  %s' % (i, line[:90]))
