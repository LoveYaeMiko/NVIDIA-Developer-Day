import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

d = open(os.path.join('_extract', 'digests', 'transcripts.md'), encoding='utf-8').read()


def between(text, start_marker, end_marker, occurrence=1):
    idx = -1
    pos = 0
    for _ in range(occurrence):
        idx = text.find(start_marker, pos)
        if idx < 0:
            return ''
        pos = idx + len(start_marker)
    j = text.find(end_marker, pos)
    if j < 0:
        j = len(text)
    return text[idx + len(start_marker):j].strip()


# Rec1 timeline = first '### 时间轴分段', Rec2 = second
t1 = between(d, '### 时间轴分段', '### 老师强调的重点', 1)
t2 = between(d, '### 时间轴分段', '### 老师强调的重点', 2)
mapping = between(d, '**与 12 个课时页面的对应关系**', '## 原文金句摘录', 1)
quotes = between(d, '## 原文金句摘录', '\x00')

# keep only table lines from mapping
mtable = '\n'.join(l for l in mapping.split('\n')
                   if l.startswith('|')).strip()
extra = [l for l in mapping.split('\n') if l.startswith('补充：')]
extra = extra[0] if extra else ''

L = []
L.append('## 8. 录音与字幕索引')
L.append('')
L.append('### 8.1 三个文件的关系')
L.append('')
L.append('| 文件 | 内容 | 规模 |')
L.append('|---|---|---|')
L.append('| `录音机-20261015-0935.wav` | 原始录音（第一段） | 1.9 GB |')
L.append('| `录音机-20261015-1135.wav` | 原始录音（第二段） | 978.6 MB |')
L.append('| `【原始字幕】录音机-20261015-0935-B 接口-英语.json` | 第一段的语音识别结果 | 3356 条字幕 / 时间轴 0–120.0 分钟 |')
L.append('| `【原始字幕】录音机-20261015-1135-B 接口-英语.json` | 第二段的语音识别结果 | 1723 条字幕 / 时间轴 0–59.3 分钟 |')
L.append('')
L.append('JSON 结构为 `{"序号": {start_time, end_time, original_subtitle, translated_subtitle}}`，'
         '时间是毫秒；**`translated_subtitle` 全部为空**，没有任何人工校对或翻译，'
         '`original_subtitle` 是实时语音识别的原始中文，含大量同音错字（如 OpenClaw 被识别成"open cloud / 小龙虾"，'
         'NemoClaw 被识别成"NEO 克洛 / 柠檬 co"，RAG 被识别成"right / ride"，harness 被识别成"哈里斯"）。')
L.append('')
L.append('已转成可读、可搜索的带时间戳文本，放在 `字幕转录\\`：')
L.append('')
L.append('| 提取文件 | 覆盖 | 行数特征 |')
L.append('|---|---|---|')
L.append('| `录音一-0935（约120分钟）.md` | 00:00–01:59:56，3356 条 | 每行 `[mm:ss] 原文` |')
L.append('| `录音二-1135（约59分钟）.md` | 00:00–59:18，1723 条 | 每行 `[mm:ss] 原文` |')
L.append('')
L.append('### 8.2 结论：这是同一场 3 小时课，被切成两个文件')
L.append('')
L.append('不是上午/下午两场，也不是两节课。依据：')
L.append('')
L.append('1. **句子跨文件接续**：录音一最后一句停在 `[01:59:56]「就是说你哪些这个…可执行」`，'
         '录音二第一句是 `[00:00]「…系统调用，因为系统调用的是比较危险的执行」`，拼起来是一句话。')
L.append('2. **时间对得上**：09:35 + 120 分钟 = 11:35，正好是第二个文件的起始时间；'
         '合计约 179 分钟，与讲师反复说的"我们只有三个小时"吻合。')
L.append('3. **内容接续**：录音一末尾刚开始讲安全策略三方面（文件系统 / 进程 / 网络），'
         '录音二开头接着讲进程与系统调用。')
L.append('4. **场景一致**：同一批学员（有奖问答延续）、同一个实验环境、同一场开发者日（"楼下有 OpenClaw 安装专场"）。')
L.append('')
L.append('### 8.3 录音一时间轴（09:35 起，约 120 分钟）')
L.append('')
L.append(t1)
L.append('')
L.append('### 8.4 录音二时间轴（11:35 起，约 59 分钟）')
L.append('')
L.append(t2)
L.append('')
L.append('### 8.5 录音 → 课时对照')
L.append('')
L.append(mtable)
L.append('')
if extra:
    L.append('> ' + extra)
    L.append('')
L.append('### 8.6 讲师原话金句（最能说明课程立场）')
L.append('')
L.append(quotes)
L.append('')
L.append('> 完整的讲解脉络（老师强调的重点、现场演示的每一步操作、学员提问与解答、课程定位与学习方法）'
         '见 `附录\\授课字幕脉络.md`。')
L.append('')
open(os.path.join('_gen', 'part5.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('part5 lines:', len(L))
print('t1 len', len(t1), 't2 len', len(t2), 'map len', len(mtable), 'quotes len', len(quotes))
