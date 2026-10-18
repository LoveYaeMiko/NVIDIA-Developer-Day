import os, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

GEN = '_gen'
os.makedirs(GEN, exist_ok=True)

outline = json.load(open(os.path.join('_extract', '_outline.json'), encoding='utf-8'))
refs = json.load(open(os.path.join('_extract', '_refs.json'), encoding='utf-8'))['refs']

MODULE = {'01': '模块 1 · 智能体基础（约 1 小时 / 3 页）',
          '02': '模块 2 · 高级模式（约 1 小时 / 3 页）',
          '03': '模块 3 · NemoClaw 设置（约 1 小时 / 3 页）',
          '04': '模块 4 · OpenShell 安全机制（约 1 小时 / 3 页）'}
MD_FILE = {'01a': '01a-智能体.md', '01b': '01b-ReAct循环.md', '01c': '01c-规模化工具.md',
           '02a': '02a-工作流.md', '02b': '02b-索引智能体.md', '02c': '02c-深度智能体.md',
           '03a': '03a-连接NemoClaw.md', '03b': '03b-OpenClaw.md', '03c': '03c-持续运行.md',
           '04a': '04a-OpenShell.md', '04b': '04b-现代CLI.md', '04c': '04c-深入探索.md'}
SRC = {'01a': '智能体', '01b': 'ReAct 循环', '01c': '规模化工具', '02a': '工作流',
       '02b': '索引智能体', '02c': '深度智能体', '03a': '连接 NemoClaw',
       '03b': 'OpenClaw', '03c': '持续运行', '04a': 'OpenShell',
       '04b': '现代 CLI', '04c': '深入探索'}

# ---------- part2: 课时索引 + 章节索引 ----------
L = ['## 3. 课时索引', '',
     '每个课时都有三份可查材料：**原始网页**（`智能体\\` 下，含可运行的交互单元）、'
     '**提取正文**（`课时全文\\` 下，纯文本 Markdown，可全文搜索）、**详细摘要**（`附录\\模块N-详细摘要.md`）。',
     '',
     '| 序号 | 课时 | 页面英文名 / 关键词标签 | 原始网页 | 提取正文 | 二级章节 | 三级小节 | 代码单元 |',
     '|---|---|---|---|---|---|---|---|']

for r in outline:
    lid = r['id']
    if lid == '' or lid == 'xx':
        continue
    nav = r.get('nav', '')
    nav = re.sub(r'^(The Agent|The ReAct Loop|Tools at Scale|Workflows|The Index Agent|Deep Agents|Connect NemoClaw|OpenClaw|持续运行|OpenShell|现代 CLI|深入探索)\s*', '', nav)
    src = '缺失' if not r['exists'] else '`%s · 安全智能体.html`' % SRC.get(lid, r['title'])
    md = '—' if not r.get('md') else '`%s`' % MD_FILE.get(lid, r.get('md'))
    h2s = [h for h in r.get('h2', []) if h != '新会话']
    h3s = [h for h in r.get('h3', []) if h != '参考资料']
    L.append('| %s | %s | %s | %s | %s | %d | %d | %s |' % (
        lid, r['title'], nav or '—', src, md,
        len(h2s), len(h3s),
        r.get('code_cells', '—') if r['exists'] else '—'))
L.append('')
L += ['> 「代码单元」是页面上可直接运行的交互式 JavaScript 单元个数（`cell-code-body`），'
      '课程的学习方式是"跑一遍→改一个输入→再跑"，所以它大致等于该页的实验密度。', '']
L += ['---', '', '## 4. 章节索引（每页小节 → 主题）', '',
      '用于「我记得有个讲 X 的小节，但忘了在哪一页」的场景。括号内是该页的二级章节数。', '']
for r in outline:
    if not r['exists'] or not r.get('h2'):
        if r['id'] == '04c':
            L.append('### 04c 深入探索 —— 页面缺失')
            L.append('')
            L.append('原始网页 `深入探索 · 安全智能体.html` 未保存，仅剩资源目录，'
                     '因此没有章节可索引。据导航标签与各页"参考资料"小节的链接，'
                     '该页承担 **全课程统一参考文献表（#refs）** 与「Brev · NIMs · Blueprints」等进阶路径。')
            L.append('')
        continue
    h2s = [h for h in r.get('h2', []) if h != '新会话']
    h3s = [h for h in r.get('h3', []) if h != '参考资料']
    L.append('### %s %s（%d 节）' % (r['id'], r['title'], len(h2s)))
    L.append('')
    for i, h in enumerate(h2s, 1):
        L.append('%d. %s' % (i, h))
    if h3s:
        L.append('')
        L.append('   *三级小节：*' + '；'.join(h3s))
    L.append('')
