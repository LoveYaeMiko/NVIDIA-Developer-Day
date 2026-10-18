# 三、技术主线剖析

以下按五条主线展开，每条主线给出"问题—手段—数据—要点"四层，数据只引用幻灯片上的原始数值。

## 3.1 主线一：把 MoE 的通信与计算压进一个内核（第 1–34 页）

### 3.1.1 问题：MoE 层是"四段式"的，通信插在中间

一个 EP（专家并行）MoE 层天然分成四段：**dispatch（把 token 按专家路由 all-to-all 发出去）→ FC1 + SwiGLU 激活 → FC2 → combine（把结果收回来）**。四段串联执行时，通信期间计算单元空闲、计算期间网络空闲。第 1 页用三行时间轴把这件事画得很直白：

| 方案 | 排布方式 | 理论加速比 |
|---|---|---|
| (a) Naive Solution | `Dispatch → L1 → Act → L2 → Combine` 严格顺序 | 1.00×（基线） |
| (b) Comet | 通信（Dispatch/Combine）与计算（Act 等）拆成两条流水线并行推进 | **1.42×** |
| (c) Ours（MegaMoE） | `Dispatch All-to-All` 与计算重叠，计算侧按 `L1/L2` 交替重复，再逐段插入 `Act`、`Combine`；通信按 `Expert Wave 1/2/3` 分波，波间为 `Combine All-to-All` | **1.92×** |

关键差别在颗粒度：Comet 是"通信/计算两条大流水"，MegaMoE 是"按专家波次把通信切成多段、与 L1/L2 交替填满时间轴"。

### 3.1.2 代价：融合不是免费的（第 3 页）

讲者专门用一页讲"融合带来的挑战"，这是理解后续十一项优化的钥匙：

- **通信和计算跑在同一个 SM 上**，通信要**借用计算侧的 shared memory**；
- 通信流量会**干扰主循环的 TMA 效率**；
- `NVFP4` 把 L1/L2 的耗时减半，但 combine 数据"一直"是 bf16，于是 **NVLink 流量的相对代价被放大**。

三条叠加的效果就是：GEMM 效率与 NVLink 效率相互牵制（图中直接标为"compute 与 comm 之间的干扰"）。后面的优化几乎全部是在给这三条还债。

### 3.1.3 手段：三条优化清单（第 4–5 页大纲）

| 优化方向 | 具体条目 | 主要落地页 |
|---|---|---|
| **GEMM 性能** | 大 tile（256×256）、swapAB 动态 tileN、TMEM 内 epilogue 转置 | 6–8、19 |
| **降低通信/计算干扰** | MEMBAR 同步优化（`batch-commit`、`async UREDGR`）、只留一个活跃 dispatch warp | 13、27 |
| **combine 性能** | 三种流量模式、FC1/FC2 相位交织、自适应流量控制、低精度 combine 数据类型 | 14–16 |

**（1）GEMM 侧：256×256 与 "overlapping acc"**
把 tile 从 256×192 改成 **256×256**，理由是"更大的 tile 有更充裕的访存预算"；难点是寄存器/累加器放不下，于是用**累加器重叠（overlapping ACC）技巧**让 256×256 近似获得"两段式 acc"的效果（第 6 页）。

**（2）GEMM 侧：swapAB 动态 tileN（第 7、19 页）**
**根因**：SM90 的 WGMMA 形状是 **`m64nNk32`**——M 每个 atom 固定为 64、N 可灵活（最小到 8）。于是非 swapAB 下 token 只能落在 M 维，token tile 最小就是 64：解码类负载常常只有 8 个 token，**64 行里有 56 行是 padding**（第 19 页原话：`56 of 64 token rows wasted`）。**做法**：把 token 维换到 N 维，`M = weight channels（128 / 256，恒密）`、`N = tokens（8 / 16 / 32 / 64 / 128）`，于是 `M128/256 × N8` 的 tile 几乎"全是有用的"，**tile 利用率最高提升 8×**。**代价与技巧**：swap 本身只是**纯 stride view、零拷贝**；expert 维变成 GEMM-A 的 `L` mode，**TMA descriptor 变成 tile-invariant**；转置被推到 epilogue（FC1 走 R2S + SMEM 寻址，FC2 干脆不落 SMEM、直接从寄存器发 BF16 的 `STG`）；而"8 行 gate/up 交错"恰好落在同一线程的寄存器对上，**folding 不需要任何 shuffle**；同时它与主 kernel 共用 MMA mainloop 与 warp topology，维护成本低。

**（3）GEMM 侧：TMEM 内 epilogue 转置（第 8 页）**
这一页的方法论比结论更有意思：起点只是一个 `16×8 → 32×4` 的 copy-pattern 小技巧（`2× LDTM.16dp128b + STTM.32dp32b`），讲者与**LLM 迭代讨论**后把"每条 LDTM、寄存器置换、STTM"统一建模为**作用在 thread 位 / register 位 / TMEM-DP 位 / column 位上的位级置换**，再用 **Cayley/BFS 搜索**找最优组合，最后用**模拟器回放验证**，得出可用的完整 TMEM 转置（32×32、16×32→32×16），并集成进 CuTe 内核。页面上那五个步骤 `Observe → Model with LLM → Search → Validate → Integrate` 值得单独记住。

