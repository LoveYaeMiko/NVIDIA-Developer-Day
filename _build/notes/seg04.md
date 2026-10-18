# 第 49–64 页 OCR 结构化摘要

> 来源：`_build\ocr\text\049_*.txt` ～ `064_*.txt`（课堂投影片手机翻拍照片的 OCR 文本，共 16 个文件，全部存在）
> 说明：术语、缩写、模型名、内核名、硬件名、精度格式、数值与倍数均按 OCR 原样保留；粘连的英文已按语义拆分；不确定处在词末标 `(?)`；凡 OCR 未出现的内容不作补充推断。

---

## 页 49｜STEP 3: Optimize the MoE

- 标题：**STEP 3: Optimize the MoE**。涉及对象：**Mixture-of-Kittens (MoK) from Cursor**（OCR 原文如此，`Kittens` 一词存疑 **(?)**）。
- 三条优化手段，逐条列出：
  1. **Fused execution** —— *Combine expert computation and communication in one kernel.*（把专家计算与通信合并进同一个 kernel。）
  2. **Communication overlap** —— *Pipeline token transfers with expert computation.*（token 传输与专家计算流水重叠。）→ **+14.0% at 64K context length**
  3. **Buffer reuse** —— *Reuse fixed-size ring buffers to reduce memory usage and avoid CPU synchronization for buffer allocation.*（复用固定大小的 ring buffer，降低显存占用并避免缓冲区分配带来的 CPU 同步。）→ **+4.6% at 1M context length**
- 结论句：*MoK can bring **30%–40% speedup on the MoE part** in the DeepSeek-V4-Pro setting.*
- 图元素：右侧为「Throughput uplift from STEP 3（compared with the config after STEP 2）」的柱状/条形标注，两项数值即 **+14.0%（64K）** 与 **+4.6%（1M）**；趋势是长上下文（1M）下收益明显小于 64K。
- 该页是「优化清单 + 收益数字」型投影片，无曲线图。

---

## 页 50｜STEP 4: Balance CP Workloads

- 标题：**STEP 4: Balance CP Workloads**。
- 核心论断：**Equal tokens per rank does not mean equal work on each rank.**（每个 rank 分到等量 token，并不等于每个 rank 承担等量工作。）
- 图元素：柱状图，图注为 **CSA and Indexer time on 512K context size with CP32**；纵轴 **GPU time (ms)**，刻度 10 / 20 / 30 / 40 / 50 / 60；横轴为 **CP rank**；每根柱按两个分量堆叠，图例为 **Indexer score forward** 与 **CSA forward**。
- 柱顶数据（OCR 保留的 9 个数值）：**53.1、49.9、45.3、40.9、36.6、31.9、27.3、23.1、18.4**。
- 图描述：柱高自 53.1 单调递减到 18.4，说明同一 CP32 组内各 rank 的总 GPU 时间相差近 3 倍，负载极不均衡；堆叠关系表明 `Indexer score forward` 与 `CSA forward` 两部分共同构成该时间。
- 不确定项：横轴 CP rank 只留下 `12 / 16 / 20 / 24 / 28 / 31` 等刻度，与 9 个柱值数量不匹配，疑有刻度识别丢失 **(?)**。

---

## 页 51｜STEP 4 II：用 zigzag 布局均衡 CP 负载

- 标题（OCR 作 `STEP4I`）：**STEP 4 II: Balance CP Workloads**。
- 复述论断：*Equal tokens per rank does not mean equal work on each rank.*
- **Why?** —— *QK score computation scales quadratically with sequence length.*（QK score 的计算量随序列长度二次增长。）
- **How?** —— *Balance the workloads with **zigzag layout**.*（用 zigzag 布局均衡负载。）
- 收益：**12.2% at 1M context length**（图注为「Throughput uplift from STEP 4，compared with the config after STEP 3」）。
- 图元素（负载重分配示意，两行 rank 块）：
  - 布局前：`R0 R1 R2 R3` 对应 `lightest / hea(v)ier / heavier / heaviest`，即 **R3 becomes the straggler and the others wait**（R3 成为掉队者，其余 rank 空等）。
  - 布局后（标注 `AFTER 2xCP SEGMENTS, PAIRED DIAGONALLY`）：上一行 `R3 R2 R1 R0`、下一行 `R0 R1 R2 R3`，即 **R0 takes the lightest and the heaviest**（R0 同时承担最轻与最重的段），以此拉平各 rank 总工时。