open(os.path.join(GEN, 'part2.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('part2:', len(L), 'lines')

# ---------- part3: helpers API 分组表 ----------
api = open(os.path.join('_extract', 'helpers-API.md'), encoding='utf-8').read()
groups, cur = [], None
for line in api.split('\n'):
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.strip('|').split('|')]
    if len(cells) < 2:
        continue
    a, b = cells[0], cells[1]
    if set(a) <= set('-') or not a:
        continue
    if a in ('共享状态',) or (b == '' and not a.startswith('helpers.')):
        if a in ('共享状态', '模型调用', '模型配置', 'Web 搜索', '嵌入与相似度',
                 'token 与上下文', '原始 HTTP', '可启动实例终端', 'OpenShell 策略',
                 '课程内容', '交互页面', '图表字符串', 'OpenClaw 网关', '运行控制',
                 '追踪与日志', '可视化 · helpers.viz.*'):
            cur = (a, [])
            groups.append(cur)
        continue
    if cur is not None:
        cur[1].append(a)

total = sum(len(g[1]) for g in groups)
L = ['## 6. `helpers.*` API 索引', '',
     '课程所有交互单元共用一套浏览器端辅助函数，共 **%d 条 / %d 组**（各课时内容一致，已去重）。'
     '完整签名与说明见 `附录\\helpers-API速查表.md`。' % (total, len(groups)), '',
     '| 组 | 条数 | 成员 |', '|---|---|---|']
for name, items in groups:
    L.append('| %s | %d | %s |' % (name, len(items),
             '、'.join('`%s`' % x.replace('helpers.', '') for x in items)))
L.append('')
L += ['**按用途找函数：**', '',
      '| 我想…… | 用这些 |', '|---|---|',
      '| 发一次模型请求 | `helpers.chat`、`helpers.chatStream` |',
      '| 知道当前用哪个模型/端点/有无密钥 | `helpers.getConfig`、`helpers.getKey`、`helpers.getEmbeddingConfig` |',
      '| 做检索与相似度 | `helpers.embed`、`helpers.cosineSim`、`helpers.webSearch`、`helpers.instantAnswer` |',
      '| 估算上下文预算 | `helpers.contextWindow`、`helpers.estimateTokens` |',
      '| 在沙盒/宿主上跑命令 | `helpers.terminal`、`helpers.sandboxExec`、`helpers.courseShell`、`helpers.courseRead` |',
      '| 读/评估 OpenShell 策略 | `helpers.policyGet`、`helpers.evalSandboxNetwork`、`helpers.evalSandboxFs`、`helpers.mountPolicyMap` |',
      '| 连 OpenClaw 网关对话 | `helpers.openclawChat`、`helpers.courseTurn`、`helpers.runOpenClawConnectionAudit` |',
      '| 直接读课程正文当工具 | `helpers.coursePage`、`helpers.coursePages` |',
      '| 画图解释过程 | `helpers.viz.*`（9 个）、`helpers.diagramSVG`、`helpers.ganttBarsSVG` |',
      '| 让长任务可被"停止"按钮取消 | `helpers.signal`、`helpers.delay` |',
      '']
open(os.path.join(GEN, 'part3.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('part3:', len(L), 'lines, api total:', total)

# ---------- part4: 外部资料索引（精简） ----------
ORDER = ['00', '01a', '01b', '01c', '02a', '02b', '02c', '03a', '03b', '03c', '04a', '04b', '04c']
RNAME = {'00': '课程主页', '01a': '01a 智能体', '01b': '01b ReAct 循环', '01c': '01c 规模化工具',
         '02a': '02a 工作流', '02b': '02b 索引智能体', '02c': '02c 深度智能体',
         '03a': '03a 连接 NemoClaw', '03b': '03b OpenClaw', '03c': '03c 持续运行',
         '04a': '04a OpenShell', '04b': '04b 现代 CLI', '04c': '04c 深入探索'}
grouped = {}
for r in refs:
    if len(r['pages']) >= 8:
        grouped.setdefault('通用', []).append(r)
        continue
    primary = next((p for p in ORDER if p in r['pages'] and p != '00'), r['pages'][0])
    grouped.setdefault(primary, []).append(r)

L = ['## 7. 外部参考资料索引', '',
     '课程引用了 **%d 条**外部资料（已排除课程内部导航与隐私条款链接），按首次出现的课时归并。'
     '带完整"另见"信息的版本见 `附录\\外部参考资料清单.md`。' % len(refs), '']
for lid in ORDER + ['通用']:
    if lid not in grouped:
        continue
    label = '全课程通用' if lid == '通用' else RNAME[lid]
    L.append('**%s（%d 条）**' % (label, len(grouped[lid])))
    L.append('')
    for r in grouped[lid]:
        name = (r['text'] or '').strip()
        if len(name) > 46:
            name = name[:43] + '…'
        if not name:
            name = r['href'].split('/')[2]
        L.append('- %s —— `%s`' % (name, r['href']))
    L.append('')
open(os.path.join(GEN, 'part4.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('part4:', len(L), 'lines')