**（4）精度策略：per-tensor 与 blockwise 是两种不同的工程取舍（第 20 页）**

| | per_tensor | blockwise（DeepGEMM 风格） |
|---|---|---|
| 权重缩放 | 每个专家一个标量 | 128×128 块 |
| 累加 | 1×acc / 2×acc，按 K tile 做 FP32 promote | promote 内建 |

这也解释了第 33 页为什么要把两种量化模式分开测：blockwise 的量化粒度更细、GEMM 更重，单内核融合的收益结构随之改变。

**（5）同步与调度：把"等待"变成"重叠"（第 27–32 页）**
这一段是整场最"硬核"的部分，全文都是微架构级的取舍：

| # | 优化（页） | 做法 | 效果 |
|---|---|---|---|
| 1 | Cooperative warp-group scheduling（21） | 协作式 warp-group 调度，单 task tile `M64×N256` | 多个启发式表 bucket 仍由协作模式取胜（如 blockwise ≥512 恒用 `(64,128)`） |
| 2 | Task-tile ping-pong（22） | 任务 tile 乒乓交替 | 保持流水不空转 |
| 3 | Multi-CTA CGA + TMA multicast（23） | `2×2`（亦可 2×1/1×2）CGA 簇，按簇分组 task tile | TMA 多播降低重复搬运 |
| 4 | Mainloop & Store 流水（24） | WGMMA 软件流水（`k_pipe_mmas=1`）；FC2 R2S+TMA store 两段式，SMEM stage 4 KiB；228 KB SMEM 预算动态填满 | 延迟隐藏 |
| 5 | All-Register epilogue fusion chain（25） | R2S 单次过 SMEM → TMA 批量 store，并在链条里做 FP8 requant | 减少一次 SMEM 往返 |
| 6 | Gate/Up interleave = 8（26） | 依据 WGMMA 寄存器布局决定交错因子 | 让 FC1 的 gate/up 配对读取不额外搬数 |
| 7 | 单个活跃 dispatch warp（27） | 只保留 1 个 warp 做 dispatch（约 **132 行在飞**已超过 NVLink 带宽时延积） | 实测 **1 warp > 2 > 4**：更深的读队列会拉长每次往返并与 GEMM 争用 |
| 8 | 折叠 producer warp-group + 寄存器重排（28） | 让"双 WG 协作"变得可行 | blockwise 512–32768 全部切到 `M64N256`，**+11% ~ +30%，几何平均 +15.8%** |
| 9 | 提前发布 `fc1_done`（29） | 发布点上移，FC2 tile 更早通过就绪检查、更早发 TMA load | 缩短等待 |
| 10 | 调度器分组 + `fc1_done` 自旋（31） | 把小 bucket 下的调度组扩大到 **264（≈6 个专家）**，使 FC2 tile 到达时 `fc1_done` 已完成 | 消除 activation TMA producer **约 25%** 的自旋时间 |
| 11 | 16 字节 FC2 输出（32） | 4×4 butterfly transpose（4 次 shuffle）让每条 lane 持有某行连续的 8 列 | `8× STG.32`（swapAB 时 `8× STG.16`）→ **1× `STG.128`** |

**（6）架构：一个 kernel 做所有事（第 17–18 页）**
`Overall Architecture: One Kernel Does Everything` 的四段数据通路环流是：**Dispatch（4 个 dispatch warp 通过 NVSHMEM symmetric heap 把各 rank 的 token 拉到本地 pool）→ FC1（pool 的 FP8 view 直接被当作 GEMM 的 activation，零拷贝、零中间 kernel）→ FC2（通过 GMEM counter 握手 `fc1_done_counter` 消费 FC1 输出）→ Combine（写回 source rank）**。Combine 的组合方式是 **`3 种 executor × 2 种 reduce 落点 = 6 种模式`**（这正好解释了第 34 页"six modes"的来历）。与常规基线相比，关键差别是**通信 warp 与 GEMM warp 同驻一个 SM 且真正并发**：token 一到就被计算。

第 18 页的 warp 分工表给出了这套"同驻"的具体编制（总量 **20 warps / 640 threads**，`setmaxnreg` 按角色重新分配，其中 epilogue 拉满到 **256**）：

| 角色 | Warps | setmaxnreg | 职责 |
|---|---|---|---|
| epi / WGMMA WG | 4×(1–2) | 200–256 | 发 WGMMA + SwiGLU / quant / store |
| TMA-A | (?) | — | 装 activation 与 `fc1_output`；FC2 的 `fc1_done` 自旋 |
| TMA-B | (?) | — | 装权重（与 FC1 解耦，不等 counter） |
| sched | (?) | — | 发布 work tile + 专家预取 |
| dispatch | (?) | — | 跨 rank 拉 token（MegaMoE 的核心动作） |
| token-back | 4（可选） | (?) | 把 FC2 结果推回 source rank |

