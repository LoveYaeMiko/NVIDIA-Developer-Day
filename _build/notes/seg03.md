# 第 33–48 页摘要（seg03）

> 来源：`_build\ocr\text\033_*.txt` — `048_*.txt`，共 16 页，全部存在。
> 说明：本段前半（33–34）是上一段「MegaMoE」主题的收尾，后半（35–48）切换到以 DeepSeek-V4-Pro + Megatron Core + NVIDIA Blackwell 为例的大规模训练优化 playbook。第 39/40 页、41/42 页是同一张投影片的两次拍摄（OCR 质量略有差异），已分别列出并标注。

---

## 页 33｜Token Sweep Results

**图表**：4 组/两簇柱状图为 token sweep 的耗时对比，横轴 `tokens per rank`（8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768，共 13 个 bucket），纵轴为耗时 `ms (slowest rank, useful FLOPs)`(?)（刻度 200/400/600/800/1000/1200）。两组配色分别对应 `Per-Tensor FP8` 与 `Blockwise FP8 (DeepGEMM-style)`；每组柱子上方标注 `MegaMoE ÷ baseline` 的加速倍数。图中可见两组柱子在小 token 数时高度接近，随 token 数增大差距拉开。

- 实验设定：`4x H200`、`EP4`、`DeepSeek-V4-Pro shape`、`full MoE-layer forward`，统计口径为 `p50 over the slowest rank`。
- 图注定义：每组上方数字 = speedup（`MegaMoE ÷ baseline`）。
- Baseline = 常规四段式流程：`NCCL all-gather / reduce-scatter` + `CUTLASS grouped GEMM`（fused finalize）。
- 对照实现：`MegaMoE` = fused single kernel（`NVSHMEM` dispatch/combine）。
- 关键结论（讲者原话）：Per-Tensor 配置下 `MegaMoE` 在全部 13 个 bucket 上领先 —— 512 tokens 及以下为 **1.02–1.11x**，1024 起为 **1.24–1.35x**（峰值 **1.35x** 出现在 8192），geomean **1.16x**。
- 解释：小 token 数时两者接近 —— launch / communication 主导；一旦 GEMM 占比上升，单内核方案的优势才显现出来。
- 图中标注的其余倍数（OCR 可读）：1.33x、1.24x、1.72x、1.35x、1.59x、1.51x、1.29x、1.27x、1.45x、1.37x、1.11x、1.31x、1.09x、1.22x、1.06x、1.05x、1.03x、1.02x、1.18x、1.16x。其中大于 1.35x 的数值（如 1.72x、1.59x、1.51x）应属于 Blockwise FP8 一组（由 Per-Tensor 组 ≤1.35x 的结论反推）(?)。
- 页脚可见 `NVIDIA` logo。

---

## 页 34｜Summary

**What was built**（这一页是 MegaMoE 部分的总结清单）：

- **One persistent kernel**，融合 `dispatch + FC1/SwiGLU + FC2 + combine`（共 **six modes**）。
- **Two complementary kernel variants**：`non-swap` / `swapAB`；并配 **two quantization modes**：`per_tensor` / `blockwise`。
- **30+ kernel / communication / scheduling optimizations**，并用 **token-bucket heuristics** 把 sweep 出来的 winner 冻结下来（freezing the sweep winners）。
- 页面上重复出现多枚 NVIDIA logo（版式元素）。

---

## 页 35｜Two Challenges Define Training at Scale

**结构**：左右两栏并置 —— 左侧「Make it fit」，右侧「Make it fast」，中间标注本讲的取材来源。

- 左侧 **Make it fit**（装得下）：
  - `Massive parameter counts`（超大参数量）
  - `Model states and HBM capacity`（模型状态与 HBM 容量）
  - `Long context windows`（长上下文窗口）
  - `Parallel layout and topology`（并行切分布局与拓扑）
  - `Feature compatibility`（特性兼容性）
- 右侧 **Make it fast**（跑得快）：
  - `Kernel and launch overhead`（内核与 launch 开销）
  - `Recompute and offload costs`（重算与 offload 代价）
  - `Communication and load imbalance`（通信与负载不均衡）
- 取材说明（This talk is based on）：
  - `Public DeepSeek-V4-Pro model architecture`（公开的 DeepSeek-V4-Pro 模型架构）
  - `Implementations in Megatron Core`
  - `NVIDIA Blackwell GPUs`

