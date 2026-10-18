# 第 17–32 页 OCR 结构化摘要

> 来源：`_build\ocr\text\017_*.txt` ～ `032_*.txt`（课堂投影片手机翻拍照片的 OCR 文本，16 页全部存在，无缺页）
> 说明：术语、缩写、模型/内核/硬件名、精度格式、数字与倍数均按 OCR 原样保留；粘连的英文已按语义拆分；不确定处标 `(?)`；凡 OCR 未出现的内容不作补充。

---

## 页 17｜Overall Architecture: One Kernel Does Everything

- **总体架构：一个 kernel 包揽全部（One Kernel Does Everything）**，四个阶段在同一条链上：
  - **Dispatch**：`4 dispatch warps` 通过 **NVSHMEM symmetric heap**，把 token 从 every rank 拉到本地 pool。
  - **FC1**：pool 的 **FP8 view** 被直接当作 GEMM 的 activation 消费 —— **zero copy, zero intermediate kernels**。
  - **FC2**：通过一个 **GMEM counter handshake**（即 `fc1_done_counter`）消费 FC1 的输出。
  - **Combine**：FC2 结果写回 source rank；组合方式为 **three executors × two reduce placements = six modes**。
- **vs. baseline**：communication warps 与 GEMM warps **co-resident 且并发**；token 一到就算（tokens are computed as soon as they arrive）。
- 页脚总结句（OCR 残缺，`...es live in one persistent kernel`）：dispatch / GEMM / token-back warps 全部 co-resident 于**一个 persistent kernel** 内，token 到达即被计算。
- 图为一条从左到右的数据通路，OCR 中可见的标签依次为：
  - 左端 `Peer ranks` → **NVSHMEM symmetric heap** / `NVLink`；
  - 中间 `local FP8 pool (GMEM)`，旁注 `4 dispatch warps pull`、`zero-copy FP8 view`、`token_buffer`（OCR 作 `11_token_buffer`，前缀不清）**(?)**；
  - 计算段 `FC1 WGMMA + SWiGLU + FP8 requant` → `fc1_output workspace (GMEM)` → `FC2 WGMMA`，段间以 `TMA store` 与 `fc1_done_counter handshake` 连接；
  - 右端 `BF16 output`，回写段标 `Combine — writeback to source rank`，执行方式为 `epi-warp STG/REDG or bulk push`。
  - 图意：通信侧（NVLink/NVSHMEM pull）与计算侧（FC1/FC2 WGMMA）在同一 kernel 内左右咬合，形成 拉取 → FC1 → 握手 → FC2 → 回写 的环流，中间无独立 kernel 边界。

---

## 页 18｜Warp Specialization

- 该页是一张 **warp 角色分工表**，表头为 `Role | Warps | setmaxnreg | Duty`（OCR 列名残缺，第 3 列数字与第 4 列职责有串行，以下按可辨读重建，(?) 标注不确定项）：

  | Role | Warps | setmaxnreg | Duty |
  | --- | --- | --- | --- |
  | epi / WGMMA WG | 4×(1–2) | 200–256 | Issue WGMMA + SwiGLU / quant / store |
  | TMA-A | 32**(?)** | —**(?)** | Load activation / `fc1_output`；FC2 的 `fc1_done` spin |
  | TMA-B | 32**(?)** | —**(?)** | Load weights（independent of FC1，no wait on the counter） |
  | sched | 40**(?)** | —**(?)** | Publish work tiles + expert prefetch |
  | dispatch | 48**(?)** | —**(?)** | Pull tokens across ranks（**MegaMoE**） |
  | token-back | 4 (opt.) | 32**(?)** | Dedicated push of FC2 results back to the source rank |

  > 注：`Warps` 列的 OCR 数字多与 `setmaxnreg` 列粘连（如 `32↓`、`40`、`48`），无法确认逐行取值；**总量以页面明写的 `20 warps / 640 threads` 为准**，各角色具体 warp 数仅作参考 **(?)**。
