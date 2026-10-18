# 附录 A：逐页索引表（96 张）

下表为全部 96 张照片的索引：序号即整理编号（与影印本、第六章逐页整理一一对应），时间为照片拍摄时刻，标题为识别出的首页标题行，字数为该页识别到的有效字符数。重复拍摄页与文字量偏少的页面在备注中标出。

{{PAGE_INDEX}}

# 附录 B：OCR 处理与可靠性说明

## B.1 处理方法

| 环节 | 做法 |
|---|---|
| 预处理 | 读取 EXIF 方向 → 转 RGB → 生成最长边 2600 px 的识别副本（保留原图坐标映射，便于把识别框回贴到影印本的隐匿文本层） |
| 识别引擎 | RapidOCR 1.4.4（PP-OCRv4 检测 + 方向分类 + 识别模型，ONNX Runtime CPU 推理），中英混合字典 |
| 并行 | 9 进程 × 每进程 2 个 ONNX 线程；96 页总耗时约 4 分钟 |
| 阅读顺序还原 | 按识别框垂直中心聚类成"行"，行内按左边界排序；解决双栏/多块式投影片的串读问题 |
| 质地检 | 统计每页文本量、平均置信度、低分框（<0.60）数量；对最弱 8 页做 3800 px 二次识别并择优 |
| 人工校核 | 逐条核对英文单词粘连、符号（`·`）、乱码与中英混排；不确定处标 `(?)` |

## B.2 质量统计

| 指标 | 数值 |
|---|---|
| 页数 | 96（无缺页） |
| 识别字符总数 | 60,024 |
| 平均置信度 | 0.947（仅第 31 页低于 0.80） |
| 重复/重拍页 | 3 组：4–5、39–40、41–42 |
| 文字量最少 | 见附录 A"备注"列 |

## B.3 二次（高分辨率）识别补充

以下页面的第一次识别质量偏低，已用最长边 3800 px 重跑，互为补充：

- **第 31 页（Optimization 10: Scheduler Groups and the `fc1_done` Spin）** 二次识别恢复了三条关键信息：① 调度器**按组**派发，"先派一组专家的全部 FC1 tile，再派它们的 FC2 tile"，默认 group = 一个波次；② 小 bucket 下每个专家只有 1 个 token tile 却有 48 个 FC1 tile，一个组只装得下 1–3 个专家，于是 FC2 tile 紧跟在自家 FC1 tile 后面、在其尚未算完时到达；③ **把 group 扩大到 264（≈6 个专家）后，FC2 tile 到达时 `fc1_done` 已完成，自旋消失**。原第一次识别只保留了"activation TMA producer 约 25% 时间在自旋"这一条。
- **第 84 页（Observability – Dynamo Provider Plugin）** 第一次识别被界面元素严重分割；二次识别确认该页是一张 **trace 可视化截图**：时间轴 `00:02:20 → 00:04:00`、lane 名形如 `swebench_pl_8task...`、`traj-astropy_astropy-693/774`、`traj-django_django-109`、`tool:bash`，并可见模型标签 `Qwen3.5-27B` 与"NVIDIA"标识。该页**不含技术论点**，属于工具/可观测性演示。
- **第 26 页（Why Gate/Up Interleave = 8: the WGMMA Register Layout）** 二次识别得到 171 个文本框（首次仅 15 个），确认该页是一张 `T32–T35` 线程与 `(d0,d1)`/`(d4,d5)` 数据对的寄存器布局表；具体逐格对应仍**不保证正确**，正文只引用其结论（interleave = 8 由 WGMMA 寄存器布局决定）。
- **第 18 页（Warp Specialization）** 的 `Warps / setmaxnreg / Duty` 三列表格存在串行，逐行数值不确定；只有页面明写的 `20 warps / 640 threads` 可靠。

## B.4 引用时的注意事项

1. 正文中的**加粗数字**均取自幻灯片文字层或图注，未做换算；若与你的复现结果不符，请先核对原图（影印本第 5–100 页为逐页原图）。
2. 图表类页面（如第 33、45、60、63、64、76、83、86、88、93 页）的**柱高/曲线高度**没有可靠数值，本文只引用幻灯片上用文字写出的结论倍数，不根据像素估计。
3. 中文页（第 68–96 页为主）存在少量识别别字（如"缓存"→"媛存"），已按上下文修正，不影响结论。

# 附录 C：术语与缩写对照