---

## 页 36｜One Playbook, Two Workloads

**结构**：左栏列出统一的优化 playbook 四步，右栏给出这套 playbook 实测的吞吐收益。

- **One Optimization Playbook**（四步）：
  1. `Runtime Overhead and Memory Trade-offs`
  2. `Attention Compute Efficiency`
  3. `Expert Execution and Memory Footprint`
  4. `Context-Parallel Load Balance`
- **Measured throughput gains from the playbook**：
  - **+59%** at **64k** context length
  - **+32%** at **1M** context length
- 标题点题：同一套 playbook，作用于两种不同 workload（64K 与 1M 上下文）。

---

## 页 37｜DeepSeek-V4-Pro Overview

**图**：DeepSeek-V4-Pro 的整体模型结构图（左侧为从 `Input Tokens` 向上的堆叠，右侧为两个关键规格数字与预训练 recipe）。图中元素与标签：

- 自下而上的层级标签：`Input Tokens` → `Embedding` → `Pre-Block Mixing` → `Residual Mixing` → `CSA/HCA` → `DeepSeekMoE` → `Post-Block Mixing` → `Transformer Block x L` → `Prediction Head` → `MTP Modules`（并标注 `MTP Loss`）。
- 右侧规格：**`1.6T` Total parameters**；**`49B` Activated parameters per token**。
- 右侧 **Pre-training recipe**：横轴为上下文长度 `4K → 16K → 64K → 1M`，对应数据形态 `dense → dense → dense/sparse → sparse`。
- 出处注：`The model graph is from DeepSeek-V4 tech report.`

---

## 页 38｜Model Features Drive Optimizations

**图**：与第 37 页同一张模型结构图，但本页在右侧用四条编号说明「哪些模型特征驱动了哪些优化」。图内标签同上（`Input Tokens`、`Embedding`、`Pre-Block Mixing`、`Residual Mixing`、`Indexer`、`CSA/HCA`、`DeepSeekMoE`、`Post-Block Mixing`、`Transformer Block x L`、`Prediction Head`、`MTP Modules` / `MTP Loss`）。注意本页 OCR 中比第 37 页多出 `Indexer` 一项（第 37 页 OCR 未识别到）。

- 规格：**`1.6T` total / `49B` active**。
- 四条特征 → 优化映射：
  1. **Model states limit memory headroom for faster execution.**（模型状态挤占显存余量，限制了更快的执行方式）
  2. **Hybrid attention**：different attention paths require tailored kernel optimizations.（不同注意力路径需要定制内核优化）
  3. **Fine-grained MoE**：expert compute, communication, and buffers drive performance.（专家计算、通信与 buffer 决定性能）
  4. **Causal long context**：equal token counts can still m[ean] unequal workloads.（同样 token 数也可能意味着不等的实际工作量）
- 出处注同上：`The model graph is from DeepSeek-V4 tech report.`

---

## 页 39｜Choose the Parallel Layout（General Guidance on Parallel Tuning）

- **1. Model size guides the initial layout.**
  - 可以估算 static part budget，据此选一个初始 layout。
  - 为 activations 与 buffers **预留 headroom**。
  - 专家优先用 `EP`，跨 domain 用 `PP`，必要时再加 `TP`。
- **2. Context length guides CP.**（本页 OCR 为 `Cp`）
  - 上下文长度影响 activation 与 buffer 的大小。
- **3. Topology guides placement.**
  - 通信密集的组（如 `EP`、`TP`、`CP`）尽量收在 **NVLink domain** 内，以获得更好的吞吐。
- 实例：**256-GPU 的 DeepSeek-V4-Pro run，初始布局用 `PP4` 与 `EP64`。**

---

## 页 40｜Choose the Parallel Layout（同页重拍）

与第 39 页为**同一张投影片**（本条 OCR 更完整，`CP` 未误识为 `Cp`），要点完全一致，此处仅列差异与完整句：

- **1. Model size guides the initial layout.** We can estimate the static part budget and choose an initial layout. Reserve headroom for activations and buffers. Prefer EP for experts, use PP across domains, and add TP if necessary.
- **2. Context length guides CP.** Context length affects the activation and buffer size.
- **3. Topology guides placement.** Keep communication-heavy groups (such as EP, TP, and CP) within NVLink domains where practical for better throughput.
- **For our 256-GPU DeepSeek-V4-Pro runs, we use `PP4` and `EP64` as the initial layout.**

