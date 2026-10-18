# -*- coding: utf-8 -*-
"""v2: clean markdown extraction from saved NVIDIA DLI lesson pages.

Outputs:
  _extract/lessons/<id>-<title>.md    cleaned lesson body
  _extract/helpers-API.md             de-duplicated course helper API reference
  _extract/_links.json                external link inventory per page
"""
import os, re, sys, glob, json
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

VOID = {'br', 'img', 'input', 'hr', 'meta', 'link', 'source', 'col', 'area',
        'base', 'embed', 'param', 'track', 'wbr'}
SKIP_TAGS = {'script', 'style', 'svg', 'button', 'input', 'textarea', 'select',
             'option', 'noscript', 'label', 'iframe', 'canvas', 'template'}
SKIP_IDS = {'journey-map', 'nav'}
SKIP_CLASS_RE = re.compile(
    r'(^|\s)(CodeMirror[\w-]*|cf-helpers-source-row|cf-helpers-src-editor|'
    r'cf-jm[\w-]*|dli-ui[\w-]*|cm-[\w-]+|cell-actions|cf-code-copy|'
    r'cf-panel-reset|cf-panel-runone|heading-anchor|heading-permalink|'
    r'cf-helpers-status|cf-helpers-apply|cf-helpers-revert)(\s|$)')

CHROME = {
    '**JS async (state, helpers) => { … }**',
    '**结果流式输出 · 日志 · 返回值尚未运行**',
    '**辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**',
    '**辅助函数位于此单元格的作用域内。点击行可查看其源代码**',
    '在您运行前为空', '就绪', '。', '**模型与上下文选项**',
    '**AI 辅助内容 · 人工审核**', '课程原创文字、示例代码和原始图表采用',
    '许可。注明名称的外部资料沿用各自条款；请参阅',
    'NVIDIA 隐私政策 ·隐私权利与请求 ·NVIDIA API 试用条款 ·GitHub 托管隐私说明',
    '浏览器会保存对话和课程偏好设置；发送消息时，所选 AI 服务会处理输入。删除本地会话不会删除服务端记录。请使用虚构、非机密的数据，并遵守所选服务的条款。',
    '本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN ·资料来源EN .',
}

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


class Node(object):
    __slots__ = ('tag', 'attrs', 'children', 'parent')

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent

    def cls(self):
        return self.attrs.get('class', '') or ''