（`Warps` 列的个别数字与 `setmaxnreg` 列在 OCR 中粘连，逐行取值不可靠，故标 `(?)`；总量 `20 warps / 640 threads` 为页面明写。）**最反直觉的一点**：这里**没有独立的 MMA warpgroup**——由 epilogue WG 自己发 WGMMA，accumulator 常驻 RMEM（`acc stage = 1`），省掉了一个 warp-group 的握手中转。

### 3.1.4 数据：token sweep（第 33 页）

| 项目 | 设定 |
|---|---|
| 硬件/并行 | 4× H200，EP4 |
| 模型形状 | DeepSeek-V4-Pro shape，完整 MoE 层 forward |
| 统计口径 | p50 over the slowest rank |
| token 档位 | 8 / 16 / 32 / 64 / 128 / 256 / 512 / 1024 / 2048 / 4096 / 8192 / 16384 / 32768（13 档） |
| 基线 | 常规四段式：NCCL all-gather / reduce-scatter + CUTLASS grouped GEMM |
| 对照 | MegaMoE：单内核（NVSHMEM dispatch/combine） |

**结果**：

- **Per-Tensor FP8**：13 个档位全部领先 —— 512 及以下 **1.02–1.11×**；1024 起 **1.24–1.35×**（峰值 **1.35×** @8192）；**几何平均 1.16×**。
- **Blockwise FP8**：512 以下差异很小；1024 起 **1.33–1.72×**（峰值 **1.72×** @32768）；**几何平均 1.30×**。
- **讲者的解释**：小 token 数时两者接近，因为此时 **launch 与通信开销主导**；只有当 GEMM 占比上升后，单内核"省掉 launch、省掉中间张量往返、通信与计算交织"的优势才显现。
- **口头补充（录音）**：讲者在总结时给出了档位级的说法——小 token 档位加速约 **3%**、大 token 档位约 **24%**、blockwise 在 **32768** 档可达 **72%**；并解释"小 token 时通信占比高、实际计算量小、launch 也不饱和，两种配置其实都是 **memory-bound**"，而增益来自"通信与计算融合、epilogue 与 SwiGLU 融合，减少了 HBM 读写"。

**要点**：这类优化的收益是**形状相关**的。它不是在所有场景都赢 1.9×，而是"理论 1.92× 的上界 + 实际 1.16–1.30× 的几何平均 + 大 token 时 1.35–1.72× 的峰值"。第 34 页的 Summary 也印证了这一点：`1 个 persistent kernel、6 种模式、2 个变体（non-swap / swapAB）、2 种量化模式、30+ 项优化`，外加 **token-bucket heuristics**——把 sweep 出来每个档位的最优解冻结成查表。

---

## 3.2 主线二：大规模训练的"装得下 / 跑得快"四步法（第 35–52 页）

### 3.2.1 两个挑战（第 35 页）

| Make it fit（装得下） | Make it fast（跑得快） |
|---|---|
| 超大参数量 | 内核与 launch 开销 |
| 模型状态与 HBM 容量 | 重算（recompute）与 offload 代价 |
| 长上下文窗口 | 通信与负载不均衡 |
| 并行的切分布局与拓扑 | （同上） |
| 特性兼容性 | |

取材来源写得很清楚：**公开的 DeepSeek-V4-Pro 架构 + Megatron Core 实现 + NVIDIA Blackwell GPU**。

### 3.2.2 模型为什么这样设计优化（第 37–38 页）

DeepSeek-V4-Pro 的规格是 **1.6T 总参数 / 49B 每 token 激活参数**；结构自下而上为 `Embedding → Pre-Block Mixing → Residual Mixing → Indexer → CSA/HCA（混合注意力）→ DeepSeekMoE → Post-Block Mixing → Transformer Block × L → Prediction Head → MTP Modules（MTP Loss）`；预训练配方从 `4K → 16K → 64K → 1M` 逐级拉长，数据形态从 **dense 过渡到 sparse**。

讲者由此把"模型特征"直接映射到"优化方向"（第 38 页四条）：

1. 模型状态（参数 + 梯度 + 优化器状态）挤占显存余量，限制"更快执行"的余地；
2. **混合注意力**：不同注意力路径（CSA/HCA）需要各自定制的内核；
3. **细粒度 MoE**：专家计算、通信与 buffer 决定性能；
4. **因果长上下文**：同样 token 数也可能对应不等的实际工作量（负载不均）。

### 3.2.3 先定起点：并行布局与显存策略（第 39–43 页）