- **总量与配额**：`20 warps / 640 threads`；**setmaxnreg 按角色重新分配**（rebalanced per role），其中 **epi 拉满到 256**。
- **关键设计**：没有独立的 MMA warpgroup —— **由 epilogue WG 自己发 WGMMA**，accumulator 常驻 **RMEM**（`acc stage = 1`）。

---

## 页 19｜The swapAB Variant: the Cure for Small Token Counts

- **Problem**：`SM90 WGMMA` 是 **m64nNk32**，非 swapAB 下 token tile 最小就是 **64**；decode 类负载大部分 tile 都浪费在 padding 上。
- **swapAB 的做法**：`M = weight channels (128 / 256)`，`N = tokens (8 / 16 / 32 / 64 / 128)`。
  - WGMMA 的 **N 维最小可到 8** → token tile 可以小到 **8**，**up to 8× better utilization**。
  - **M 轴变成恒密的 channel 维**，因此即使 token 数极小也能填满 SM。
- **Implementation highlights**：
  - swap 只是**纯 stride view，zero copy**；expert 维变成 GEMM-A 的 **L mode**，于是 **TMA descriptor 是 tile-invariant 的**。
  - transpose 挪进 epilogue：FC1 走 **R2S SMEM addressing**；FC2 **丢掉 TMA store**，直接从寄存器发出 BF16（**STG**）。
  - **8 行 gate/up interleave 正好落在同一线程的寄存器对上 → folding needs zero shuffles**。
  - **与主 kernel 共用 MMA mainloop 与 warp topology → low maintenance cost**。
- 图为左右对照：
  - 左 `non-swap: tokens on M-tile, M64×N128` —— `8 real tokens` 落在 M 方向，标注 **padding — 56 of 64 token rows wasted**。
  - 右 `swapAB: tokens on N-tile, M128/256 × N8` —— `same 8 tokens` 落在 N 方向，标注 **N=8 tokens, all useful**。
  - 中轴说明：`WGMMA m64nNk32: M is fixed at 64 per atom`，`N is flexible down to 8 — token tile 8/16/32/64/128`；`M = weight channels (always dense)`。
  - 结论标签：**up to 8× better tile utilization**；OCR 残句 `...tches leave most of the tile empty`（指非 swapAB 的 tile 大量空置）**(?)**。

---

## 页 20｜FP8 Quantization: per_tensor vs. blockwise

- 该页是一张 **per_tensor 与 blockwise（DeepGEMM style）逐项对照表**：

  | 项目 | per_tensor | blockwise (DeepGEMM style) |
  | --- | --- | --- |
  | activation | scalar FP32 | **per-token × K128 block** |
  | weight | per-expert scalar | **128×128 block** |
  | FC2 activation | scalar（two-pass precompute） | **per-token × K64**（online in FC1 epilogue） |
  | dequant | scalar multiply in the epilogue | **per-K-tile promote in the mainloop** |
  | accumulation | 1×acc / 2×acc（FP32 promote per K tile） | **promotion built in** |

- **blockwise 的 online requant 链路**：register **absmax** → `shuffle_sync_bfly` **quad reduction** → **single-lane STG** 写出 scale → 再乘（乘回，OCR 行尾断在 `multiply by ...`，下一页补全为 reciprocal）。
- **blockwise half-K split**：scale load 与另一半的 WGMMA 相互重叠（scalar loads overlap the other half's WGMMA）。
- **零额外同步**：`SF shares the TMA stage barrier with A/B (merged tx_count)` —— 量化 scale 因子复用 A/B 的 TMA stage barrier，**zero extra synchronization**。

---

## 页 21｜Optimization 1: Cooperative Warp-group Scheduling

