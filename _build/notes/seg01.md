# 第 1–16 页 OCR 结构化摘要

> 来源：`_build\ocr\text\001_*.txt` ～ `016_*.txt`（课堂投影片手机翻拍照片的 OCR 文本）
> 说明：术语、缩写、数字均按 OCR 原样保留；粘连的英文已按语义拆分；不确定处在词末标 `(?)`；凡 OCR 未出现的内容不作补充。

---

## 页 1｜MegaMoE recap — What is MegaMoE

- 一句话定义（OCR 首行要点）：**Fine-grained pipeline to better overlap communication and compute** —— 细粒度流水线，以更好地重叠通信与计算。
- 该页用三条泳道时间轴对比三种方案：
  - **(a) Naive Solution**：`Dispatch → L1 → Act → L2 → Combine` 顺序执行。
  - **(b) Comet**：把 `Communication`（`Dispatch`、`Combine`）与 `Computation`（`Act` 等）拆成两条流水线；标注 **Theoretical speedup: 1.42x**。
  - **(c) Ours**：`Disp(atch) All-to-All` 与计算重叠，计算侧为 `L1 / L2` 交替重复（`L1 L2 L1 L2 L1 L2`），并逐段与 `Act`、`Combine` 交织；标注 **Theoretical speedup: 1.92x**。
- 图上出现的计算/通信单元标签：`Linear 1 GEMM`、`SWiGLU + FP8 Cast`、`Linear 2 GEMM`；通信按 **Expert Wave 1 / Expert Wave 2 / Expert Wave 3** 分波次，波次之间为 `Combine All-to-All`。
- 图描述：整页是一张三行对照的时序图，横轴为时间。越往下（Naive → Comet → Ours）通信块与计算块的重叠程度越高，最下方一行把通信切成与 Expert Wave 对齐的多段，从而与 `L1/L2` 计算段交错填满时间轴；右上角给出 1.42x 与 1.92x 两处理论加速比。
- 页脚残留文字 `rom Deeps` → 推测为出处标注 `from DeepSeek…` **(?)**，OCR 不清。

---

## 页 2｜MegaMoE support matrix

- **Inference and training are both supported** —— 推理与训练均支持。
- **Compute data types**（计算数据类型）：
  - `W4A4`
  - `W8A8`
  - `W16A16`
  - `Mixed precisions (W4A8, W8A16 and more in progress)` —— 混合精度，W4A8、W8A16 及更多仍在开发中。
- **Architectures**（支持架构）：
  - `Hopper`
  - `Blackwell`
  - `Blackwell GeForce`
  - `Rubin`
- 通信/框架相关（OCR 残缺较多）：
  - `72andIBRDMAwithNCCLGIN(WIP)` → 疑似与 **IB RDMA + NCCL GIN** 相关，且标注 WIP（开发中）；前半段数字与缩写不可辨 **(?)**。
  - `eworkintegration` → 应为 `Framework integration`（框架集成）。
  - 集成对象：`LLM`(?)、`FlashInfer`、`cuDNN FE (WIP)`（cuDNN Frontend）。
- 该页为矩阵/清单式投影片，OCR 只保留了条目文字，无图表趋势信息。

---

## 页 3｜MegaMoE on Blackwell — Challenges from fusion

- 副标题为 **Challenges from fusion**（融合带来的挑战），核心论点：
  - **Fusion is not 'free'** —— 融合不是"免费"的。
  - **Communication and compute in the same SM** —— 通信与计算跑在同一个 SM 上。
  - **Comm borrows smem from compute** —— 通信要借用计算侧的 shared memory（SMEM）。
  - **Comm traffic can interfere mainloop TMA efficiency** —— 通信流量会干扰主循环的 TMA 效率。
  - **NVFP4 halves L1/L2 time while combine data is always bf16, NVLink traffic will pay more cost** —— NVFP4 把 L1/L2 的耗时减半，但 combine 数据始终是 bf16，因此 NVLink 通信的代价占比更高。
- 图描述：该页为一张分区时序图，上方是 `Dispatch / L1 / L2 / Act / Combine` 的分块时间轴（`L2 L1 L2 L2 / Act Combine` 交替），右侧有两个纵向指标标注 **Interference between compute and comm**（计算与通信的相互干扰）、**GEMM efficiency**（GEMM 效率）与 **NVLink efficiency**（NVLink 效率）；图中无具体数值曲线，只以标签说明干扰会同时压低 GEMM 与 NVLink 两类效率。