---

## 页 41｜Context Length Drives Memory Policy

**结构**：左右对照两种上下文长度的显存策略。核心命题：`More tokens per rank increase activation and buffer memory.`

| | 64K Context | 1M Context |
|---|---|---|
| 并行度 | `CP16` | `CP64` |
| 每 rank token 数 | `4,096 tokens/rank` | `16,384 tokens/rank` |
| 策略 | Fine-grained recompute + offload | Full recompute |
| 效果 | More headroom for CUDA Graphs | Higher activation pressure |

- 结论句：**1M 时每个 rank 的 token 数是 4 倍，因此切换到更激进的显存策略（more aggressive memory policy）。**

---

## 页 42｜Context Length Drives Memory Policy（同页重拍）

与第 41 页为**同一张投影片**，本条 OCR 更完整（`1M Context`、`16,384 tokens/rank` 数字正确）；原文要点：

- `More tokens per rank increase activation and buffer memory.`
- `64K Context` / `CP16` / `4,096 tokens / rank` → **Fine-grained recompute + offload**；**More headroom for CUDA Graphs**
- `1M Context` / `CP64` / `16,384 tokens / rank` → **Full recompute**；**Higher activation pressure**
- `4x more tokens per rank at 1M, so we switch to a more aggressive memory policy.`

---

## 页 43｜The Starting Points

- 用 **4K-context 的 sparse proxy model** 来基本验证所需特性，包括：
  - `Kernel fusions`、`packed sequence support`、`CUDA Graphs support`, and others
- 用 profile 来指导后续优化；两段 profile **都在 150ms 窗口内**（OCR 为 `15oms`，应为 150ms）(?)
- 图：上下两张 Nsight 式 timeline 截图，分别标注 `64K` 与 `1M`；行标签为 `CUDA HW (0008:06:00.0 - N…)`、`Kernel`、`Memory`、`[AllStreams]`；可见内核名形如 `nvjet_sm103_tst_…`、`nvjet_sm103_tss_…`（`sm103` 指向 Blackwell 一代的 CUTLASS 内核命名）。
- 该页文字偏少，主要是两张 timeline 截图作对照（未给出具体数值）。

---

## 页 44｜STEP 1: Runtime Overhead and Memory Trade-offs

- 判断：**64K 场景下的主要问题是大量 GPU idle（Lots of GPU idles）**。两种缓解手段：
- **Fusion kernels**
  - 有些算子容易融合，例如 simple mathematics 与 memory movements。
- **CUDA Graphs**
  - 把 static modules 捕获后 replay；**用 padding 把 packed sequences 变成 static**（`we use padding to make packed sequences static!`）。
- 图：上下两条 kernel timeline 对比 —— `w/o CUDA Graphs` 与 `w/ CUDA Graphs`；图中为密集的小 kernel 块（OCR 只见 `kern…`、`void`、`kernel`、`kerne…` 等碎片标签），示意启用 CUDA Graphs 后 kernel 发射的空隙被压缩。
- 该页数值信息极少（无具体百分比）。

---

## 页 45｜Where the Step Time Goes（Layer time decomposition）

**图**：堆叠柱状图，横轴 `Context Length` = `4K` / `64K` / `1M`，纵轴 `Percent %`（OCR 刻度数字残缺，仅见 `100`、`200`(?) 等碎片），每根柱子按模块分段。

- 图例（分段含义）：`MoE experts`、`EP comms`、`Indexer + CP comm`、`Sparse Attn`、`Group-O Proj`、`Others`；柱内另有 `Attn` / `MoE` 大类标注。
- 注：`4K is a sparse proxy case for comparison`（4K 仅作 sparse proxy 对照）。
- 讲者意图：拆解 layer 时间构成，为后面 STEP 2（注意力）与 STEP 3（MoE）的优化定位瓶颈。
- 该页 OCR 未给出各分段的具体百分比数值。

---

## 页 46｜STEP 2: Optimize the Hybrid Attention

**Optimize Three Important Modules in the DeepSeek-V4 Hybrid Attention** —— 三个模块各一组 BEFORE / AFTER 对照：