- **cooperative 模式下 warpgroup 数量随 tile 形状走**：
  - `N=256`（swapAB `M=256`）：**两个 warpgroup 协作切同一 task tile** —— 各管一个 `N=128`（`M=128`）slice，各自发自己的 WGMMA、各自跑自己 slice 的 epilogue。
  - `N=128`（swapAB `M=128`）：**单 warpgroup 精简配置（8 warps）**；epi 寄存器可拉满到 **256**。
- **Task boundary**：用 **CTA-level NamedBarrier**；所有 epi warps 一起进入下一个 task。
- **Characteristics & trade-offs**：
  - WGMMA → epilogue 在单个 WG 内**串行**，会暴露 epilogue latency；但 **TMA warps 是独立的**，下一个 task 的 load 能继续 prefetch。
  - **大 tile（N=256）摊销 A/B load、减少 task 数** → 更适合 GEMM-bound 的大 batch。
  - 启发式表里仍有大量 bucket 由 cooperative 胜出（例如 **blockwise ≥512 一律用 (64,128)**；**per_tensor 16384 用 (64,256)**）。
- 图为 `One task tile: M64×N256 (swapAB: M256 × token N)` 的切分与流水：
  - `WG0 owns N=0..127`、`WG1 owns N=128..255`，各自 `WGMMA + epilogue`。
  - 时间轴：`WG0: WGMMA task0 (own half) → epilogue task0 → WGMMA task1 → epilogue task1`；`WG1` 同构并行。
  - 每一 task 边界标 `CTA NamedBarrier` —— **all epi warps advance**。图意：两个 WG 在 N 方向对半分工，靠 CTA 级 barrier 对齐推进，没有跨 WG 的语义依赖。

---

## 页 22｜Optimization 2: Task-tile Ping-pong

- **两个物理 warpgroup 交替消费 task stream 中的 task**（ping-pong）。
- **两套 PipelineOrder barrier**：
  - `math_wg_order` 串行化 **WGMMA issue 权**；
  - `epi_wg_order` 串行化 **epilogue 所有权**。
- **重叠方式**：当 WG-A 占着 tensor core 时，WG-B 跑上一个 task 的 `SwiGLU / quant / store` —— **epilogue latency 被完全隐藏**。
- **被跳过的 peer task** 通过 `advance_pipeline_state` 推进，是**纯状态记账，不碰 mbarrier**。
- **Retire-handoff 沿用 CUTLASS 顺序**：tail async stores → publish done flag → hand over epilogue ownership → 然后 wait for the descriptor **two steps ahead**。
- 图为两条泳道的时间轴（`WG-A` / `WG-B`），横轴 `time →`：
  - `WG-A: WGMMA task0 → epilogue task0 → WGMMA task2 → (wait) → epilogue task2`
  - `WG-B: wait(math order) → WGMMA task1 → epilogue task1 → wait → WGMMA task3`
  - 泳道之间标 `math order` / `epi order` 两列 barrier。
  - 图注：**WGMMA never overlaps across the two WGs（tensor core 是独占的）**；**one WG's epilogue overlaps the other WG's WGMMA → epilogue latency is hidden**；补充适用配置 `(swapAB M=128)`。

---

## 页 23｜Optimization 3: Multi-CTA CGA + TMA Multicast

- **Cluster 形状**：`(2,1)` / `(1,2)` / `(2,2)`；cluster 内**每个 CTA 各自跑一个独立的 1-CTA WGMMA**。
- **多播方向**：**A 沿 cluster-N 多播，B 沿 cluster-M 多播** → 共享 operand 的 **L2/DRAM traffic 减半**（is halved）。
- **调度粒度**：scheduler 以 cluster 为粒度把 task tiles 成组（groups task tiles at cluster granularity）。
- **计数器隔离**：`fc1_done_counter` **每个 CTA 独立 slot** —— cluster peer 之间**没有 false-sharing 等待**。
- 图为 `CGA cluster 2×2 (also 2×1 / 1×2)` 的四象限布局：
  - 上方源数据：`A tile (GMEM/L2)`、`B tile (GMEM/L2)`。
  - 四角各一个 `1-CTA WGMMA`：`CTA(0,0)`、`CTA(0,1)`、`CTA(1,0)`、`CTA(1,1)`。
  - 箭头分别为 `A multicast (cluster-N)` 与 `B multicast (cluster-M)`。
  - 图注：一次 A load 服务沿 cluster-N 的 CTAs，一次 B load 服务沿 cluster-M 的 CTAs → 共享 operand 的 L2/DRAM 流量（减半）；而 `one_counter stays per-CTA (no false sharing)`。