---

## 页 4｜MegaMoE on Blackwell — Optimizations（与页 5 同一张投影片，右侧内容被裁切）

- 标题：**Optimizations** 大纲页，三个大项：
  1. **GEMM Perf optimizations**
     - **Large tile size (256x256)**
     - **Dynamic tileN with swapA/B**
     - **In-TMEM epilogue transpose**
  2. **Reduce interference between communication and compute**
     - **MEMBAR synchronization optimization**
       - `Batch-commit`
       - `Async UREDGR`
  3. **Combine perf issues and optimization(s)**
     - `Three modes for combine traffic`
     - `Phase interleaving between FC1 and FC2`（OCR 作 `hase interleavingbetweenFCl andFC2`）
     - `Adaptive traffic control`（OCR 作 `tive traffic control`）
     - `Support for low-precision combine types`（OCR 作 `rt for low-precision co`）
- 该页右侧文字被画面边缘截断，条目只剩词尾片段；**页 5 是同一张投影片的另一次翻拍，内容更完整**，两页可互相校对。

---

## 页 5｜MegaMoE on Blackwell — Optimizations（页 4 的补拍版本）

- 与页 4 为同一张投影片，标题与结构一致，右侧裁切更少，因此完整列出优化清单：
  - **GEMM Perf optimizations**：`Large tile size (256x256)`；`Dynamic tileN with swapA/B`；`In-TMEM epilogue transpose`。
  - **Reduce interference between communication and compute**：`MEMBAR synchronization optimization` → `Batch-commit`、`Async UREDGR`。
  - **Combine perf issues and optimizations**：`Three modes for combine traffic`、`Phase interleaving between FC1 and FC2`、`Adaptive traffic control`、`Support for low-precision combine types`。
- 该页为纯文字大纲，后续各页（6–16）正是按这份大纲逐条展开。

---

## 页 6｜MegaMoE on Blackwell — Large tile size (256x256)

- 论点：**Larger tile has more memory access budget** —— 更大的 tile 意味着更充裕的访存预算。
- 具体做法：**Using 256x256 instead of 256x192** —— 由 256×192 改为 256×256。
- 关键技巧：**Overlapping acc trick to achieve nearly 2-stage acc for 256x256** —— 用累加器（ACC）重叠的技巧，让 256×256 也近似获得"双缓冲/两段式 acc"的效果。
- 图描述：示意图标注 `512 columns`、`48 48 for SF`(?)（疑为 scale factor 的 48×48 分区）以及两块累加器 `ACC0`、`ACC1`；图上以颜色区分两块 ACC 在列方向上的错位搭接，说明"重叠"如何覆盖 512 列宽度。

---

## 页 7｜MegaMoE on Blackwell — Dynamic tileN with swapA/B

- 主旨：**Dynamic tileN with swapA/B**，即配合 swapAB 做动态 tile N。
- 要点：
  - **Use swapAB to map N onto the token dimension to reduce tile quant(ization)** —— 用 swapAB 把 N 维映射到 token 维，以减少 tile 量化浪费（OCR 行尾为 `tile quant`，宾语缺失）。
  - **Dynamically tile N to skip unnecessary loads & computation** —— 动态切分 N，跳过不必要的加载与计算。
- **Epilogue transpose** 子项：
  - **Fuse TMEM 16dp and 32dp ops to transpose 16x32 → 32x16** —— 融合 TMEM 的 16dp 与 32dp 操作完成 16×32 → 32×16 的转置。
  - **Human & LLM co-work to find the optimal TMEM solution** —— 人类与 LLM 协作寻找最优 TMEM 方案。
- 图描述：右侧为「**View of one CTA**」的 tile 布局示意，纵轴标 `Token` 与 `Weight`、横轴标 `tileN` 与 `tileM`，另有 `Valid tokens` 区与 `ACC` 块；图中用 `Valid tokens` 之外的空洞区域表示被动态 tileN 跳过的无效计算。

---

## 页 8｜From a 32x4 Trick to a Full TMEM Transpose

- 标题即该页主张：从一个 **32×4** 的小技巧，扩展到完整的 **TMEM transpose**。
- 方法论副标：**Human hardware intuition × LLM-assisted mathematical modeling** —— 人的硬件直觉 与 LLM 辅助的数学建模 相乘。
- 左侧「**The observable starting point**」（可观测的起点）：
  - **2x LDTM.16dp128b + STTM.32dp32b**
  - **16×8 → 32×4** 的 copy-pattern trick（OCR 作 `16×8→32×4`；该数字组合与标题的 `32x4` 呼应，具体映射关系可能被 OCR 简化 **(?)**）。