- **布局三原则**：模型规模定初始布局（为 activation 与 buffer 预留 headroom；专家优先 `EP`、跨域用 `PP`、必要时加 `TP`）；上下文长度定 `CP`；**拓扑定放置**——通信密集的 `EP/TP/CP` 尽量收在 **NVLink 域**内。
- **实例**：256 GPU 的 DeepSeek-V4-Pro 训练，初始布局 **`PP4` + `EP64`**。
- **显存策略随上下文切换**：

| | 64K 上下文 | 1M 上下文 |
|---|---|---|
| 并行度 | `CP16` | `CP64` |
| 每 rank token | 4,096 | 16,384 |
| 策略 | 细粒度重算 + offload | 全量重算 |
| 好处/代价 | 给 CUDA Graphs 留出余量 | activation 压力更大 |

- **先证后调**：用 **4K 上下文的 sparse 代理模型**验证所需特性（kernel fusion、packed sequence、CUDA Graphs 等），再用 profiler 定位。

### 3.2.4 四步 playbook 与实测收益（第 36、44–52 页）

| 步骤 | 做什么 | 模块级收益 | 端到端收益 |
|---|---|---|---|
| **STEP 1** 运行开销与显存权衡 | 64K 场景的主要问题是"大量 GPU idle"；用 **kernel fusion** + **CUDA Graphs**（把 packed sequence 用 padding 变静态后捕获/重放） | — | 为后续提供基线 |
| **STEP 2** 混合注意力 | ① 稀疏注意力"左对齐有效索引、只扫前 L 个 slot"，`topk_length = L` 消除空洞；② Indexer **一个内核内完成打分+选择**（Q·K 量化为 FP8，只写回被选中的分数）；③ Group-O 投影 **8 个小 GEMM 合成一个 batched GEMM** 并启用 FP8 | 稀疏注意力 **25%–30%**、FP8 Indexer **25%–35%**、Group-O batched GEMM **50%–60%** | 64K **+4.6%**、1M **+9.0%** |
| **STEP 3** MoE | MoE 中约 **30%–50%** 是 EP 通信；两条路：**跨 batch EP 重叠**（适合跨 NVLink 域，block size 由 nsys 的 silicon time 决定，代价是显存开销）与**用 megakernel 做细粒度重叠**（NVLink 域内更易融合、显存更省） | 融合执行 + 流水化 token 传输；引用的 MoE 侧手法可带来 **30%–40%** 的 MoE 部分加速 | 64K **+14.0%**、1M **+4.6%** |
| **STEP 4** CP 负载均衡 | 根因：**QK score 计算量随序列长度平方增长**——512K / CP32 下同一组内各 rank 的 GPU time 从 **53.1 ms 一路降到 18.4 ms**（差近 3×），R3 成为掉队者、其余空等；手段：用 **zigzag 布局**把"最轻段 + 最重段"配到同一 rank（R0 同时承担 lightest 与 heaviest） | — | 1M **+12.2%**；**64K 无可测收益**（页面原话 `HOWEVER: the balance process also introduces extra overheads`） |

第 52 页"Lessons for Scalable Training"把结论收成一套可复用配方（针对 64K 与 1M 两种上下文），这与第 36 页的 `+59% @64K、+32% @1M` 相互印证——注意后者是**整条 playbook 叠加后的吞吐收益**，比单步收益之和高得多，说明各步之间存在正向协同（例如 CUDA Graphs 与 batched GEMM 都减少 launch 空隙）。

### 3.2.5 要点

- 这套 playbook 的**顺序很讲究**：先解决"GPU 空转"（STEP 1），再解决"注意力算不动"（STEP 2），然后解决"通信藏不住"（STEP 3），最后才谈负载均衡（STEP 4）——因为前一步的收益会改变下一步的瓶颈占比（第 47 页明说："1M 下 indexer 占 step time 的比例更大"）。
- **收益有适用范围，代价也写在页面上**：STEP 4 的 zigzag 均衡在 **1M 拿到 +12.2%**，而同一页紧接着写 `HOWEVER: the balance process also introduces extra overheads`——所以**在 64K 下没有可测收益**。这说明第 45 页那种"把 step time 按模块拆开"的度量是决策依据，而不是"做了就有效"。

---

## 3.3 主线三：KV Cache 是推理侧的第一性瓶颈（第 53–67 页）

### 3.3.1 定位：三重瓶颈、方法分类与集成判定规则（第 53–56 页）

第 54 页先立题——**KV 显存随上下文长度线性增长**，于是形成三重瓶颈：

| 瓶颈 | 页面对应的因果链 |
|---|---|
| **GPU 容量** | 能装下的活跃请求变少 → 有效 batch ↓、可用上下文 ↓ |
| **HBM 带宽** | 每生成一个 token 都要重读历史 → 每步读取字节数 ↑，直接变成带宽受限 |
| **系统 I/O** | 容量溢出时 KV 要在 GPU ↔ CPU / SSD / 远端之间搬运 → **TPOT ↑**，prefill / decode 被拖慢 |