---

## 页 24｜Optimization 4: Mainloop & Store Pipelines

**Mainloop**
- **WGMMA software pipelining（`k_pipe_mmas=1`）**：稳态下**保持 1 个 WGMMA group in flight**，推迟 `consumer_release` —— **TMA refill 与 WGMMA 完全重叠**；`producer_acquire` 只回收上一组。
- **TMA producer `try_acquire` peek**：探测下一 stage 的可用性，**跳过大部分 mbarrier wait**。
- **A/B pipeline stage 数动态填满 228 KB SMEM**（`misc budget` 只占 **1 KB**）。
- **SMEM 复用**：FC1 的 **FP8 64×64** 与 FC2 的 **BF16 64×32** 每 stage **都正好 4 KiB** → 覆盖在同一份 **WG-private ring** 上。

**Store path**
- **FC2 R2S + TMA store 两级流水**：每 WG 两个 **4 KiB SMEM buffer**。
- 当前 TMA S2G in flight 时，**下一个 subtile 的 R2S 写另一个 stage**。
- **Deferred drain**：保持一个 store group in flight，**只在 phase 边界 / kernel 尾部 / 需要可见性时**才 drain。
- **TMA store 只由 warp0 通过 `elect_one` 发出**；**空 tile 直接跳过**（empty tiles are skipped outright）。
- 图为 epi WG 的 store 时间轴：
  - `R2S subtile0 → stage0`、`subtile1 → stage1`、`subtile2 → stage0`、`subtile3 → stage1`（ring depth = 2）。
  - 下方 TMA 泳道：`TMA S2G stage0 (inflight)`、`stage1`、`stage0` 交替；`SMEM stage0 (4 KiB)` / `SMEM stage1 (4 KiB)`。
  - `producer_acquire` 只回收上一组的 store（`ring depth 2`），于是 **subtile i+1 的 R2S 与 subtile i 的 in-flight S2G 重叠**。
  - 图注强调 **FC1/FC2 share the same WG-private ring（both 4 KiB）**，以及 deferred drain 的三个 drain 时机。

---

## 页 25｜Optimization 5: All-Register Epilogue Fusion Chain

- 该页把 epilogue 做成一条**全寄存器融合链**，OCR 中可见的链路顺序为：

  `WGMMA accumulator (FP32)` → `gate/up register deinterleave (interleave=8 → acc layout, zero shuffle)` → `dequant (scalar multiply, read once per task tile)` → `SwiGLU (exp2 fastmath + rcp_approx)` → `[optional: absorb top-k weights]` → `requant (precomputed reciprocal, multiply instead of divide)` → `R2S (single pass through SMEM)` → `TMA bulk store` → `fc1_output`

- 逐环节要点：
  - **deinterleave**：`interleave=8` 与 acc layout 对齐 → **zero shuffle**（展开见下一页）；dequant 是 scalar multiply，**每 tile 只读一次**。
  - **SwiGLU**：用 `exp2 fastmath + rcp_approx` —— **no slow exp/division**。
  - **optional**：吸收 top-k 权重（**unlocks the atomic-add combine**）。
  - **requant**：**提前算好的 reciprocal，用乘法代替除法**，再 requant 到 FP8。