- 右侧「**The modeling leap** — developed through iterative discussion with an LLM」：
  - **Treat each LDTM / register permutation / STTM as a bit permutation over thread bits, register bits, TMEM-DP bits, and column bits** —— 把每条 LDTM、寄存器置换、STTM 都视为作用在 thread 位、register 位、TMEM-DP 位与 column 位上的**位级置换**。
- 顶部给出五步流程图：**Observe → Model with LLM → Search → Validate → Integrate**，各步下方标注：
  - `Observe`：`16×8→32×4 copy-pattern trick`
  - `Model with LLM`：`bit permutations + generator constraints`
  - `Search`：`Cayley/BFS`
  - `Validate`：`simulator replay` + `32×32 and 16x32→32×16`
  - `Integrate`：`+ CuTe silicon kernels` + `+ FC1 epilogue`；并有 `overlap-safe in-place … component`(?) 的批注。
- **贡献切分**（页面下半部分两栏对照）：
  - **What the LLM contributed**：`mathematical abstraction`, `search-state design`, `permutation generators`, `systematic exploration beyond what one developer could enumerate` —— 数学抽象、搜索状态设计、置换生成器，以及单个开发者无法穷举的系统性探索。
  - **What the developer contributed**：`Hardware intuition`, `useful constraints`, `simulator/silicon validation`, `and the final overlap-aware kernel integration` —— 硬件直觉、有效约束、模拟器/硅验证，以及最终的"重叠安全"内核集成。
- 结论行：**Result: 16x32 → 32x16 in 4 rounds / 10 TMEM instructions within the searched generator model** —— 在搜索得到的生成器模型内，用 4 轮 / 10 条 TMEM 指令实现 16×32 → 32×16（OCR 作 `Rec  t:`）。

---

## 页 9｜CuteDSL MegaMoE on Blackwell — MEMBAR Synchronization optimization: batch-commit

- 标题：**MEMBAR Synchronization optimization - batch-commit**。
- 机制：**L2 flag is used for pipeline synchronization** —— 用 L2 上的 flag 做流水线同步。
- 两步写 flag 的协议：
  1. **MEMBAR.GPU**：确保此前所有 in-flight 的 GPU-scope 访存流量 **write flag** 都已到达 **PoC**（point of coherence，本例中即 **L2**）。
  2. **RED.ADD flag**：对该 flag 执行 **atomic add 1**。
- 图描述：三行泳道时间轴 —— `Dispatch` 行（`Load token & store local` → `write flag`，重复两次）、`Computation` 行（`Act` → `STG` → `write flag`）、`Pipeline` 行（`wait flag` 之后进入 `Combine`），中间竖排标 `L2`，表示 flag 与数据都落在 L2 上，消费方靠 `wait flag` 等待。

---

## 页 10｜CuteDSL MegaMoE on Blackwell — MEMBAR batch-commit 的权衡

- 核心做法：**The batch-commit: merging multiple MEMBARs into one** —— 把多条 MEMBAR 合并成一条。
- 动机：**MEMBAR can stall requests** —— MEMBAR 会阻塞（stall）请求。
- 代价：**A tunable trade-off between fewer MEMBARs and higher latency** —— 在"更少 MEMBAR"与"更高延迟"之间做可调折衷。
- 两处具体合并粒度：
  - **Dispatch to FC1: batch of 2 flag update** —— 每次批处理 2 个 flag 更新。
  - **FC2 to Combine: batch of 4 flag update** —— 每次批处理 4 个 flag 更新。
- 图描述：两条时间轴分别对应上述两段。`Dispatch to FC1` 行是两次 `Load token & store local` 之后接一条 `MEMBAR`，再用两条 `REDG` 完成 2 次 flag 更新；`FC2 to Combine` 行是 4 组 `Act → STG` 之后接一条 `MEMBAR`，再由 `REDG ×4` 完成 4 次更新，消费侧 `wait flag` 后进入 `Combine`。可见 MEMBAR 数量被压到每批一条，而 flag 更新次数不变。

---

## 页 11｜CuteDSL MegaMoE on Blackwell — MEMBAR Synchronization optimization: async UREDGR