- 代价：*HOWEVER: the balance process also introduces extra overheads.* → **NO measurable perf gain at 64K context length**（64K 下无可测量收益）。
- 页脚残留 `DIA` 疑为 `DIAGONAL` 的截断 **(?)**。

---

## 页 52｜Lessons for Scalable Training（KEY TAKEAWAY）

- 标题：**Lessons for Scalable Training**，标签 **KEY TAKEAWAY**。
- 三条结论：
  - **Parallelism and memory policy jointly determine feasibility.**（并行策略与显存策略共同决定可行性。）
  - **Use profiling to guide the optimization.**（用 profiling 指导优化。）
  - **Optimization priorities depend on the target workload.**（优化优先级取决于目标负载。）
- 右半区：**Get Started with Megatron Core** —— **Reference recipes for DeepSeek-V4-Pro**；三条卖点：
  - *Composable parallelism for scalable dense and MoE training.*
  - *FP8, fused kernels, and communication overlap optimized for NVIDIA GPUs.*
  - *Modular building blocks for custom models and training workflows.*
- 链接：`https://github.com/NVIDIA/Megatron-LM`；配方路径 OCR 作 `Megatron-LM/examples/moe recipes/deepseek_pro/gb300/`（`examples` 与 `moe_recipes` 的目录名拼接不清）**(?)**。
- 配置文件名（OCR 严重残缺，仅能读出片段，标注不确定）：
  - `DmSL4K266OPU_TP1PP4EAyam` → 疑似 **…64K…256GPU_TP1_PP4…​.yaml** 一类的 64K 配方 **(?)**
  - `mTHO1_256OPUTPIPPP64CP84yal` → 疑似含 **256GPU / TP1 / PP? / CP64** 的 1M 配方 **(?)**
  - `mTH045CCPU_TP1PECP16ym` → 疑似含 **TP1 / PP? / CP16** 的配方 **(?)**
  - 另有 `[Dev] Updte c(NVI335)`、`Tools bench 1379…` 等行基本不可辨 **(?)**。
- 该页为「结论 + 资源入口」型投影片，无图表。

---

## 页 53｜Motivation: KV Cache as a Serving Bottleneck（议程页）

- 标题：**Motivation: KV Cache as a Serving Bottleneck**。
- 本页是后续整段的 **Agenda**，四节：
  1. **Motivation: KV Cache as a Serving Bottleneck**
  2. **Taxonomy: Inference-time KV Cache Compression Patterns**
  3. **Performance Analysis: TurboQuant & KVTC & nvCOMP**
  4. **Takeaways**
- 该页为目录页，仅有章节标题，无数据；文本中未出现图表元素。

---

## 页 54｜KV Cache Is a Serving Bottleneck

- 标题：**KV Cache Is a Serving Bottleneck**；首句 **KV memory grows linearly with context length**（KV 显存随上下文长度线性增长）。
- **THREE BOTTLENECKS**（三重瓶颈）：
  - **GPU capacity**：*Fewer active requests fit* → **active batch ↓**、**max context ↓**
  - **HBM bandwidth**：*Every token rereads history* → **more HBM bytes, bandwidth-bound**
  - **System I/O**：*When capacity spills, KV moves GPU ↔ CPU / SSD / remote* → **TPOT ↑**、**prefill / decode not work**(?)
- **SYSTEM TRADE-OFF**（系统级权衡），三条互相牵制的目标：
  - **Maintain concurrency** —— 固定 GPU budget 下，要维持并发就得 **more GPUs · cost ↑**，否则 **active requests ↓**
  - **Maintain TTFT / TPOT** —— 代价是 **offload / re-prefill ↑**
  - **Optimize the global serving trade-off**
- 图描述：整页为「三列瓶颈 → 一栏 trade-off」的矩阵式版面，三列各自向下给出因果链，底部汇到全局权衡；OCR 未含数字，只有方向性符号（↑ / ↓）。