- **同时挂在这条链上的 blockwise 处理**：per-token **amax** 用 **register accumulation + `shuffle_sync_bfly` quad reduction**，**不做 SMEM reduction**。
- **register pressure 的代价**：**`M=128` tile 因 spilling 被禁用**；swapAB blockwise 改为 **chunked**；`per-t_shape` 折叠成编译期常量。
- 图为 accumulator（`RMEM (registers)`）向下流经 `dequant → SwiGLU → requant to FP8 → SMEM → R2S → GMEM → TMA bulk store` 的竖向管线，侧栏标 `exp2 fastmath + rcp_approx`、`multiply by a precomputed reciprocal`、`optional: absorb top-k weight`、`unlocks the atomic-add combine`。

---

## 页 26｜Why Gate/Up Interleave = 8: the WGMMA Register Layout

- 该页解释**为什么 gate/up interleave 必须取 8**，从 **Accumulator D fragment（m64nNk32）** 的寄存器排布出发：
  - **M 方向**：每个 warp owns **16 rows**；每个 thread 持有 **row r 与 row r+8**。
  - **N 方向**：寄存器按 **8 列一组**推进（**每 group 4 个 reg**）。
- **gate/up 在离线阶段按 8 交错**，两种布局都能**零 shuffle 折叠**：
  - **non-swapAB（沿 N）**：gate 在 `regs 8k..8k+3`，与之配对的 up 在 `8k+4..8k+7`。
  - **swapAB（沿 M）**：`row r = gate`，`row r+8 = up` → 对应 `regs 0/1 vs 2/3`。
- **为什么恰好是 8**：M 方向的行对间距恰好是 **8**（row-pair spacing）；**更小的粒度需要 shuffle，更大的粒度就要走 cross-warp SMEM**；因为 N 是 8 的倍数 → **8 是唯一可行的粒度**（8 is the only granularity），两种布局都能做到 **zero-SMEM folding**。
- 图为一张大表：行方向是 tile 行号（OCR 可辨 `2 4 6 7 8 10 11 12 13 14 15 ... N-8 N-7 N-6 N-5 N-4 N-3 N-2 N-1`，另有块头 `0 / 8 / 15 / 16 / 31 / 32 / 47 / 48 / 63`），单元格内是该行的 thread fragment 标签与它持有的元素对：
  - 前半段 block 的 fragment 为 `T0..T3`、`T4..T7`、`T28..T31` 等，元素对写作 `(d0,d1)`、`(d2,d3)`、`(d4,d5)`、`(d6,d7)`，N 方向更远的 group 写作 `(dx,dY)`（列索引符号 OCR 不清）**(?)**；
  - 后续 block 出现 `T32..T35`、`T60..T63`、`T64..T67`、`T92..T95`、`T124..T127` 等，行号跨度到 `63`，右下角标 `(tid % 128): fragments`。
  - 图意：同一 tile 内 thread 与寄存器的映射随 N 方向每 8 列移交给另一组 4 个线程，**行 r / r+8 落在同一线程**，因此 gate（r）与 up（r+8）天然成对，这是 interleave=8 能零 shuffle、零 SMEM 的直接原因。
- ⚠️ 该页 OCR 表格**严重残缺与错乱**（数字与 `T*` 标签大量串行、空单元格丢字），上表结构为按可辨读片段重建，**具体 fragment 编号不保证逐格正确** **(?)**。

---

## 页 27｜Optimization 6: A Single Active Dispatch Warp