- 标题：**async UREDGR**（OCR 作 `aysnc UREDGR`）。
- 定义：**Async atomic add instruction with built-in MEMBAR** —— 内置 MEMBAR 的异步原子加指令。
- 对比：**MEMBAR is blocking**，而 **UREDGR is non-blocking**。
- 指令原文：`red.async.release.gpu.global.add.u32 [addr], b;`
- **Before**（改造前）：`Load token & store local` ×2 → `MEMBAR` → `REDG` ×2，计算侧 `wait flag`，中间标 `L2`。MEMBAR 显式阻塞。
- **After**（改造后）：`Load token & store local` 连续三次流水推进，计算侧 `wait flag`，用 **Async UREDGR** 替代显式 MEMBAR，屏障语义并入指令内部，不再单独阻塞。
- 图描述：Before/After 两条时间轴上下对照，After 一侧去掉了独立的 `MEMBAR` 块，`Dispatch` 行的加载动作因此可以更早连续发射。

---

## 页 12｜MegaMoE on Blackwell — Three modes for combine traffic（模式一）

- 标题：**Three modes for combine traffic** —— combine 流量的三种模式。本页讲第一种（OCR 作 `Model:`，按上下文与后两页的 `Mode 2 / Mode 3` 判断应为 **Mode 1**）。
- 方案：**direct store over NVLink in L2 epilogue（DeepGEMM solution, long time ago）** —— 在 L2 的 epilogue 里直接通过 NVLink 远端写，这是 DeepGEMM 很早的做法。
- 优点：**good for low latency combine; epilogue warps can send out tokens directly** —— 适合低延迟 combine，epilogue warp 可以直接把 token 发出去。
- 缺点：
  - **Burst NVLink traffic makes fc2 epilogue longer** —— 突发式 NVLink 流量使 FC2 的 epilogue 变长。
  - **epilogue becomes longer, blocking L1/L2** —— epilogue 变长后会阻塞 L1/L2。
  - **the issue makes nvfp4 worse since it halves mainloop** —— 该问题在 NVFP4 下更严重，因为 NVFP4 使 mainloop 减半，epilogue 占比进一步升高。
- 图描述：时间轴分三行 `Dispatch / Computation / Epilogue`。Computation 行是 `L1 L2 L2 L2 L2` 与 `Act Act` 交替；Epilogue 行在每个 `Act Act` 之后出现成对的 `Remote Store`，右侧批注指明这是 NVLink 突发流量导致 epilogue 变长。

---

## 页 13｜MegaMoE on Blackwell — Three modes for combine traffic（模式二、模式三）

- 过渡页，先点出目标与障碍：
  - **Decouple combine from epilogue warps** —— 把 combine 从 epilogue warp 中解耦。
  - **Backpressure from NVLink still blocks the TMA LDG issue** —— 来自 NVLink 的反压仍会阻塞 TMA 的 LDG 发射。
- **Mode 2: reuse dispatch warp group (to smooth the combine traffic over kernel lifetime)** —— 复用 dispatch 的 warp group，把 combine 流量在整个 kernel 生命周期内摊平。
- **Mode 3(?)：standalone combine warp group (further overlap dispatch with combine)** —— 独立的 combine warp group，进一步让 dispatch 与 combine 重叠（OCR 该行行首被裁，按语义应为 Mode 3）。
- 图描述：两条时间轴。Mode 2 中 `Dispatch` 行先出现 `Dispatch`、后段出现 `Combine`（同一 warp group 前后复用），Computation 行为 `L2` 与 `Act Act STG STG` 交替，Epilogue 行不再有 Remote Store。Mode 3 在此基础上把 `Combine` 抬为独立的第三行，与 `Dispatch`、Computation 并行，形成三层重叠。

---

## 页 14｜MegaMoE on Blackwell — Phase interleaving between FC1 and FC2

- 标题：**Phase interleaving between FC1 and FC2**（OCR 作 `FCland FC2`）。
- 要点：
  - **FC1/FC2 tile schedule matters** —— FC1 与 FC2 的 tile 调度顺序很关键。
  - **Perfect overlap with L1 mainloop** —— 目标是让远端写与 L1 mainloop 完全重叠。
  - **Prologue state: consume some L1 tiles to cutoff the L1/L2 dependency in steady state** —— prologue 阶段先消化掉若干 L1 tile，从而在 steady state 切断 L1 与 L2 之间的依赖（OCR 作 `cutoff theL1/L2 dependencyinsteadystate`）。