---

## 页 55｜KV Cache Compression Methods: training-time & inference-time

- 标题：**KV Cache Compression Methods**，副题 **Training-time & inference-time**。
- 分成两大类：
  - **TRAINING-TIME — Architecture design**（架构设计，示例为模型结构本身）：
    - `MQA · GQA`
    - `MLA · CLA`（`CLA` 拼写存疑 **(?)**）
    - `Kimi Linear · CSA/HCA · MSA`
  - **INFERENCE-TIME — Runtime compression**（运行时压缩），三个子类：
    - **Quantization**：*Fewer bits per KV element*（FP16 → low-bit），手段为 **Scales + protected outliers**（缩放因子 + 保护离群值）
    - **Storage sparsity**：*Retain fewer KV entries*，手段为 **Prune / evict KVs**（剪枝 / 淘汰 KV）
    - **Compute sparsity**：*Read fewer KV entries or pages*，手段为 **Query-aware top-K reads for attention**（查询感知的 top-K 读取）
- 版面内含 `FP16 | Low-bit`、`full cache`、`retained`、`full cache stays resident` 等对比标签，说明低比特方案保持全量 cache 常驻，只是每元素位宽下降。
- **SERVING IMPACT**（指标定义，页脚）：
  - **MEM = footprint**（显存占用）
  - **MEM READ = KV-cache bytes / decode**（每步 decode 读取的 KV 字节数）
  - **ATTN = attention**(?) （OCR 截断）
  - 三类压缩均标 **MEM↓**，注意力开销行标 **ATTN↓**；某行 OCR 作 `ATTN=(+DQ)`，疑为 `ATTN = f(DQ)` 一类函数写法 **(?)**。
- 残缺项：表内 `161616`、`MEMI / MEMI / MEM=` 等字符为表格分隔线与角标的误识 **(?)**。

---

## 页 56｜Where KV Compression Fits（两种集成路径）

- 标题：**Where KV Compression Fits**，副题 **Online attention path or KV-cache backend**。
- **REUSABLE MODULE**：`KV-cache compression` —— 三个实现：**TurboQuant**、**KVTC**、**nvCOMP-ANS**。
- **TWO INTEGRATION PATHS**（两条集成路径）：
  - 路径一：**Inference engine（vLLM / SGLang / TRT-LLM）** → **Online path, e.g. INT8 · TurboQuant**
    - *Compressed KV remains GPU-resident.*（压缩后的 KV 常驻 GPU）
    - 收益：**Capacity ↑**、**KV bytes per decode step ↓**、对推理引擎**透明（Transparent）**，等效于 **more effective KV batch / context / throughput**
    - **CHALLENGE**：**attention fusion · engine & model-specific integration**（需与 attention 融合，且与引擎、模型强绑定）
  - 路径二：**KV-cache backend（LMCache / FlexKV / Mooncake）** → **Offload path, e.g. KVTC · nvCOMP-ANS**
    - *Restore to standard KV before attention.*（注意力前先还原成标准 KV）
    - 收益：**Storage / Transfer ↓**、**Capacity ↑**（CPU / SSD / remote），并带来 **prefix-hit potential**
    - **CONS**：**decompression overhead · no direct TPOT gain**（解压开销，且不直接改善 TPOT）
- **INTEGRATION RULE**（选择准则）：**KV-read savings > decompression overhead → Inference engine；Otherwise → KV-cache backend**（只有省下的 KV 读取量大于解压开销，才值得放进推理引擎，否则退回 KV-cache backend）。
- 图描述：两列对照版面，左列标「在线路径」、右列标「卸载路径」，每列自上而下为「压缩后形态 → 收益行 → 代价行」，底部一条横向判定规则把两条路径连起来。

---

## 页 57｜TurboQuant: Online KV Quantization