而系统级权衡是三条互相牵制的目标：**维持并发**（固定 GPU 预算下要么加卡、要么减活跃请求）、**维持 TTFT/TPOT**（代价是 offload 与 re-prefill ↑）、以及**全局服务最优点**。

第 55 页把压缩方法分成两大类：**训练期靠架构设计**（`MQA/GQA`、`MLA/CLA`、`Kimi Linear / CSA·HCA / MSA`），**推理期靠运行时压缩**，后者又有三个子类：**量化**（每元素更少比特，配 scales + 保护离群值）、**存储稀疏**（保留更少 KV，剪枝/淘汰）、**计算稀疏**（只读更少的 KV 或页，查询感知 top-K）。

第 56 页回答"压缩放在哪儿"，给出**两条集成路径与一条判定规则**：

| 路径 | 形态 | 收益 | 代价 / 挑战 |
|---|---|---|---|
| **推理引擎内**（vLLM / SGLang / TRT-LLM） | 在线路径（如 INT8、TurboQuant），**压缩后的 KV 常驻 GPU** | 容量↑、每步 decode 读的字节↓、对引擎**透明** | 需与 attention 融合，且与引擎/模型强绑定 |
| **KV 缓存后端**（LMCache / FlexKV / Mooncake） | 卸载路径（如 KVTC、nvCOMP-ANS），**注意力前先还原成标准 KV** | 存储/传输字节↓、CPU/SSD/远端容量↑，并带来**前缀命中潜力** | **解压开销**、**不直接改善 TPOT** |

> **INTEGRATION RULE**：**`KV-read savings > decompression overhead` → 放进推理引擎；否则退回 KV-cache 后端。** 这条规则比任何压缩比都重要——它把"要不要在线解压"变成一个可测量的不等式。

**口头补充（录音问答）**：讲者把"为什么没有 TPOT 收益"说透了——解压算子"绝对会占用 SM"，实测"对 SM 的压力还挺多"，"解压执行的时候推理会受到一定程度的阻碍"；好在"解压带宽基本在 **50 GB/s** 量级、解压比较快"，因此在真实场景里占用时间短；但干扰会让"整个推理系统的稳态变得特别复杂"，"并发高了以后 TTFT 就会下降"，性能波动约 **−5.6% ~ +5%**。

也就是说，KV 压缩不是"免费午餐"，它的收益主要体现在 **TTFT（跨层/跨节点取 KV 的等待）** 与 **容量（并发数）**，而 TPOT 未必改善甚至可能退化——这条判断在第 67 页 Takeaways 里被明确写成"要在编解码与集成成本之后重新度量质量、TTFT、TPOT、吞吐与缓存命中率"。

### 3.3.2 三条技术路线与各自数据

| 路线 | 机制 | 压缩率 / 收益 | 代价与适用 |
|---|---|---|---|
| **TurboQuant**（在线 KV 量化，57–60） | **随机旋转 → Lloyd-Max codebook 查表 → 逆旋转/反缩放 → 可选 QJL 内积修正**；每向量只存"质心索引 + 残差符号位 + 标量范数"；为解码把 KV 布局改为**页内字段平面化**（16 token 一页、**2,144 B/KV head**），使 32 B 扇区有效字节 **3.68 B → 29.75 B**；解码用 **tiled MMA**（64-token tile、双缓冲、FP32 running state） | Llama-3.1-8B 上 **≥4.5×** 名义载荷压缩；解码吞吐（Qwen3-8B、BS=32、仅 decode）短上下文约 **1.25–1.28×**、长上下文 **2.5–4.8×**（峰值 **4.84×**） | 需要定制解码内核与布局；收益随上下文变长放大，基线在长上下文多处 **FA OOM** |
| **KVTC**（存储与传输压缩，61–64） | **跨层/头拼接 + PCA + 动态量化**（重要主成分给更多比特，可选 nvCOMP DEFLATE），压缩单元为**一个 token**、输出无损变长字节；配套**流水化解压** | 压缩率 **8×–64×**；16× CR 时精度损失 **≤0.8 分**（3 模型 × 5 基准）；单请求 TTFT **−5.5% ~ −10.8%**；96 GiB 压力下吞吐 **2.49×**、TTFT **−64%**、命中率 **11.9% → 74.7%** | 粒度不匹配 + dequant/逆 PCA 太重，故定位在存储/卸载侧；容量充足时几无开销也几无收益 |
| **nvCOMP-ANS**（无损熵编码，65–66） | 用 ANS 熵编码做**无损** KV 传输压缩，解码后可**精确还原** | TTFT **≈1.4×（BF16）/≈1.1×（FP8）**；P90 TTFT 最高 **+18.7%**、均值 **+8.2%**，且**低并发收益最大** | 无损意味着压缩率有限，收益集中在"传输占比高"的低并发场景 |

第 67 页 Takeaways 三句话概括了这一段的工程哲学：**KVTC 在显存压力下保住吞吐；nvCOMP-ANS 在低并发下降低 TTFT 且能精确恢复；任何 codec 都要在"编解码 + 集成"成本之后重新度量质量、TTFT、TPOT、吞吐与命中率。**