- 图描述：单条流水时间轴，`Dispatch` 行给出 `L1 L2 L2 L2`，其下 `Act Act Act` 之后出现 `Remote Store`（缩写 `RS`）与 `Act` 交替，右侧为 `RS RS`；图意是让 `RS` 落在 L1 计算之下被完全遮盖，从而不延长 epilogue。

---

## 页 15｜CuteDSL MegaMoE on Blackwell — Adaptive NVLink traffic control

- 标题：**Adaptive NVLink traffic control**（OCR 作 `Adaptive NvLiNK`）。
- 机制：**Measure each chunk's NVLink round trip, EMA (Exponential Moving Average) it, and nanosleep the deviation** —— 测量每个 chunk 的 NVLink 往返时间，用指数滑动平均（EMA）跟踪，并对偏差做 `nanosleep`（让出时间片）。
- 目的：**Reduce remote traffic head-of-line blocks** —— 减少远端流量的队头阻塞。
- 适用范围：**Used in mode 2 and 3 with combine that's not in epilogue warps** —— 用于 Mode 2 与 Mode 3，即 combine 不在 epilogue warp 里的情形。
- 图描述：上方是 `Combine` 的 chunk 序列 `chunk0, chunk1, chunk2, …, the last chunk`；下方标注两个时刻 `t0`、`t1` 及 `w = t1 - t0`(?)（即测得的往返/等待窗口），并给出 `TMA load: local → SMEM` 与 `bulk store peer` 两个动作，中间插入 `nanosleep`。图意是按实测往返偏差主动插入短暂休眠，避免远端流量扎堆造成队头阻塞。

---

## 页 16｜MegaMoE on Blackwell — Support for low-precision combine data types

- 标题：**Support for low-precision combine data types**。
- 主张：**MXFP8 and NVFP4 to reduce NVLink traffic** —— 用 MXFP8 与 NVFP4 降低 NVLink 流量。
- 精度格式对照表（表头为 `data format / scale / block`）：

  | data format | scale | block | 说明 |
  |---|---|---|---|
  | `bf16` | `bf16` | （未标） | baseline；**the only format the in-kernel REDG path can atomic-add** —— 是内核内 REDG 路径唯一能直接原子加的格式 |
  | `FP8 E4M3` | `E8M0` | `32` | `32 e4m3 × e8m0`，即 standard MXFP8 power-of-two scale（2 的幂次 scale） |
  | `NVFP4 E2M1` | `bf16 amax` | `16` | `16 e2m1 × bf16`，full-precision amax per 16 elements —— 每 16 个元素一个全精度 amax，**recovers accuracy the E8M0 rounding loses**（挽回 E8M0 舍入造成的精度损失） |

- 前提条件：**Precision doesn't regress on some models** —— 在部分模型上精度不退。
- 工程代价：因为 bf16 是唯一可被内核内 REDG 原子加的格式，低精度 combine 需要 **A separate topK reduction kernel after megakernel** —— 在 megakernel 之后加一个独立的 topK 归约 kernel。
- 图描述：底部为两张并排的方块图，`Mega Kernel` → `TopK Reduce Kernel`，表示低精度 combine 被拆成"主内核 + 后置 topK 归约内核"两段流水。
- 页脚（OCR 残留 `ALDONOTDISTRIBUTE`）应为 `NVIDIA CONFIDENTIAL. DO NOT DISTRIBUTE` 一类保密声明。

---

## 本段主题与脉络

这 16 页完整讲了一个问题：**MegaMoE 要在 Blackwell 上把 MoE 的通信与计算真正融到同一个 SM 里**。页 1 先用三条时间轴定基调——把 dispatch/combine 与 L1/L2 GEMM 细粒度交织，理论上可拿到 1.42x（Comet）到 1.92x 的加速；页 2 给出支持矩阵，说明能力边界；页 3 立刻反问"融合不是免费的"，点出通信抢 SMEM、干扰 TMA mainloop、NVFP4 让通信占比上升三大矛盾。页 4–5 是优化大纲，其后各页逐条兑现：页 6–8 攻 GEMM 侧（256×256 大 tile、swapAB 动态 tileN、以及与 LLM 协作推导出的完整 TMEM 转置）；页 9–11 攻同步侧（MEMBAR 合并、异步 UREDGR）；页 12–15 攻 combine 侧（三种流量模式、FC1/FC2 相位交织、自适应 NVLink 限速）；页 16 收在低精度 combine 与后置 topK 归约上。整体是"提出融合收益 → 揭露融合代价 → 逐子系统给出对策"的技术递进。