- 标题：**TurboQuant: Online KV Quantization**，副题 **Low-bit vectors for the attention path**。
- **概念解码路径（Conceptual decode path）**，按流水顺序：
  1. **Input K/V vector** → **Random rotation**（随机旋转）→ 理由：*In high dimensions: smoother, nearly independent coordinates*（高维下坐标更平滑、近似独立）
  2. **Codebook lookup → low-bit indices**：用**预计算的 Lloyd-Max codebook**（Precomputed Lloyd-Max codebook），码字中心为 **−1.2 / −0.4 / +0.4 / +1.2**，编码示意 **00 | 10 | 01 | 11**；*Nearest centroid → store its ID*（存最近质心的 ID）
  3. **Inverse rotate + rescale**（逆旋转 + 反缩放）
  4. **Optional inner-product correction**：*residual → QJL projection → sign bits*（残差经 QJL 投影取符号位）
- **每个向量存储三类信息**：
  - **Centroid indices** —— main low-bit payload（主体低比特载荷）
  - **Residual sign bits** —— optional QJL correction（可选修正）
  - **Scalar norms** —— small per-vector metadata（少量逐向量元数据）
- **不逐向量存储、而是共享**：`rotation / projection matrices + codebook`。
- 效果与出处：**4.5X Compression ratio**；**Llama-3.1-8B · ≥4.5x nominal payload**；**50.06 LongBench-V1 aggregate = FP16**(?)（该行 OCR 作 `50.06 LongBench-V1 aggregate =FP16`，含义应为聚合分与 FP16 持平，`50.06` 数值存疑 **(?)**）。
- 论文链接：`https://arxiv.org/abs/2504.19874`
- 图描述：中部为「向量 → 旋转 → 量化到 4 个码字之一 → 反变换」的流程示意，底部一行色块图例把「主载荷 / 可选修正 / 元数据」对应到三类存储字段。

---

## 页 58｜TurboQuant: Layout Compressed KV for Decode

- 标题：**TurboQuant: Layout Compressed KV for Decode**；要点：**Quantize + pack directly into aligned page fields for MMA decode**（量化后直接打包进对齐的 page 字段，供 MMA decode 使用）。
- 对比两种布局：
  - **TOKEN-INTERLEAVED**（按 token 交错）：**D = 128，134B per token**；每个 token 的字段依次为
    - `K codes` **64B** · `K norm` **2B** · `V codes` **64B** · `V scale` **2B** · `V zero` **2B**
    - **134B stride**，且 **V codes begin at byte 66**（V codes 从第 66 字节开始）
  - **PAGE-LOCAL FIELD PLANES**（页内字段平面化）：**16 tokens · 2,144B per page / KV head**，字段平面宽度（schematic）：
    - `K codes` **16 × 64B = 1,024B**
    - `V codes` **16 × 64B = 1,024B**
    - `K norms` **16 × 2B = 32B**
    - `V scales` **16 × 2B = 32B**
    - `V zeros` **16 × 2B = 32B**
- 收益指标：**NCU · Useful bytes per 32B load sector：3.68B → 29.75B**（每个 32B 访存扇区里的有效字节数由 3.68B 提升到 29.75B，即访存利用率大幅提高）。
- 实现链接：`https://github.com/vllm-project/vllm/pull/53060`（OCR 作 `vm-project/vilm`、`vlm-pro`，疑为 vLLM **(?)**）。
- 图描述：上行为 token 交错排布（每 134B 一段，K/V 字段交替），下行为同页 16 个 token 重新按字段聚成 5 个连续平面，从而让一次 32B 扇区读取几乎全是有效数据。

---

## 页 59｜TurboQuant: Tiled MMA Decode Attention on 4-bit KV

- 标题：**TurboQuant: Tiled MMA Decode Attention on 4-bit KV**；要点：**Stream compressed tiles, build MMA operands on chip, carry softmax state**（流式加载压缩 tile、片上构造 MMA 操作数、携带 softmax 状态）。
- 循环结构：**REPEAT FOR EACH 64-TOKEN KV TILE**；**one CTA handles one KV split**；**Double-buffered async load**（`tile i: compute` / `tile i+1: load`）。
- 每个 tile 的计算链：
  - **GQA Q pack · up to 16 heads** → **FWHT → FP16 Q tile**
  - **4-bit KV page fields（codes + metadata）** → **K codes → centroid direct MMA fragment**（码字直接映射为 MMA fragment），再做 **Knorm correction**
  - **QKᵀ Tensor Core MMA**
  - **V codes + scale/zero** → **FP16 shared-memory tile** → **P × V Tensor Core MMA**
