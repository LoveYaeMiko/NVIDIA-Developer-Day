# 脚本说明

这些是从归档中提取内容、生成索引与总结所用的一次性脚本，按编号顺序执行即可复现 `智能体解析\` 下的全部派生文件。
全部为 Python 3（无第三方依赖），在 `` 目录下运行。

| 顺序 | 脚本 | 作用 | 输入 → 输出 |
|---|---|---|---|
| 1 | `01_extract_lessons.py` | 解析 12 个课时 HTML，还原成干净 Markdown | `智能体\*.html` → `_extract\lessons\*.md`、`_extract\helpers-API.md` |
| 2 | `02_extract_subtitles.py` | 字幕 JSON 转带 `[mm:ss]` 的逐句转录 | `智能体\*.json` → `_extract\*（转录）.md` |
| 3 | `03_build_outline.py` | 汇总每页章节、代码单元数、导航标签 | `智能体\*.html` → `_extract\_outline.json` |
| 4 | `04_build_refs.py` | 提取导航关键词与外部资料链接 | `_extract\_links.json` → `_extract\_refs.json` |
| 5 | `05_build_inventory.py` | 统计目录条目与体积 | `智能体\` → `_extract\_inventory.json` |
| 6 | `06_gen_index_parts.py` | 生成索引里的课时表 / 章节表 / API 表 / 资料表 | `_extract\_*.json` → `_gen\part2..4.md` |
| 7 | `07_gen_ref_appendix.py` | 生成参考资料附录 | `_extract\_refs.json` → `智能体解析\附录\外部参考资料清单.md` |
| 8 | `08_gen_recording_part.py` | 抽取录音时间轴，生成索引第 8 节 | `_extract\digests\transcripts.md` → `_gen\part5.md` |
| 9 | `09_concat_index.py` | 合成最终索引 | `_gen\part1..6.md` → `智能体解析\索引.md` |
| 10 | `10_assemble_output.py` | 整理派生文件到输出目录 | `_extract\*` → `智能体解析\课时全文|字幕转录|附录|数据\` |

## 备注

- **第 4 步依赖第 1 步之外的东西**：`_links.json` 由脚本 1 生成（`extract2.py` 里附带输出），脚本 4 读它并与 `智能体\*.html` 交叉。
- `_gen\part1.md`、`part2b.md`、`part6.md` 是**手写**的叙述段落（用法说明、主题索引、缺口说明），不由脚本生成；脚本只生成其余分块。
- 提取器刻意丢弃的内容：CodeMirror 编辑器渲染出的逐行 `<span>`、每页重复的 `helpers.*` 面板（已去重为 `helpers-API.md`）、UI 文案（"结果流式输出 · 日志 · 返回值尚未运行"等）、导航条与课程进度 SVG。
- 已知提取缺陷：纯装饰性内联标签会被丢弃，导致个别以代码标识符开头的句子缺少主语或连词。要引用原文请回看 `智能体\*.html`。