### 1. Sparse Attention
- 手法：`Left-align the valid indices`；kernel 跳过 invalid slots。
- **BEFORE**：`SCAN EVERY SLOT`（逐 slot 扫描）；图注 `One query row of KV indices — -1 is invalid`。
- **AFTER**：`SCAN THE FIRST L ONLY`；`valid prefix L`、其余 `ignored`；**`topk_length = L` — no holes left to walk over**。

### 2. Indexer
- 手法：`Skip the invalid part from causal mask`；对重头的 QK matmul **用低精度**（`Use low-precision on the heavy QK matmul`）。
- **BEFORE**：`MATERIALIZE, THEN SELECT` —— 先物化 `Full score matrix S`（图中标注 `(S/4)` mostly unused(?)），`second pass`，QK 用 **BF16**。
- **AFTER**：`SCORE AND SELECT IN ONE KERNEL` —— `Q·K quantized to FP8`，`Candidates + top-k` 一步出，`Only the selected scores are ever written out`。
- 图中另有两处 `4Q`/`40`(?) 的残缺标注（疑为 `4Q` 或 mask 比例），无法确认。

### 3. Group-O Projection
- 手法：`Fuse into a batched GEMM`；`Enable FP8 computation`。
- **BEFORE**：`SEPARATE LAUNCHES` —— 输入 `Attention output [S, B, heads × dim]`，`split into G groups`（图中画出 `G0, G1 … G7`，即 `G=8`）；**`G=8 small GEMMs, one kernel launch each`**。
- **AFTER**：`ONE BATCHED GEMM` —— `All G groups multiplied together — one kernel`；再 `Project back to hidden`。

---

## 页 47｜STEP 2: Optimize the Hybrid Attention（效果页）

- **Speedup (module-level)**（模块级加速，相对 STEP 1 之后的 config）：
  - `Compact sparse attention`：**25%–30%**
  - `Compact FP8 Indexer`：**25%–35%**
  - `Group-O batched GEMM`：**50%–60%**
- **Throughput uplift from STEP 2**（端到端吞吐提升）：
  - **+4.6%** at **64K** context length
  - **+9.0%** at **1M** context length
- 解释：`These gains come from faster execution.`（这些收益来自更快的执行）
- 附加观察：`The indexer accounts for a larger share of step time at 1M.`（1M 下 indexer 占 step time 的比例更大）——这与 1M 的端到端收益（+9.0%）高于 64K（+4.6%）相呼应。

---

## 页 48｜STEP 3: Optimize the MoE

- 观察：**MoE 部分中约 30%–50% 是 EP communication**；目标是 `hide the communication behind computation`（把通信藏到计算后面）。
- **Two solutions now**：
  1. **Cross-batch EP overlapping**
     - 更适合 **cross-NVLink domain** 场景
     - block size 由从 **nsys report** 中提取的 silicon time(?) 决定（`The block sizes are determined by the silicon time extracted from nsys report.`）
     - 代价：**Increase memory overhead**（增加显存开销）
  2. **Fine-grained overlapping with Megakernel**
     - 在 NVLink domain 内相对更容易融合
     - 更好地利用显存（`Better utilize the memory`）
- 图（右下）：overlap 示意 —— `Overlapped` 区间内 `Computation` 为 `Expert FFNs1` / `Expert FFNs2`，`Communication` 为 `Dispatch1` / `Dispatch2` / `Combine1` / `Combine2`，横轴 `Time`；左上另有 `layer1_f` / `layer0_b` 之类的层命名碎片（`Ifib`(?)、`Ifib with loss`(?) 等 OCR 残字，含义无法确认）。
- 出处注：`The graph below is from the MoK(?) blog from Cursor.`（`MoK` 疑为 `MoE`，待核）

---

## 本段主题与脉络

这 16 页分两段：33–34 页收尾 MegaMoE（单内核在 1024 tokens/rank 以上领先，geomean 1.16x）；35–38 页转入训练 playbook，以"装得下/跑得快"切入，用 DeepSeek-V4-Pro（1.6T/49B）映射四步优化，实测 +59%(64K)、+32%(1M)；39–43 页定起点：PP4/EP64 布局与显存策略切换；44–48 页落地消 GPU idle、FP8 indexer、batched GEMM 与 EP 通信 overlap。