- **FP32 RUNNING STATE**（跨 tile 携带的 FP32 运行状态）：**max score**、**exp sum**、**weighted output**；**Online softmax · rescale across tiles**，状态 **carried into the next tile**。
- 归约：**KV split 0 … KV split 1 … KV split N** → **Stable merge → BF16 output**。
- 图描述：整页是一张流水/数据流图，左侧为 Q 侧准备（FWHT 到 FP16 tile），中部为 K 侧（码字→fragment→QKᵀ）与 V 侧（反量化到 shared memory→P×V）两段 Tensor Core MMA，右侧是 FP32 运行状态的闭环回路与最终 BF16 输出。
- 链接同上：`vllm/pull/53060` **(?)**。

---

## 页 60｜TurboQuant: Decode Performance

- 标题：**TurboQuant: Decode Performance**，副题 **Higher throughput at long context lengths**。
- 对比设置：**vLLM TurboQuant（Ours）** vs **FlashAttention (BF16 KV)**，后者按硬件分档：**Ampere · FA2**、**Hopper · FA3**、**Blackwell · FA4**。
- 图元素：分组柱状图，**Shared y-axis · Decode throughput (tokens/s)**，纵轴刻度 **1,000 / 2,000 / 3,000 / 4,000 / 5,000 / 6,000**；横轴为 **Cached context length**（`128`、`4K`、`16K`、`32K`…`128K` 一类刻度，OCR 排序错乱）。
- 柱上标注的加速比（OCR 保留）：**1.28x、3.27x、1.25x、1.27x、2.52x、4.54x、2.74x、4.84x、3.71x、4.03x、3.99x、4.42x**；峰值 **4.84x**。
- 多个柱位标 **FA OOM**，页脚说明 **FA OOM = capacity-skipped**（FP16/BF16 KV 的 FA 在长上下文下显存不足被跳过，故该点无对应基线）。
- 实验条件：**Qwen3-8B, BS=32, cuda graph, decode only, 128 output tokens**，**excludes prefill, TTFT and first token**。
- 严谨性声明：*independent GPU/software runs, cross-GPU throughput directional*（各 GPU/软件版本为独立运行，跨 GPU 的吞吐对比仅作方向性参考）。
- 图描述：随 cached context length 增大，TurboQuant 相对各代 FA 基线的倍数整体上行（128 附近约 1.2–1.3x，长上下文达 3.7x–4.8x），且基线在长上下文多处因容量不足（OOM）缺席。

---

## 页 61｜KVTC: Compression for Storage and Transfer

- 标题：**KVTC: Compression for Storage and Transfer**，副题 **PCA and dynamic quantization across layers and heads**。
- 压缩流水：**Cross-layer/head concat → PCA transform → Dynamic quantization → OPTIONAL nvCOMP DEFLATE**
  - **Compression unit: one token**（压缩单元为一个 token）
  - **Rank principal components (PCs)**，按重要性分配精度：**Important PCs → more bits**
  - 末级为 **LOSSLESS · VARIABLE BYTES**（无损、变长字节），**Higher ratio · variable bytes**
- **Runtime Attention KV Path**（`Pure extra overhead vs. standard KV already in HBM`）：
  `Load Compressed KV from CPU → KVTC decompress on SM → Store standard KV in HBM → Stream HBM→SM → Attention`
- **Why storage-oriented?**（为何面向存储而非在线）：
  - **Granularity mismatch**：Attention 按 **per layer/head** 取用，KVTC 按 **cross layer/head** 组织
  - **Runtime overhead**：**dequant + inverse PCA** 太重，**too heavy for online decode**
- 效果：**8x–64x Compression ratio**；**Max accuracy drop ≤ 0.8 pt with 16x CR**，覆盖 **3 models × 5 benchmarks**。
- 论文链接：`https://arxiv.org/abs/2511.01815`
- 图描述：上部为四段式压缩流水（concat → PCA → 动态量化 → 可选 DEFLATE），中部为「CPU 压缩态 → SM 解压 → HBM 标准态 → 注意力」的运行时路径，下部为「面向存储」的两条理由对照。