- **active dispatch warp 默认为 1**（可配 `1 / 2 / 4`）：**4 个物理 warp 仍全部保留**，多余的跳过 dispatch，**只在 kernel tail 重新汇合**。
- **为什么更快**：`1 warp/SM`（约 **132 rows in flight**）**已经超过 NVLink bandwidth-delay product**；实测 **1 > 2 > 4 warps** —— 更深的 read queue 只会**拉长每一次 round trip**，并且**与 GEMM 抢 L2**。
- **Compact pull buffer**：SMEM slot 只按 active warp 分配，**每 CTA 省出 21 KiB** 还给 GEMM 的 A/B stages。
- 图为 `dispatch warpgroup (4 physical warps)` 的对比：
  - **after**：`warp0 — ACTIVE`，流程 `prep · barrier · pull-token-back`（`NVSHMEM, over NVLink`）→ `SMEM pull slot`（**1 row in flight**）→ `local token pool (GMEM)`；`warp1 / warp2 / warp3 — idle: skips dispatch, rejoins at kernel tail`。
  - **before**：`4 slots = 4 × hidden_bytes`；**after**：`1 slot`。
  - 回收量：`bulk load 3 × 7168 B = 21 KiB per CTA`，**returned to the GEMM AB stages**；另有 `bulk store` 与 `peer rank rows` 两条通路。
  - 图注（`4/EP8` 场景）：`1 > 2 > 4 warps` —— 每 GPU 约 **132 rows in flight** 已超过 NVLink BDP，更深的 queue 只是拉长每个 request 的 RTT，并和 GEMM 抢 L2 / issue slots。

---

## 页 28｜Optimization 7: Folding the Producer Warpgroup + Register Refit

- **整个 warpgroup（128 threads）消失**（folded away）。
- **Register refit**：一个 warpgroup 的 **4 个 warp 共享同一个 `setmaxnreg` 值** —— **producer 侧统一为 48**，**剩下的全给 epilogue：双 WG 时 224，单 WG 时 256**。
- **Effect**：
  - **two-WG cooperative 从此可行**；
  - **blockwise 512–32768 全部切换到 `M64N256`**，收益 **+11% … +30%**，**geomean +15.8%**。
- **对照**：在旧布局下同一个 tile **慢 14%** —— 结论是 **"the layout, not register tuning, makes the two-WG mode usable"**（是布局而非寄存器调参让双 WG 模式变得可用）。
- 图为 before / after 两条 warp 槽位条：
  - **before**：`epilogue/WGMMA WG ×1-2 | TMA-A | TMA-B | sched | idle | disp0 | disp1 | disp2 | disp3`，左侧另标 `producer warpgroup — 128 threads + registers`。
  - **after**：`epilogue/WGMMA WG ×1-2 | disp0 | TMA-A | TMA-B | sched`，标 **128 threads per CTA**，且 `dispatch warpgroup now hosts the producers` —— 原本占位的 producer WG 被折叠进 dispatch warpgroup 的空闲 warp。
  - 中间说明：`register cap = 65536 / threads rises` → **epilogue 拿到 224（two WGs）/ 256（one WG）**。
  - 图注重申：4 个 warp 共享一个 `setmaxnreg`，producer 侧统一 48、余额给 epilogue —— **这才是 `two-WG cooperative M64N256` 可行的原因**。

---

## 页 29｜Optimization 8: Early fc1_done Publish

- **做法**：FC1 tile 的 **TMA store 一落地**，就由**一个 epilogue 线程立刻用 release atomic add 发布 `fc1_done`**，而不是等到 **task boundary 再批量发布**。
- **two-WG cooperative 下的阈值**：每个 WG 各 **+1**，FC2 的等待阈值因此是 **×2** —— **不需要 cross-WG barrier**。
- **Why it is faster**：发布点前移 → FC2 tile 更早通过 readiness 检查、更早发出 TMA load → **FC1→FC2 依赖链变短**。
- **代价**：**no extra warp / registers** —— 这是 **Mega default path**，同时作为下一页 store offload 的 **fallback**。
- 图为 epilogue 的 per-tile 时间轴（`before` / `after` 两行）：
  - **before**：`R2S → TMA store → wait for next task → task-boundary barrier → batched publish fc1_done`。
  - **after**：`R2S → TMA store lands → release-publish fc1_done → wait for next task → task-boundary barrier`。
  - 图上标出两个不同的 `A FC2 tile unblocked here` 位置：after 行的解除阻塞点明显前移（早于 task-boundary barrier）。
  - 图注：一个 epilogue 线程在 store 之后立即做 **GPU-scope release atomic add**；双 WG cooperative 时每个 WG 各 +1、FC2 等待阈值翻倍，**no cross-WG barrier needed**。

