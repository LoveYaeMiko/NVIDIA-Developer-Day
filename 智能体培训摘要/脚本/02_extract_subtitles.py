import json, sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('_extract', exist_ok=True)
for p in sorted(glob.glob(os.path.join('智能体', '*.json'))):
    base = os.path.basename(p)
    d = json.load(open(p, encoding='utf-8', errors='replace'))
    keys = sorted(d.keys(), key=lambda k: int(k))
    segs = [d[k] for k in keys]
    total = segs[-1]['end_time'] if segs else 0
    n_tr = sum(1 for s in segs if (s.get('translated_subtitle') or '').strip())
    chars = sum(len(s.get('original_subtitle') or '') for s in segs)
    print('%-52s segs=%-5d dur=%.1f min  chars=%-6d translated=%d'
          % (base[:52], len(segs), total / 60000.0, chars, n_tr))

    def ts(ms):
        ms = int(ms)
        s, msec = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return '%02d:%02d:%02d' % (h, m, s) if h else '%02d:%02d' % (m, s)

    lines = ['# 字幕转录 · ' + base.replace('.json', ''), '',
             '- 音频时长：%.1f 分钟（%d 条字幕片段）' % (total / 60000.0, len(segs)),
             '- 原文总字数：%d' % chars, '']
    for i, k in enumerate(keys):
        s = d[k]
        t = (s.get('original_subtitle') or '').strip()
        if not t:
            continue
        lines.append('[%s] %s' % (ts(s['start_time']), t))
    out = os.path.join('_extract', base.replace('.json', '') + '（转录）.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(lines))
    print('    ->', out)