---

## 页 62｜KVTC: Integration and Pipelined Decompression

- 标题：**KVTC: Integration and Pipelined Decompression**；副题 **A pluggable codec backend for inference engines and KV cache management frameworks**（可作为推理引擎与 KV cache 管理框架的可插拔 codec 后端）。
- **Pipelined decompression**（流水化解压）对比：
  - **Before**：`PCIe H2D | H2D | H2D | H2D` 与 GPU compute `DQ0 → Full GEMM×8 · C0`、`DQ1 → Full GEMM×8 · C1`、`DQ2 → Full GEMM×8 · C2` 串行交替；每段解压后都要做**全量 GEMM×8**。
  - **After**（含 warm-up）：解压 `DQ0 / DQ1 / DQ2` 与 **M-sharded TP-GEMM · M/8 per GPU**、**AllGather(M)**（`AGC0 / AGC1 / AGC2`，产物 **[M,D]/GPU**）重叠流水。
  - 收益标注：**Time saved**（节省的时间，因前后两排时间轴长度差）。
- **Pluggable integration architecture**（可插拔集成架构）分层：
  - **Inference Engines**：`vLLM`、`SGLang`、`TensorRT-LLM`
  - **KV Cache (management)**：`LMCache`、`HiCache`、`Dynamo`（另有 OCR 作 `aement` 的截断词，疑为 `Management` **(?)**）
  - **Codec API** / **GPU Connector**
  - **Algorithm**：`KVTC STORE/COMPRESS` —— **KV blocks**、**Layout & chunking**、**PCA/LRPCA**、**DP-planned mixed precision**、**Packed chunks**
- 图例：**Current integration** vs **Candidate adapter**（已集成 / 候选适配）。
- 图描述：下半部分为四层堆叠的架构框图（引擎 → KV cache 管理层 → Codec API → 算法内部步骤），上半部分为两条时间轴，下面一条把解压、TP-GEMM、AllGather 三段错位排布以显示并行度提升。

---

## 页 63｜KVTC: Single-Request TTFT

- 标题：**KVTC: Single-Request TTFT**；结论句：**Smaller transfers reduce TTFT by 5.5% to 10.6%**(?)（更小的传输量把 TTFT 降低 5.5%–10.6%；正文里出现的最大降幅为 **−10.8%**，与标题的 10.6% 不一致，以 OCR 为准存疑 **(?)**）。
- **SETUP**：**GLM-5.1** FP8 · **8× Hopper GPU** · **PCIe Gen5** · **TP = 8** · **vLLM + LMCache** · **Compression ratio: 4.7x**（`GLM-5.1` 版本号 OCR 如此，存疑 **(?)**）。
- 图元素：堆叠柱状图，纵轴为 **Prefill（ms）**（OCR 作 `(sW)`，疑为 ms **(?)**），刻度 200 / 400 / 600 / 800 / 1000；横轴按上下文 **32K / 64K / 128K / 192K** 分成四组，每组两根柱：**uncompressed baseline** 与 **KVTC**；堆叠分量为 **Prefill** + **Vanilla PCIe transfer / KVTC transfer + decompression**，**red = wall-clock TTFT**。
- 四组主数值与降幅（OCR 依序对应，配对关系为推断 **(?)**）：
  - **843ms → 773ms**，**−8.4%**
  - **591ms → 558ms**，**−5.5%**
  - **407ms → 377ms**，**−7.4%**
  - **204ms → 182ms**，**−10.8%**
- 其余残留数值（分量为传输/解压段等）：**582 / 514**、**390 / 355**、**207 / 180**、`200 197 201 203 261 259`、**113 / 98**、**91 / 84**。
- 页脚定义：**Prefill = TTFT − LMCache load latency**，堆叠分量分别呈现，红色为墙钟 TTFT。
- 图描述：上下文越长，未压缩基线越高（843ms → 204ms 一线对应最长上下文组的最低值），KVTC 柱始终略低于基线，降幅随上下文增长而扩大（5.5% → 10.8%）。

---

## 页 64｜KVTC: Throughput Under Memory Pressure