三条路线的实现细节（决定它们能不能兑现压缩比的关键）：

- **TurboQuant（在线量化）**：解码路径是 `K/V 向量 → 随机旋转（高维下坐标更平滑、近似独立）→ 预计算 Lloyd-Max codebook 查表（码心 −1.2 / −0.4 / +0.4 / +1.2，只存最近质心的 ID）→ 逆旋转与反缩放 → 可选的 QJL 内积修正（残差投影取符号位）`；每个向量只存**质心索引 + 残差符号位 + 标量范数**，而旋转/投影矩阵与 codebook 是**全局共享、不逐向量存储**。为了让解码真的快，它把布局从"按 token 交错"（`D=128` 时 **134 B/token**，V codes 从第 66 字节开始）改为**页内字段平面化**（16 token 一页、每 KV head **2,144 B**，K/V codes 各 1,024 B、K norms 与 V scales/zeros 各 32 B），使 **NCU 测得的每 32 B 访存扇区有效字节从 3.68 B 提到 29.75 B**；解码内核按 **64-token KV tile** 流式加载、双缓冲异步、把码字直接映射成 MMA fragment，并用 **FP32 running state（max / exp sum / weighted output）跨 tile 保持 + 在线 softmax 重缩放**，最后对多个 KV split 做稳定归约输出 BF16。实测（Qwen3-8B、BS=32、仅 decode、128 个输出 token）相对 FP16 KV 的 FlashAttention 基线，短上下文约 **1.2–1.3×**、长上下文 **3.7–4.8×**（峰值 **4.84×**）；基线在长上下文多处 **FA OOM = capacity-skipped**，这也是"容量本身就是性能"的直接证据。
- **KVTC（存储/传输压缩）**：流水是 `跨层/跨头拼接 → PCA 变换 → 动态量化（重要主成分给更多比特）→ 可选 nvCOMP DEFLATE`，压缩单元是**一个 token**、输出**无损变长字节**；之所以定位在存储侧，是因为**粒度不匹配**（attention 按 per layer/head 取用，KVTC 按跨层/头组织）与**运行时开销**（dequant + 逆 PCA 对在线解码太重）。集成走**可插拔 codec 后端**（引擎侧 vLLM / SGLang / TRT-LLM，管理层 LMCache / HiCache / Dynamo），并把解压与 TP-GEMM、AllGather 做**三段错位流水**来回收时间。
- **nvCOMP-ANS（无损熵编码）**：在 GPU / CPU 内存 / SSD 三级之间搬运 KV 时做 ANS 熵编码，解码可**精确还原**，因此不需要改内核——这也解释了它的收益为何"温和但稳定"。

**KVTC 的两组关键数据**（值得单独记）：① **单请求 TTFT**：GLM-5.1 FP8 / 8×Hopper / PCIe Gen5 / TP=8 / vLLM+LMCache、压缩率 4.7× 下，四组上下文分别 **843→773 ms（−8.4%）、591→558 ms（−5.5%）、407→377 ms（−7.4%）、204→182 ms（−10.8%）**；页面结论句写"降低 5.5%–10.6%"，与柱值最大降幅 **10.8%** 存在小幅不一致（已在明细页标注 `(?)`）。② **显存压力下**（96 GiB 主机内存、并发 16）：输出吞吐 **2.49×**、平均 TTFT **−64%（108.8 → 39.1 s）**、LMCache 命中率 **+62.8 个百分点（11.9% → 74.7%）**；而在容量充足（400 GiB）时开销可忽略（吞吐变化 **+3.6% ~ −2.1%**，主机内存占用约小 **4.7×**）。这一对数据说明：**压缩的价值不是"平均更快"，而是"避免性能断崖"**。

---

## 3.4 主线四：从"算得快"到"找得准"——KV Router 与 Flash Indexer（第 68–78 页）

这一段是中文投影片，讲的是 NVIDIA Dynamo 体系里的**缓存感知路由**，骨架可以概括为"一个成本函数 + 一张位置地图 + 六代索引"。

### 3.4.1 打分机制：一个成本函数（第 69–70 页）

请求路径是四跳：**请求 Token → Block Hash → KV Indexer（给出缓存前缀命中）→ Slot Tracker（给出活跃的 Prefill + Decode）→ Cost Function → 最低成本 worker**；另一条反向通路是 worker 主动推送 **KV Events（缓存新增/删除）** 来更新索引。成本函数写作：

```text
Cost = Prefill 成本 + Decode 成本 +（可选）活跃请求成本
```

页面上的总结句把两类信号的分工说得很清楚：**"缓存告诉我们能省多少，负载告诉我们还能接多少。"** 这也是整个路由设计的核心张力——只按命中率路由会把热节点压垮，只按负载路由会把缓存白白丢掉。第 69 页另给出生产验证：Baseten 侧 **TTFT 快 2×、TPS 1.6×**；另一家（美团）**TTFT 快 2×、KV cache 多 20%**。

