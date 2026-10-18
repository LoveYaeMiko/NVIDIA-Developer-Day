import os, sys, json, glob, hashlib, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')

root = '智能体'
rows = []
for name in sorted(os.listdir(root)):
    p = os.path.join(root, name)
    st = os.stat(p)
    if os.path.isdir(p):
        files, size = 0, 0
        for dp, dn, fn in os.walk(p):
            for f in fn:
                files += 1
                size += os.path.getsize(os.path.join(dp, f))
        rows.append({'name': name, 'kind': '目录', 'files': files,
                     'bytes': size, 'mtime': datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')})
    else:
        rows.append({'name': name, 'kind': '文件', 'files': 1,
                     'bytes': st.st_size,
                     'mtime': datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')})

tot_bytes = sum(r['bytes'] for r in rows)
tot_files = sum(r['files'] for r in rows)

def human(b):
    for u in ('B', 'KB', 'MB', 'GB'):
        if b < 1024 or u == 'GB':
            return '%.1f %s' % (b, u) if u != 'B' else '%d B' % b
        b /= 1024.0

print('| 类型 | 名称 | 文件数 | 大小 | 修改时间 |')
print('|---|---|---|---|---|')
for r in sorted(rows, key=lambda x: (x['kind'] != '文件', x['name'])):
    print('| %s | %s | %d | %s | %s |' % (r['kind'], r['name'], r['files'], human(r['bytes']), r['mtime']))
print('\n合计：%d 个条目 / %d 个文件 / %s' % (len(rows), tot_files, human(tot_bytes)))

json.dump({'rows': rows, 'total_bytes': tot_bytes, 'total_files': tot_files},
          open(os.path.join('_extract', '_inventory.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('-> _extract/_inventory.json')