- 标题：**KVTC: Throughput Under Memory Pressure**；结论句：**Compression prevents the cache-capacity cliff**（压缩避免了「缓存容量悬崖」）。
- **Setup**：**GLM-5.1-FP8, TP=8 on 1 node with 8× Hopper GPU SXM 141GB**（NVLink **900 GiB/s**，PCIe Gen5 **465 GiB/s per GPU**(?)），**vLLM + LMCache**，**128 GiB CPU-DRAM**，**18K-token chunks**(?)（OCR 作 `L18K-tokenchunks`，疑为 `1K/18K` 之类 **(?)**），**NUMA interleave = all**，**prefix caching off**，**KVTC CR 8x**。
- **Problem — Vanilla degrades as memory shrinks**；**Resilience — KVTC holds performance under pressure**。
- 左图 **Capacity sweep · concurrency = 16 · Higher is better**：横轴 **Host memory capacity (GiB) — decreasing**（**400 / 300 / 200 / 96 / 80 / 60** 一类刻度，OCR 排序倒置），纵轴 **Output tok/s**，两条曲线 **KVTC** vs **Vanilla**；纵轴刻度含 **140 / 120 / 80 / 60** 与 **50.0** 等。
- 右图：**Concurrency = 16**，**Output tok/s** 与 **LMCache hit rate** 两条对照；标注 **Eviction pressure**、**Host memory constrained**、**124.7**、**11.9%**、**2.49x**、**−64%**、**+62.8pp**、hit rate 轴刻度 **0 / 20% / 40% / 60% / 80%**。
- **Takeaway 文字**：*Vanilla hits a capacity cliff as memory shrinks: cache eviction lowers hit rate and throughput.*
- **Low overhead — Capacity sufficient (400 GiB)**：**Throughput delta: +3.6% to −2.1%**，**~4.7x smaller host-memory footprint**。
- 表格（**Mean TTFT V/K**、**Output tok/s V/K**、**Δthroughput**，多组 concurrency）：
  - **38.3 / 38.1**，**−0.5%**，**0.58 / 0.53 s**
  - **72.8 / 71.8**，**−1.4%**，**0.57 / 0.56 s**
  - **129.4 / 126.7**，**−2.1%**，**0.71 / 0.67 s**
  - **127.1 / 131.0**，**+3.1%**，**13.1 / 12.9 s**
  - **125.8 / 130.3**，**+3.6%**，**36.54 / 36.54 s**
- 关键点（96 GiB / concurrency 16）：**Output throughput 2.49x**、**Mean TTFT −64%**（`108.8 → 39.1 s`）、**LMCache hit rate +62.8pp**（**11.9% → 74.7%**）。
- 收尾句：*…KVTC reduces memory footprint by ~4.7x with negligible performance overhead.*（KVTC 把内存占用降低约 4.7x，性能开销可忽略。）
- 图描述：随 host memory 从 400 GiB 压到 96 GiB，Vanilla 的吞吐与 hit rate 双双断崖式下跌（hit rate 跌到 11.9%），KVTC 曲线基本走平并保持约 2.49x 的吞吐优势。

---

## 本段主题与脉络

本段前四页（49–52）是「大规模训练」部分的收尾：STEP 3 在 MoE 层做内核级优化（融合执行、通信重叠、ring buffer 复用），STEP 4 处理 CP 负载不均——等 token 不等于等工时，于是用 zigzag 对角线配对重分配 indexer 权重，代价是额外开销且在 64K 下无收益；最后以 Lessons 收束到 Megatron Core 的可组合并行与 DeepSeek-V4-Pro 参考配方。第 53 页起切换赛道：从训练转向推理服务，以 KV Cache 为瓶颈（容量 / HBM 带宽 / 系统 I/O 三重约束）立题，先给训练期与推理期的压缩方法分类，再把 TurboQuant（在线量化路径）与 KVTC（存储/传输路径）分别定位，随后各自展开原理、内核实现与实测收益。

---

> 备注：本段 16 页（`049`–`064`）OCR 文本文件均存在，无缺页。OCR 残缺最严重的是页 52 的配方文件名与页 63 的柱值分组，上文已逐处标注 `(?)`。