### 3.4.2 索引的键设计：为什么必须带位置（第 71–72 页）

Flash Indexer 不生成 token、也不转发请求，只回答一个问题——**"哪里有缓存？"**；四步链路是 `prompt blocks → block_hashes(h0 h1 h2 …) → 实时缓存地图（持续接收 Store/Remove 事件）→ 各 worker 的连续命中深度`（示例输出 `Worker C: 4`、`Worker A: 2`、`Worker B: 0`）。它同时受两个约束：**查询慢了会拖慢路由，状态旧了会错过可复用的 KV**。

索引的键不是 block 内容，而是 **`(position, block_hash)`**：

| key | value（示例） |
|---|---|
| `(0, h0)` | Worker A, C, D |
| `(1, h1)` | Worker A, C |
| `(2, h2)` | Worker C |
| `(3, h3)` | Worker C |

**为什么必须带 position**：同一个 `block_hash` 可能出现在不同位置，只有位置也一致，才说明这段 prefix 真的连续（示例中只有 Worker C 在 position 0–3 全部命中，因此是唯一能连续命中 4 块的 worker）。

### 3.4.3 六代索引演进：从 O(W×D) 到 O(D/J+W)（第 73–76 页）

| 代 | 实现 | 吞吐 | 关键突破 / 瓶颈 |
|---|---|---|---|
| GEN 1 | Naive Nested Dict | **385K** block ops/s | "按 worker 分册的账本"，外层扫 worker、内层扫深度，复杂度 **O(W×D)**；暴露了两个问题：访问模式不对、`local_hash` 需要在 prefix 上下文中消歧（引出 `local_hash` + `sequence_hash` 双哈希） |
| GEN 2 | Rust Actor | — | 单队列保证顺序，但读并发未释放 |
| GEN 3 | Inverted Index | — | 按 block 反置到 worker |
| GEN 4 | Radix Tree | **4M** | **用树表达前缀上下文，碰撞被上下文约束住**；双键设计：`local_hash` 负责遍历、`seq_hash` 负责事件定位；仍是单线程 actor 之后 |
| GEN 5 | Concurrent Radix | — | 读并行、写保序 |
| GEN 6 | **Positional Indexer + Jump Search** | **170M** | `index[position][local_hash]` 直接随机访问某深度，按 checkpoint（0/64/128/…) 整段跳过，只需 `O(D/J+W)`；`SeqEntry::Single` 直接命中，只有 `Multi` 碰撞才 **lazy** 计算 `sequence_hash` |

页面标注的累计提升为 **440× / 42×**；基准配置写明 `24-core Arrow Lake 285K 桌面机 + Mooncake FAST'25 trace + mock engine + 16,384 GPU blocks + 24 个事件处理线程`。这条曲线的意义在于：**索引从"数据结构问题"变成了"系统吞吐问题"**——路由要想真正吃到缓存，索引的查询成本必须低到可以忽略。

### 3.4.4 从组件到服务：Standalone KV Indexer（第 77–78 页）

把索引能力从 router/frontend 里拆出来，做成**可独立查询的服务**。定位写得很克制——它**是**：独立维护 cached KV blocks 的索引、订阅 worker 的 KV cache 事件、返回 prefix overlap；它**不是**：不是 standalone router、不做最终 worker 选择、不维护请求生命周期；**适合**：调试 router 看到的 KV 状态、外部系统自建路由、观察不同 worker/tier 的缓存分布。架构上是"**ZMQ 事件面负责 ingest，HTTP 请求面负责注册、查询与观测**"：worker 用 ZMQ PUB 推事件 → indexer 侧 SUB 收事件 → 写入 `Worker Registry` 与 `(model, tenant) → Radix Tree` → 对外暴露 `GET /health`、`POST /register|/unregister`、`GET /workers`、`POST /query|/query_by_hash`、`GET /dump`、`POST /register_peer|/deregister_peer`、`GET /peers`，查询结果还可按 **gpu / cpu / disk 分层**返回。

---

## 3.5 主线五：智能体推理重写了性能度量（第 79–96 页）

### 3.5.1 度量先变（第 79–81 页）

智能体（Agent）场景把"一次请求"变成"一条会话轨迹"，于是 SLA 表被扩展为：**TTFT、TPOT、请求级 E2E、轨迹级 E2E、首个答案 token 时间、系统吞吐、满足 SLA 的并发 agent 数（AA-AgentPerf），以及全局 KV 缓存命中率 > 90%**。

第 80–81 页用一条真实 trace（Claude Code 轨迹）量化了这件事的规模：

- 单会话**原生上下文窗口 1,048,576**；请求 p99 接近 **900K**；ISL 分布为 32K–128K 占 21%、128K–256K 占 27%、256K–512K 占 30%；
- 单会话**累计输入 token 峰值 219K**；存在 **60 s 级的工具/用户间隔**，甚至出现"第 42 步间隔 46.7 小时后恢复"的极端情况；
- 单步时延分解显示 prefill（TTFT）与 tool/user gap 是主要构成项。