---

## 页 30｜Optimization 9: Blockwise FC2 Dual-Accumulator Overlap

- **背景**：blockwise FC2 会把**每个 K tile 按 activation scale 切成两半**；**旧代码严格串行**，中间要 `fence → wait → FP32 promote → re-issue`，**tensor core 在这段时间空转**。
- **新代码**：额外分配**第二个 accumulator register fragment**，把两半的 WGMMA **背靠背发出**；读完 weight scale 后**只等第一半**，在**第二半仍在 tensor core 上跑的时候**完成第一半的 promote，然后再等第二半。
- **Gating 条件**：**accumulator 尺寸 ≤ 64 registers**，且满足 **（single-WG standalone kernel）** 或 **（folded layout 且 epilogue registers ≥ 224）** —— 依赖上一页的 **register refit**。
- **关闭时退化**：禁用后指令序列**与旧版本完全一致**（pure refactor）；**per-tensor 路径与 FC1 mainloop 不变**。
- 图为同一个 K tile 的 before / after 时间轴：
  - **before**：`WGMMA half A → wait → promote A (FP32 FMA) → WGMMA half B → wait → promote B (FP32 FMA)`，标注 **tensor cores idle during every wait + promote**。
  - **after**：`WGMMA half A → acc1`、`WGMMA half B → acc2`、`wait A only · promote A`、`wait B · promote B`，标注 **half B 仍在 tensor core 上跑时 A 已 promote**。
  - 图注：second accumulator register fragment；gated on `accumulator ≤ 64 regs` 且（single WG，或 folded layout 且 `≥ 224` epilogue regs）；禁用后指令序列与旧代码相同。

---

## 页 31｜Optimization 10: Scheduler Groups and the fc1_done Spin

- **调度方式**：scheduler **按 group 派发** —— 先发**一组 experts 的全部 FC1 tile**，再发它们的 FC2 tile；**默认 group = one wave**。
- **小 bucket 的问题**：此时每个 expert 只有 **1 个 token tile，但有 48 个 FC1 tile**；一个 group 只装得下 **1–3 个 expert**，于是 **FC2 tile 紧跟自己的 FC1 tile，而那些 FC1 还在跑**。
- **后果**：activation TMA producer **约 25% 的时间在 `fc1_done` 上空转 spin**（OCR 此处带一处不可辨标注 `(IKET)`）**(?)**。
- **解法**：**把 group 放大到 264 ≈ 6 experts** —— FC2 tile 到达时 `fc1_done` **已经完成**，**spin 消失**。
- ⚠️ **该页识别内容严重不足**：除上述要点外，图部分几乎全为乱码（OCR 原文如 `Gepechoner(onegrowp=allengensFCities,then hsinFC2 liles)-wall ocket...`，以及 `FCi mlee envetO(e) / FOM.e91 / F02.801 / FOA/EPO / FO2/S01` 等碎片），可推测是对比「one group = 所有 experts 的 FC1 tile，再是其 FC2 tile」前后 wall clock 的条形图，**具体轴标签与数值不可辨，不予臆测**。

---

## 页 32｜Optimization 11: 16-byte FC2 Output Stores