class TreeBuilder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node('#root', {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs), self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def norm(s):
    s = s.replace('\u200b', '').replace('\u00a0', ' ')
    return re.sub(r'[ \t\r\n]+', ' ', s).strip()


def text_of(node):
    if isinstance(node, str):
        return node
    if node.tag in SKIP_TAGS:
        return ''
    return ''.join(text_of(c) for c in node.children)


def is_skipped(node):
    if node.tag in SKIP_TAGS:
        return True
    if node.attrs.get('id') in SKIP_IDS:
        return True
    c = node.cls()
    if c and SKIP_CLASS_RE.search(c):
        return True
    if 'hidden' in node.attrs:
        return True
    return False


def cm_code(node):
    out = []

    def walk(n):
        if isinstance(n, str):
            return
        if n.tag == 'pre' and 'CodeMirror-line' in n.cls():
            t = text_of(n).replace('\u200b', '')
            if t.strip() and 'xxxxxxxxxx' not in t:
                out.append(t.rstrip())
            return
        for c in n.children:
            walk(c)

    walk(node)
    return out


def render(node, out):
    if isinstance(node, str):
        t = norm(node)
        if t:
            out.append(('text', t))
        return
    if is_skipped(node):
        return
    tag, cls = node.tag, node.cls()

    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        t = norm(text_of(node))
        if t:
            out.append(('h', int(tag[1]), t))
        return
    if tag == 'p':
        inner = []
        for c in node.children:
            render(c, inner)
        parts = []
        for kind, val in inner:
            if kind in ('inline', 'text'):
                parts.append(val)
        para = norm(''.join(p if isinstance(p, str) else p[1]
                            for p in [(k, v) for k, v in inner
                                      if k in ('inline', 'text')]))
        if para:
            out.append(('p', para))
        return
    if tag in ('ul', 'ol'):
        items, idx = [], 0
        for c in node.children:
            if isinstance(c, Node) and c.tag == 'li' and not is_skipped(c):
                idx += 1
                t = norm(text_of(c))
                if t:
                    items.append(('- ' if tag == 'ul' else '%d. ' % idx) + t)
        if items:
            out.append(('list', items))
        return
    if tag == 'table':
        rows = []

        def collect(n):
            if isinstance(n, str) or is_skipped(n):
                return
            if n.tag == 'tr':
                cells = [norm(text_of(c)) for c in n.children
                         if isinstance(c, Node) and c.tag in ('td', 'th')]
                if any(cells):
                    rows.append(cells)
                return
            if n.tag == 'table' and n is not node:
                return
            for c in n.children:
                collect(c)

        collect(node)
        if rows:
            out.append(('table', rows))
        return
    if tag == 'figcaption':
        t = norm(text_of(node))
        if t:
            out.append(('caption', t))
        return
    if tag == 'pre' or 'cf-code-view' in cls:
        lines = cm_code(node)
        if lines:
            out.append(('code', lines))
        return
    if tag == 'summary':
        t = norm(text_of(node))
        if t:
            out.append(('summary', t))
        return
    if tag in ('strong', 'b', 'em', 'i', 'code', 'a', 'span', 'kbd', 'sup',
               'sub', 'mark', 'small', 'u', 's'):
        t = norm(text_of(node))
        if t:
            out.append(('inline', t))
        return
    for c in node.children:
        render(c, out)


def table_sig(rows):
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def to_md(blocks, helper_sink=None, seen_tables=None):
    lines = []
    for b in blocks:
        kind = b[0]
        if kind == 'h':
            lines.append('')
            lines.append('#' * b[1] + ' ' + b[2])
            lines.append('')
        elif kind in ('p', 'text', 'inline'):
            if b[1] in CHROME:
                continue
            lines.append(b[1])
            lines.append('')
        elif kind == 'list':
            lines.extend(b[1])
            lines.append('')
        elif kind == 'table':
            rows = b[1]
            if rows and rows[0] and rows[0][0].startswith('共享状态'):
                if helper_sink is not None and not helper_sink:
                    helper_sink.extend(rows)
                continue
            sig = table_sig(rows)
            if seen_tables is not None:
                if sig in seen_tables:
                    continue
                seen_tables.add(sig)
            w = max(len(r) for r in rows)
            rows = [r + [''] * (w - len(r)) for r in rows]
            lines.append('| ' + ' | '.join(rows[0]) + ' |')
            lines.append('|' + '|'.join(['---'] * w) + '|')
            for r in rows[1:]:
                lines.append('| ' + ' | '.join(r) + ' |')
            lines.append('')
        elif kind == 'caption':
            lines.append('*' + b[1] + '*')
            lines.append('')
        elif kind == 'code':
            lines.append('```')
            lines.extend(b[1])
            lines.append('```')
            lines.append('')
        elif kind == 'summary':
            t = b[1]
            if t in ('章节',):
                continue
            lines.append('**▸ ' + t + '**')
            lines.append('')
    return '\n'.join(lines)


def extract(path, helper_sink=None):
    raw = open(path, encoding='utf-8', errors='replace').read()
    tb = TreeBuilder()
    tb.feed(raw)
    main = [None]

    def find(n):
        if isinstance(n, str) or main[0] is not None:
            return
        if n.tag == 'main':
            main[0] = n
            return
        for c in n.children:
            find(c)

    find(tb.root)
    blocks = []
    render(main[0] or tb.root, blocks)
    md = to_md(blocks, helper_sink, set())
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip() + '\n'


def links_of(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for href, txt in re.findall(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', raw, re.S):
        if 'dli-2e7a0982d9ae45d38e5988ab627955a4' in href:
            continue
        if href.startswith('#') or href.startswith('javascript'):
            continue
        t = norm(re.sub(r'<[^>]+>', '', txt))
        out.append((href, t))
    seen, uniq = set(), []
    for h, t in out:
        if h in seen:
            continue
        seen.add(h)
        uniq.append((h, t))
    return uniq


if __name__ == '__main__':
    os.makedirs(os.path.join('_extract', 'lessons'), exist_ok=True)
    helper = []
    linkmap = {}
    for p in sorted(glob.glob(os.path.join('智能体', '*.html'))):
        name = os.path.basename(p)[:-5]
        title = name.replace(' · 安全智能体', '').strip()
        lid = TITLE_TO_ID.get(title)
        if lid is None:
            if 'NVIDIA DLI' in title:
                lid = '00'
                short = '课程主页'
            else:
                lid = 'xx'
                short = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title)[:24]
        else:
            short = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title)[:24]
        md = extract(p, helper)
        outp = os.path.join('_extract', 'lessons', '%s-%s.md' % (lid, short))
        open(outp, 'w', encoding='utf-8').write(md)
        linkmap[name] = links_of(p)
        print('%-46s -> %-46s %6d chars' % (name[:46], os.path.basename(outp), len(md)))

    if helper:
        w = max(len(r) for r in helper)
        helper = [r + [''] * (w - len(r)) for r in helper]
        sl = ['# 课程辅助函数 API 参考（helpers.*）', '',
              '本表由课程交互式代码单元中的“辅助函数”面板汇总而来，在全部 11 个课时中内容一致，'
              '此处去重后单列，作为查阅用的速查表。', '',
              '| ' + ' | '.join(helper[0]) + ' |',
              '|' + '|'.join(['---'] * w) + '|']
        for r in helper[1:]:
            sl.append('| ' + ' | '.join(r) + ' |')
        open(os.path.join('_extract', 'helpers-API.md'), 'w',
             encoding='utf-8').write('\n'.join(sl) + '\n')
        print('\nhelpers-API.md rows:', len(helper) - 1)

    json.dump(linkmap, open(os.path.join('_extract', '_links.json'), 'w',
                            encoding='utf-8'), ensure_ascii=False, indent=1)
    print('link pages:', len(linkmap))