**含义**：单请求 TTFT/TPOT 已经描述不了体验；**"间隔可达数十分钟、KV 早已被逐出、恢复时要么重算、要么从存储取回"**才是常态。

### 3.5.2 四组目标：从容量到路由（第 82–92 页）

| 目标 | 页面 | 关键事实 |
|---|---|---|
| **容量**：1 GB 能装多少 token | 85 | 每 token KV **55.9 KB**（MLA 43.9 / DSA 9.8 量级拆分）；1 GB、单节点 8 GPU 时，TP8 复制 8 份仅约 **33 个会话**，而 **DEP 约 200 个会话**；同节点 token 容量 **1.26M → 7.6M（6×）** |
| **命中率**：实际命中率 ≈ 理论上界 | 86–87 | GPU 侧 G1（约 53 GB/rank）、主机侧 G2（512 GB/节点）、G3（溢出到 1 TiB 量级）；重算占 **8.2%**、与理想差距 **−3.9 pt**；会话并发 16/32 时的容量与 in-flight 余量被逐项列出 |
| **并发**：decode 并发必须跟得上 | 88 | TP8 的 ceiling 为 33 会话；DEP 下按 `1.26M vs 7.6M tokens/node` 逐档对比 |
| **路由**：智能体路由策略 | 89–90 | Hard affinity 在 DEP 下出现**负载不均**（32 个 DP rank 中大量时段占据 ≥90%）；给出 KV-aware / Hard / Soft affinity 的取舍与 NIXL 点对点拉取 |

第 89 页那张"每分钟一格的 KV 占用热力图"值得单独注意：它把"Hard affinity 会把某些 rank 长期顶到 90%+"这件事可视化成了一个失败模式，等价于给"缓存亲和"这条路画了一条边界——**缓存亲和必须与负载均衡联立求解**。

### 3.5.3 会话网关 ThunderAgent（第 91–96 页）

方案是一个**全局控制回路**：每 **Δt = 5 s** 一拍，按 `util = 活跃 program 的上下文量 ÷ GPU KV 池` 决定 `resume / pause`：

- 门限：**util < 0.80 恢复、0.80–0.85 观察、> 0.95 暂停**（页面写 `0.80 / 0.85 / 0.95`，并有"97% resume 上限"的字样）；
- 恢复顺序：优先选"上下文最小、重算最便宜"的 program，并落到**空闲 KV 最多**的 worker；等待超过 **1800 s** 则强制恢复（避免饿死）；
- 暂停时若命中冷区，则**把 KV offload 出去**（第 94 页：G1 95%、G2 60%，且多 program 共享同一份 KV 副本）。

**实测（第 93 页）**：SWE-Bench Lite、GLM-5.2、8× NVIDIA Hopper、会话并发 32 —— **E2E 均值 −51%、TTFT p50 −87%、TPOT 减半、生成吞吐均值 ×1.6**。

**延伸到 RL rollout（第 95 页）**：与 Dynamo + VeRL 集成，Uni-Agent SWE-Bench、Qwen3-Coder-30B-A3B-Instruct、8×Hopper、rollout-only 场景，页面标注 **+16.5% / +6.8%** 两类提升。

第 96 页"Assets & Future Work"收尾：文档、Flash Indexer 与 Dynamo 的集成 PR（页面上可见 `#11447 / #11787 / #11616` 等编号）、以及 ThunderAgent v2 等后续工作。

---

## 3.6 贯穿全场的方法论

五段技术内容风格迥异，但方法论高度一致，抽出四条：

1. **测量先行，把瓶颈拆到可决策的粒度**。第 45 页把 step time 按 `MoE experts / EP comms / Indexer + CP comm / Sparse Attn / Group-O Proj / Others` 分段堆叠，才好判断"下一步该打哪一块"；第 44 页直接指出"64K 场景的主要问题是大量 GPU idle"。
2. **先抬高理论上界，再用工程把它兑现**。1.42× → 1.92× 是上界推导，后面的 11 项优化是把 1.92× 兑现成实测 1.16–1.30×（几何平均）；对应地，第 34 页用 token-bucket 查表把"每个形状最优解"冻结下来。
3. **人类硬件直觉 + LLM 辅助建模**。第 7–8 页明确把这套组合写进了方法论页：人提出 `16×8→32×4` 的观察，LLM 把问题统一成位级置换模型，再用 BFS 搜索 + 模拟器验证 + CuTe 内核集成。
4. **如实记录负结果与代价**。CP 均衡在 64K 下"no measurable perf gain"（均衡开销抵消了收益）、KV 压缩"没有直接的 TPOT 收益"、combine 数据是 bf16 带来的 NVLink 相对代价——这些都留在幻灯片上，构成了这套材料可信度的重要来源。