- **改造前**：FC2 的 **BF16 输出按 accumulator layout 逐对写出** —— 每个 lane 每个 subtile **8 × `STG.32`**（swapAB 为 **8 × `STG.16`**），**一次 warp-level store 只填半个 sector**。
- **non-swap 的改造**：在 quad 内做 **4×4 butterfly transpose（4 次 shuffle）** → 每个 lane 持有**某一行的 8 个连续列** → **一条 `STG.128`**；**cross-rank 直写的目的地查找从 8 次降到 2 次**。
- **swapAB 的改造**：accumulator 是 **channel-major**，改用**三级 lane-group transpose（6 次 shuffle + 6 次 `prmt`）**替代 7 条 STG；**仅 local-pool 路径**适用。
- **净效果**：**one warp-level store：8 half sectors → 16 full sectors**。
- 图为寄存器布局到 store 形态的变换（左右两栏）：
  - 左（before，`WGMMA accumulator layout, one row r`，**每 8 列组每 lane 持 2 个相邻 BF16**）：
    `lane0: c0c1 | c8c9 | c16c17 | c24c25`、`lane1: c2c3 | c10c11 | c18c19 | c26c27`、`lane2: c4c5 | c12c13 | c20c21 | c28c29`、`lane3: c6c7 | c14c15 | c22c23 | c30c31`，标注 **8 × `STG.32` per lane per subtile / half-sector writes**。
  - 中：`4×4 butterfly transpose — 4× shuffle (xor1, xor2)`。
  - 右（after）：`lane0: cols c0..c7 (16B)`、`lane1: cols c8..c15`、`lane2: cols c16..c23`、`lane3: cols c24..c31`，标注 **1 × `STG.128` per lane per row**。
  - 结论行：**after 每 lane 拿 8 个连续列 → 一条 16 字节 store；一个 warp 填满 16 个完整 32B sector，而不再是 8 个半 sector**；同时把 cross-rank 目的地查找从 **8 次降到 2 次/subtile**。
  - 页脚：swapAB（channel-major accumulator）走三级 lane-group transpose，`6 shuffle + 6 prmt → 1 STG.128`，**local-pool 路径专用**；store 原语**复用自 training-output（`generate_c`）路径，no new PTX**；**对齐依赖 hidden 是 8 的倍数**。

---

## 本段主题与脉络

这 16 页是 **MegaMoE kernel 的架构总述 + 十一条优化**（第 18–32 页），核心问题是：在 EP 并行的 MoE 推理里，如何让 **dispatch / FC1 / FC2 / combine** 全部挤进**一个 persistent kernel**，并让通信、GEMM、epilogue 三段互相重叠而不互相等待。脉络清晰：第 17–18 页先给总体架构与 warp specialization 分工表；第 19–20 页解决两个数值/形状前提——**swapAB** 让 token tile 从 64 降到 8（decode 工况不再浪费 padding），**blockwise FP8** 用 per-token×K128 / 128×128 / K64 的细粒度量化换取精度；第 21–24 页是流水线层面的四个优化：cooperative 双 WG 切 N、task-tile ping-pong 隐藏 epilogue latency、CGA + TMA multicast 砍半 L2/DRAM 流量、mainloop 与 store 双流水（228 KB SMEM 动态填满、4 KiB ring 复用）；第 25–26 页把 epilogue 做成全寄存器融合链，并解释 `interleave=8` 为何是寄存器布局决定的唯一粒度；第 27–28 页做减法——**只留 1 个 active dispatch warp** 省出 21 KiB，并**折叠 producer warpgroup + register refit（producer 48 / epi 224–256）**，这才使双 WG cooperative 的 `M64N256` 可行（blockwise 512–32768 全切，geomean +15.8%）；最后第 29–32 页收细节：`fc1_done` 提前 release 发布缩短 FC1→FC2 依赖链、blockwise 双 accumulator 消除 tensor core 空转、scheduler group 放大到 264 ≈ 6 experts 消掉 25% 的 spin、FC2 输出用 butterfly transpose 把 8×`STG.32` 合成一条 `STG.128`。整体是一条从**架构 → 形状/精度 → 流水线 → 寄存器预算 → 微指令**逐层下沉的优化链。