| 缩写/术语 | 全称或含义 | 在材料中的语境 |
|---|---|---|
| MoE | Mixture-of-Experts | 细粒度专家层（DeepSeekMoE） |
| MegaMoE | — | 本场提出的融合 dispatch/FC1/FC2/combine 的单持久内核 |
| EP / TP / PP / CP / DP | Expert / Tensor / Pipeline / Context / Data Parallel | 并行维度；本例初始布局 PP4 + EP64，CP16（64K）/ CP64（1M） |
| dispatch / combine | all-to-all 发送与收回 | MoE 的通信两段 |
| FC1 / FC2 | MoE 中的两层专家 FFN | FC1 含 SwiGLU 与 FP8 cast |
| swapAB | 交换 A/B 操作数（把 token 映射到 N 维） | 小 token 场景的 tile 利用率手段 |
| tile / tileN | 计算分块 / N 方向分块 | 256×256、`M64×N128`、`M128/256×N8` |
| WGMMA | Warpgroup Matrix-Multiply-Accumulate | SM90 起的 warp-group 级 MMA |
| TMA | Tensor Memory Accelerator | 异步张量搬运；S2G / G2S |
| TMEM | Tensor Memory | Blackwell 上的张量存储；TMEM-DP 为其数据通路 |
| LDTM / STTM | Load/Store TMEM | 出入 TMEM 的指令 |
| R2S | Register to Shared | epilogue 中寄存器到 SMEM 的搬运 |
| STG.32 / STG.128 | 32-bit / 128-bit 全局写指令 | 第 32 页把 8×STG.32 合成 1×STG.128 |
| setmaxnreg | 设置每 warp 寄存器上限 | warp specialization 的预算分配 |
| MEMBAR / UREDGR | 内存屏障 / 异步归约指令 | 同步优化（batch-commit、async UREDGR） |
| SMEM / HBM / SM | 共享内存 / 高带宽显存 / 流式多处理器 | 228 KB SMEM 预算、53 GB/rank 等 |
| NVFP4 / MXFP8 / FP8 / BF16 / FP32 | 数值格式 | 计算与 combine 的精度组合 |
| per_tensor / blockwise | 量化缩放粒度 | per-expert 标量 vs 128×128 块 |
| DeepGEMM / CUTLASS / CuTe / CuteDSL | 内核库/DSL | baseline 与实现载体 |
| NVSHMEM / NCCL / GIN | 单边通信库 / 集合通信库 / GPU-initiated 网络 | dispatch/combine 与 all-gather |
| NIXL | NVIDIA 推理传输库 | 点对点 KV 拉取 |
| CGA | Cluster Group Array（SM90 簇） | 2×2 CGA + TMA multicast |
| TTFT / TPOT / ISL / OSL | 首 token 时间 / 每输出 token 时间 / 输入长度 / 输出长度 | 服务指标 |
| E2E / SLA / QPS | 端到端 / 服务等级协议 / 每秒查询 | 智能体场景的轨迹级指标 |
| KV Cache | 键值缓存 | 推理显存的主要占用者 |
| TurboQuant / KVTC / nvCOMP-ANS | 三条 KV 压缩路线 | 在线量化 / PCA 压缩 / 无损熵编码 |
| KV Router / Flash Indexer | 缓存感知路由 / 前缀索引服务 | Dynamo 体系组件 |
| Dynamo | NVIDIA 推理服务框架 | 含 KV Router、provider plugin、VeRL 集成 |
| DEP | Disaggregated Expert Parallel（材料中与 KV offload/亲和路由一起出现） | 第 85–89 页的容量对比对象 |
| MLA / DSA | Multi-head Latent Attention / DeepSeek Sparse Attention | 每 token KV 体积拆分（43.9 / 9.8） |
| CSA / HCA | 混合注意力的两条路径 | DeepSeek-V4 结构图 |
| MTP | Multi-Token Prediction | 结构图中的 MTP Modules（MTP Loss） |
| AgentX | 智能体会话 trace 基准/仪表盘 | 第 79–83 页 |
| ThunderAgent | 会话网关（program 状态机 + 全局控制回路） | 第 91–96 页 |
| AA-AgentPerf | 满足 SLA 的最大并发 agent 数 | 第 79 页 SLA 表 |
| VeRL | 强化学习训练框架 | 第 95 页 rollout 集成 |
| SWE-Bench Lite | 软件工程智能体基准 | 第 93、95 页实测 |
| nsys / Nsight | NVIDIA 性能分析器 | block size 由 silicon time 决定 |

# 附录 D：产出文件与复现方式

| 文件 | 说明 |
|---|---|
| `大模型训练与推理_图片影印本.pdf` | 96 页原图影印（1 页封面 + 3 页索引 + 96 页图片），每页附**隐形 OCR 文本层**，可全文检索；书签按页标题生成，页脚标注原始文件名与拍摄时刻 |
| `大模型训练与推理_内容整理与总结分析.pdf` | 本文件：摘要 → 资料与方法 → 全篇脉络 → 技术主线剖析 → 总结 → 分析与评论 → 逐页要点整理 → 附录 |
| `大模型训练与推理_内容整理与总结分析.md` | 本文的可编辑源稿（Markdown），便于再加工或导出其它格式 |
| `大模型训练与推理_讲稿整理（录音对照）.pdf` | 配套文件：现场录音转写与投影片的时间轴对照、逐页口头要点、四场问答，以及本文的修订清单 |
| `_build/ocr/text/*.txt` | 每页的 OCR 纯文本（阅读顺序） |
| `_build/ocr/page_*.json` | 每页的识别框、文本与置信度（原图坐标），用于生成影印本文本层 |
| `_build/notes/seg0*.md` | 六段逐页结构化摘要的中间稿 |
| `_build/page_stats.json` | 逐页统计（字数、置信度、重复检测）与标题索引 |
| `_build/*.py` | 处理脚本：`ocr_batch.py`（批量识别）、`ocr_hires.py`（弱页二次识别）、`make_scan_pdf.py`（影印本生成）、`build_doc.py`（本文生成）、`finish_pdf.py`（页眉页脚与书签）、`html2pdf.py`（HTML→PDF） |

**复现要点**：先运行 `python _build/ocr_batch.py`（约 4 分钟，9 进程），再 `python _build/page_stats.py`，然后 `python _build/make_scan_pdf.py` 生成影印本，最后 `python _build/build_doc.py` 生成本文。`.py` 依赖：`rapidocr-onnxruntime`、`onnxruntime`、`numpy`、`Pillow`、`PyMuPDF`、`markdown`，以及本机 Chrome（headless 打印 PDF）。
