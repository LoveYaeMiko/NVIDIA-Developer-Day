# 第 65–80 页 OCR 结构化摘要

> 来源：`_build\ocr\text\065_*.txt` ～ `080_*.txt`（课堂投影片手机翻拍照片的 OCR 文本），共 16 页，全部文件均存在，无缺失页。
> 说明：英文术语、缩写、模型名、硬件名、精度格式、数值与倍数均按 OCR 原样保留；粘连英文已按语义拆分；不确定处在词末标 `(?)`；OCR 未出现的内容一律不作补充。

---

## 页 65｜nvCOMP-ANS: Lossless KV Cache Transfer

- 主标题 **nvCOMP-ANS: Lossless KV Cache Transfer**；副标题：**GPU compression reduces data movement during offload and reload**（GPU 压缩减少 offload / reload 过程中的数据搬运）。
- 该页是一条三级存储搬运链的示意图，泳道标签自上而下为：
  - **GPU** → **CPU memory** → **SSD**
  - 搬运路径标注：**D2H/H2D**、**Write/read**
  - 搬运内容标注：**Raw KV**（**BF16/FP16/FP8**）、**Compressed KV Blocks**、**Compressed payload**
- 中间环节标注压缩组件：**nvCOMP ANS Compress/decompress**；元信息 **Per-chunk size metadata**；主机侧动作 **Host gather/scatter**；收益 **Fewer bytes per read/write**。
- 底部三栏为三项设计要点：
  - **Exact KV recovery** —— **Lossless entropy coding restores the original values**（无损熵编码还原原始值）。
  - **Overlapped execution** —— **Batched GPU codec with double-buffered transfers**（批处理 GPU 编解码 + 双缓冲传输）。
  - **FlexKV integration** —— 支持 **MHA/GQA/MLA/DSA**，以及 **TP/DP** 并行方式。
- 一句话总结：**Fewer bytes move between tiers. CPU and SSD retain fixed-size cache slots.**（层级之间搬运的字节更少；CPU 与 SSD 侧仍保留定长 cache slot。）
- 图描述：横向为 GPU→CPU→SSD 三级，纵向对比"未压缩原始 KV 字节流"与"压缩后的定长块"两条路径；GPU 侧只做无损熵编解码，CPU/SSD 侧看到的是定长的压缩块加每块 size metadata，因此读取写入的字节数下降，而 cache slot 尺寸不变。链接：`https://developer.nvidia.com/nvcom`。

---

## 页 66｜nvCOMP-ANS: Compression and Serving Results

- 主标题 **nvCOMP-ANS: Compression and Serving Results**；结论句：**TTFT gains are strongest at low concurrency in this benchmark**（在本 benchmark 中低并发时 TTFT 收益最明显）。
- **LOSSLESS COMPRESSION**（无损压缩率，原文字节 / 压缩后字节）：
  - **~1.4x**（对应 **BF16 KV cache**）
  - **~1.1x**（对应 **FP8 KV cache**）
- **TTFT speedup by concurrency (c)** 柱状图数值（各组从左到右为 **Mean TTFT** 与 **P90 TTFT**）：
  - **+18.7%**：柱高 **20.0%**、**16.9%**、**18.7%**
  - **+8.2%** mean TTFT speedup：柱高 **5.7%**、**8.2%**
  - **P90 TTFT speedup at c = 2**：柱高 **1.8%**、**4.2%**、**3.2%**、**3.0%**
  - 负向：**2.1%**、**-10.0%**、**-5.6%**（图上有负值柱，说明部分点变慢）
- 明确标注：**Throughput unchanged**（吞吐不变）。
- 图注/公式：**TTFT speedup = baseline latency / nvCOMP latency - 1**；**Bars show means**；**P50 (?) varies widely at c = 3 and 8**；**-1.9% to +2.4% across c = 1-8**（OCR 中的 `Pg0` 疑为分位数标记，标 **(?)**）。
- **E2E 配置**：**SGLang + FlexKV (CPU only)** / **GLM-5.1-FP8** / **BF16 KV** / **128K input** / **8x Hopper GPU**。
- 图描述：横轴为并发度（OCR 只保留到 `2` 与 `8` 两个刻度标签），纵轴为百分比变化；柱组按 Mean TTFT 与 P90 TTFT 分开，低并发（c = 2）处的正向柱最高（+18.7% / +8.2%），高并发出现负值，与"低并发收益最强"的结论一致。链接：`github.com/taco-project/FlexKV/pull/18a`(?)。

---

## 页 67｜Takeaways

- 该页为整段的收束页，三条要点：
  - **Where compression runs determines what improves** —— 压缩发生在哪一层，决定了什么指标能改善。
  - **Fused attention can reduce KV reads during decode.** —— 融合 attention 可以在 decode 阶段减少 KV 读取。
  - **Cache backends can extend cache residency and reduce transfers.** —— cache backend 可以延长缓存驻留时间并减少传输。
- **The methods delivered different gains in these benchmarks**（各方法在这些 benchmark 中带来的收益各不相同）：
  - **Optimized TurboQuant improved long-context decode**（优化后的 TurboQuant 改善长上下文 decode）；
  - **KVTC preserved throughput under memory pressure**（KVTC 在内存压力下保持吞吐）；
  - **nvCOMP-ANS reduced TTFT at low concurrency with exact KV recovery**（nvCOMP-ANS 在低并发下降低 TTFT，且保持 KV 精确还原）。
- **Choose by end-to-end results**（按端到端结果选型）：**Measure quality, TTFT, TPOT, throughput, and cache hit rate after codec and integration costs** —— 要把 codec 与集成成本算进去之后，再衡量质量、TTFT、TPOT、吞吐与 cache hit rate。
- 页脚残留 `nVID` / `env` 为 NVIDIA 标识残影，非正文。

---

## 页 68｜What Dynamo can do today

- 主标题 **What Dynamo can do today**；两列能力清单 + 一组社区数据：
- **All kinds of disaggregation**（各类分离式部署）：
  - **Prefill / decode disaggregation**；**Frontend / KV router** 与 **Agg / Disagg FT**
  - **Attention / FFN disaggregation (GPU/LPU)**（`LPU` 按 OCR 原样保留，**(?)**）
  - **Multimodal E/P/D pipeline**；**Wide-EP FT-NIXL elastic EP**
  - **KV-aware router and Flash Indexer**
- **Fault tolerance**（容错）：**Model Express and Snapshot**；**Planner**；**Online active scaling of P/D workers**
- **Global KV management**（全局 KV 管理）：**FlexKV / KVCR (?)**；**Multi-node distributed P2P KV reuse with router hints**
- **Grove – Find Most Ideal Worker**；**Digital twin of large-scale MaaS – high-fidelity projection**；**ai simulate**(?)
- **RL rollout acceleration** 与 **harness-based agentic inference**；**ThunderAgent、nvext agent hints, etc.**
- 底部社区数据：**~8.3K GitHub stars**、**244K+ pip installs**、**9,000+ pull requests**（OCR 只截到 `pull ro`/`pull r…`，按上下文复原，**(?)**）。
- 图描述：该页为"能力矩阵"式版面，左侧按 disaggregation 与容错/规划分类罗列，右侧是 KV 管理与社区代理类能力，底部三个数字为开源项目的采用度指标；OCR 未保留分区框线。

---

## 页 69｜KVRouter 在生产环境中被广泛验证 / FlashIndexer 是支撑准确路由的基石

- 主标题：**KVRouter 在生产环境中被广泛验证**；副标题：**FlashIndexer 是支撑准确路由的基石**。
- 两个客户案例卡片：
  - **Baseten**：**2X faster TTFT & 1.6X TPS with KV aware routing**（KV 感知路由带来 2 倍 TTFT 提速与 1.6 倍 TPS）。
  - **Meituan**：**2x faster TTFT & +20% more KV cache hit with KV routing**（OCR 作 `+2O%`，应为 **+20%**）。
- 两条参考链接：
  - `https://www.baseten.co/blog/how-baseten-achieved-2x-faster-inference-with-nvidia-dynamo/`（OCR 中 `b  ow-baseten` 为粘连断行）
  - `https://www.nvidia.com/en-us/on-demand/session/gtc26-s81943/`
- 该页为两张案例卡并排的版面，无图表数据；正文文字量少但语义完整。

---

## 页 70｜请求进入后，KV Router 用两类信号为 Worker 打分

- 主标题：**请求进入后，KV Router 用两类信号为 Worker 打分**；副标题：**缓存命中减少重复计算；实时负载防止缓存丰富的 Worker 过载**。
- 两条数据通路：
  - **请求路径**：**请求 Token** → **Block Hash** → **KV Indexer**（输出**缓存前缀命中**）→ **Slot Tracker**（输出**活跃的 Prefill + Decode**）→ **Cost Function**（**综合成本**）→ **最低成本 Worker**。
  - **缓存事件路径**：**推理 Worker** → **KV Events**（**缓存新增/删除**）→ 索引侧更新。
- 成本公式：**Cost = Prefill 成本 + Decode 成本 +（可选）活跃请求成本**。
- "为什么要两个信号？"一栏的结论：**缓存告诉我们"能省多少"，负载告诉我们"还能接多少"。**
- 图描述：左半为请求流（Token → Hash → Indexer → Tracker → Cost → 选中 Worker），右半为 Worker 反向推送 KV Events 的事件流；两条信号在 Cost Function 处汇合，一张是"命中深度"，一张是"当前排队/负载"，共同决定 worker 打分。OCR 中 `Slot T-acker`、`Prefll`、`Wor` 均为断行/错字，已复原。

---

## 页 71｜Flash Indexer 在链路里做什么

- 主标题：**Flash Indexer 在链路里做什么**；定位句：**它不生成 token，也不转发请求；它回答一个路由问题：哪里已经有缓存？**
- 四步链路：
  1. **请求输入**：**prompt blocks**，**block_hashes: h0 h1 h2 h3 ...**
  2. **实时缓存地图**：**Store/Remove events** 持续更新每个 worker 的 **cached prefix**
  3. **查询输出**：**Worker C: 4**、**Worker A: 2**、**Worker B: 0**（即各 worker 上可连续命中的 block 数）
  4. **Router 决策**：**优先选择缓存最长、负载合适的 worker**
- **为什么这很关键**（两栏）：
  - **查询慢，会拖慢路由**（OCR 断作"查询慢，会按…"，**(?)**）；
  - **状态旧，会错过可复用的 KV cache**。
- **Flash Indexer 的目标**：**在高并发读写下，仍然快速返回"谁命中最多"，让 prefix cache 真正参与生产路由。**
- 图描述：中间是"block_hash 列表 → 缓存地图 → 命中计数"的查询示意，输出侧给出三个 worker 的命中深度（4 / 2 / 0），Router 据此排序；图中不含时间或吞吐数值。

---

## 页 72｜索引里存的是一张"位置到 worker"的地图

- 主标题：**索引里存的是一张"位置到 worker"的地图**；副标题：**为了判断 prefix 是否连续，Flash Indexer 不能只看 block 内容，还要看它在第几个位置。**
- **请求被切成 blocks**，示意块序列为 **h5 h6 h7**。
- **每个 block 有两个信息**：
  - **position**：第几块
  - **block_hash**：内容指纹
- **key → value** 映射（图右侧）：
  - **(0, h0) → Worker A, C, D**
  - **(1, h1) → Worker A, C**
  - **(2, h2) → Worker C**
  - **(3, h3) → Worker C**
- **为什么要有 position**：**同一个 block_hash 可能在不同位置出现；只有位置也一致，才说明这段 prefix 真的连续。**
- 图描述：左侧是请求的 block 切分，右侧是 `(position, block_hash) → worker 集合` 的哈希表；示例中只有 **Worker C** 在 position 0–3 全部命中，因此是唯一能连续命中 4 块的 worker，A 只到 position 1，D 只到 position 0。

---

## 页 73｜GEN01/06 THROUGHPUT — 第一代：Naive Nested Dict

- 该页左侧是一条**版本演进阶梯**（Gen 1 → 6），右侧是每一代的定位/瓶颈说明；本页高亮第 1 代。
- **第一代性能**：**Naive Nested Dict — 385K block ops/s**。
- 演进阶梯上的节点（OCR 保留的名单）：**Nested Dict** → **RustActor（单队列保证顺序）** → **Inverted Index（按 block 反置到 worker）** → **Radix Tree（用树表达前缀）** → **Concurrent Radix（读并行，写保序）** → **Flash Indexer（按位置跳转 + Jump Search）**。
- **第一版的比喻与问题**：像一本按 worker 分册的账本——要找某个 prefix，只能先翻 W1、再翻 W2、再翻 W3；**每个请求都要逐个 worker 试一遍，看它的缓存能连续命中多深**。worker 越多、prompt 越长，查询越像"在全仓库逐柜翻找"。
- **为什么慢**：外层扫 worker，内层扫 prefix depth；**复杂度 O(W×D)**（页脚标注）。
- **为什么还不够准**：`local_hash` 只代表 block 内容；相同内容出现在不同位置时，可能被误认为 prefix 连续命中。因此引入 **Two hashes**：`local_hash`（内容）+ `sequence_hash`（上下文位置）。
- **这一代的价值**：它暴露了两个核心问题——**访问模式不对**（`access pattern`，OCR 作"访问椅式"，**(?)**），以及 **local_hash 碰撞需要 prefix context**。
- 图描述：右下为三本并列的"worker 缓存账本"（W1 / W2 / W3），每条账本按 `pos0 / pos1 / pos2 / pos3` 逐行对齐，标注 **match depth = 2**、**match depth = 1**、**match depth = 0**，说明必须逐个 worker 逐深度比对才能算出命中长度；`h3*` 标记提醒该位置存在内容相同但前缀位置不同的 block。

---

## 页 74｜GEN04/06 THROUGHPUT — 第四代：Radix Tree

- **第四代性能**：**Radix Tree — 4M block ops/s**。
- 核心思想：**把 prefix 变成树**。相同 block 内容只有在相同父前缀下才算同一路，**碰撞问题被上下文约束住**；**树的父子关系就是 prefix context**——同样的 `local_hash` 在不同父节点下是不同路径。
- 英文要点：**Radix Tree: prefix context scopes collisions**。
- **解决了什么**：碰撞不再只是 hash 层面的问题，而被放进"这段内容出现在什么前缀之后"的上下文里判断。
- **事件怎么处理**：**Store/Remove 事件用 `sequence_hash` 快速定位节点；query 则沿 `local_hash` 子节点往下走** —— 页脚英文总结为 **dual-key design: local_hash for traversal, seq_hash for events**。
- **还没解决什么**：树本身更正确，但**仍然在单线程 actor 之后**，读写并发能力还没释放出来。
- 图描述：一棵 `root → h1 → h2 → h3…` 的 radix 树，左侧标注 **event lookup（seq_hash → node）** 与 **prefix traversal（沿 local_hash 下行）** 两条不同路径；图下方标出 **W1, W2 / W3 / W4** 与 **`seq_hash`**，表示多个 worker 的同一前缀在树中共享节点。页脚有"新版节点更慢：先讲 3 个背景，再讲 6 代优化。空格播放/暂停，←/→切换"——这是视频播放器 UI 残留，非投影片内容（页 75 同）。

---

## 页 75｜GEN06/06 THROUGHPUT — 第六代：Positional Indexer + Jump Search

- **第六代性能**：**Positional Indexer + Jump Search — 170M block ops/s**。
- 核心思想：**不再沿树一层层走，而是按 position 随机访问，并用 checkpoint 跳过大片共享前缀**。
- **跳过的判据**：**如果第 0、64、128 个 block 都还匹配，就不必检查中间每一个 block** —— 英文标注 **all active workers still match → skip the whole interval**，遇到不匹配则 **lookback** 回扫那一小段找掉队位置。
- **为什么更快**：**`index[position][local_hash]` 可以直接查某个深度，不需要从 root 一路走到那个深度**；查询成本 **O(D/J + W)**（D 为深度、J 为 jump size、W 为 worker 数）。
- **碰撞怎么处理**：**大多数 slot 是 Single，直接命中；只有出现 Multi 碰撞时，才 lazy 计算 `sequence_hash` 消歧**。
- 关键标签：**position -> local_hash -> SeqEntry**；数据结构与技巧：**Vec、DashMap、SeqEntry::Single、SeqEntry::Multi、lazy seq_hash、jump search**。
- 图描述：底部是一条按 checkpoint 刻度排布的横向轴，刻度为 **64、128、192、256、320、384、448、512、576、640**；命中段的整体向前跳跃，落单处标注 **lookback**。页脚英文：**checkpoints instead of pointer hops; collision path stays lazy**。
- 页面底部仍有播放器 UI 残留文字（"暂停 / 空格播放/暂停"），非投影片内容。

---

## 页 76｜性能数据（Achieved vs. Offered Throughput）

- 主标题：**性能数据**；图标题 **ACHIEVED VS. OFFERED THROUGHPUT (HIGHER IS BETTER)**（实测吞吐 vs 提供负载，越高越好）。
- 图中出现的系列与数值点：**Naive**（**385K**）、**v0.1 Radix**(?)、**Radix Tree**（**4M**）、**Concurrent Radix Tree**、**Nested Map**；**Flash Indexer / 提升** 标注 **170M**，并给出 **440x / 42x** 两个倍数。
- 图上方另见 **810K**、**5.0M** 等刻度/点位数值（与图例对应关系 OCR 不清，**(?)**）。
- **Benchmark setup**（基准配置）：
  - **24-core Arrow Lake 285K desktop**
  - **Mooncake FAST'25 trace + mock engine**（OCR 作 `MooncakeFAsT'25`）
  - **16,384 GPU blocks, prefix caching enabled**
  - **24 concurrent event-processing threads**
- 横轴为 **Offered Throughput (block ops/s)**，纵轴上界标为 **50M / 200M**，x 轴刻度 OCR 部分残损（可见 `100K / 200K / 500K / 1M / 2M / 5M / 20M / 100M / 200M / 500M / 1.0G / 2.0G` 一类量级标签，个别字符不可辨，**(?)**）。
- 结论句：**Flash Indexer 的价值不只在"知道缓存在哪里"，还在"这个查询足够快"，足以支撑大规模请求。**
- 图描述：多条曲线在"提供吞吐"升高后先后出现拐点并掉头向下（达到饱和），曲线越靠右说明能承受的负载越大；OCR 可辨认的定量信息是末端点 **170M** 与相对提升 **440x / 42x**，其余曲线形状的细节数字未识别出来。

---

## 页 77｜Standalone KV Indexer: 定位

- 主标题：**Standalone KV Indexer: 定位**；一句话定义：**把 KV cache 的索引能力从 router / frontend 里拆出来，变成可独立查询的服务。**
- 三栏对照（**它是什么 / 它不是什么 / 适合什么时候用**）：
  - **它是什么**
    - 独立维护 **cached KV blocks** 的索引
    - 订阅 worker 的 **KV cache 变化事件**
    - 通过查询接口返回 **prefix overlap**
  - **它不是什么**
    - 不是 **standalone router**
    - 不做最终 **worker selection**
    - 不维护完整 **request lifecycle**
  - **适合什么时候用**
    - 调试 router 看到的 **KV state**
    - 外部系统做 **custom routing**
    - 观察不同 **worker / tier** 的 **cache 分布**
- 该页为三列文字卡版式，无图表与数值；内容完整可读。

---

## 页 78｜Standalone KV Indexer: 架构

- 主标题：**Standalone KV Indexer: 架构**；总纲：**ZMQ 事件面负责 ingest，HTTP 请求面负责注册、查询和观测。**
- 三类 API（图中右侧清单）：
  - **管理类 API**：`GET /health`、`POST /register` 与 `POST /unregister`、`GET /workers`
  - **查询类 API**：`POST /query`、`POST /query_by_hash`
  - **恢复类 API**：`GET /dump`、`POST /register_peer` / `POST /deregister_peer`、`GET /peers`
- 数据流：**Worker 1 / Worker 2** 各自通过 **ZMQ PUB** 推送 **KV events** → Indexer 侧 **ZMQ SUB Listeners** 接收 → 写入 **Worker Registry** 与索引 **`(model, tenant) -> Radix Tree`** → 对外由 **HTTP API** 提供查询。
- 查询返回：**查询结果按 map 返回，并可拆分 gpu / cpu / disk tier**（OCR 作"按 mato 返回"，**(?)**）。
- 图描述：左侧是两个 Worker 的 ZMQ PUB 出口，中间是 Standalone Indexer 内部的两层（事件面 ZMQ SUB Listeners、索引面按 `(model, tenant)` 分树的 Radix Tree 与 Worker Registry），右侧是 HTTP API 暴露的管理/查询/恢复端点；图中无性能数值。

---

## 页 79｜SLAs of New Agentic Era

- 主标题 **SLAs of New Agentic Era**；整页是 **Traditional Inference → Agentic Inference** 的指标对照表：
  | Traditional Inference | Agentic Inference |
  |---|---|
  | **TTFT – Time to First Token** | **Trajectory E2E latency** |
  | **TPOT – Time per Output Token** | **Time to First Answer Token** |
  | **Request E2E latency** | **System throughput** |
  | **满足 SLA 的千卡 QPS** | **AA-AgentPerf: SLO 下最大并发 agent 数** |
  | — | **Global KV cache hit rate > 90%** |
  | **以单次请求为中心** | **HiCache / FlexKV、P2P KV reuse** |
  | **API price** | **SLA 下并发 session 成本** |
- 核心结论：**单次请求指标 → trajectory / session 级系统 SLA**。
- 该页为双列对照表（无柱线图），OCR 完整；表中"—"为 OCR 未给出对应项的格子。

---

## 页 80｜AgentX Trace

- 主标题 **AgentX Trace**；顶部三个关键数字：**393**、**98,827**、**1M**。
- 其中：**393 真实会话（Claude Code 轨迹）**、**98,827 请求数**、**原生上下文窗口 1,048,576**、**trace 请求 p99 近 900K**。
- **主线程请求输入长度分布（按请求数占比）**：
  - **< 32K：2%**
  - **32K–128K：21%**
  - **128K–256K：27%**
  - **256K–512K：30%**
  - **> 512K：20%**
- **pareto curve**（帕累托曲线）：纵/横为 **每 GPU tok/s** 与 **TTFT p90**，即"吞吐 vs 交互性"的权衡曲线。
- 实验方法标签：**真实会话**、**固定 seed**、**官方 harness 回放**、**每 lane 10 条**、**393 任务**、**25–75% 处切入**、**N lane**、**-1 小时 warmup 预热**。
- 图描述：上方是输入长度分布的堆叠条（`< 32K` 仅占 2%，主体集中在 32K–512K，`> 512K` 仍占 20%），下方/右侧是吞吐与 TTFT p90 的帕累托曲线，用于在固定真实 trace 上比较"要吞吐还是要交互性"；OCR 未给出曲线上的具体坐标数值。

---

## 本段主题与脉络

本段从 KV 压缩收口，转向路由与索引，最后把评价尺度抬到服务层。65–67 页收束 nvCOMP-ANS：GPU 侧熵编码把 KV 压成定长块搬运，BF16 约 1.4x、FP8 约 1.1x，低并发 TTFT 最高 +18.7%、均值 +8.2%，吞吐不变。68 页给出 Dynamo 能力全景，把 KV 路由与索引列为基座；69–72 页以 Baseten 2x TTFT、美团 +20% 命中证明其生产价值，并说明必须同时看 block_hash 与 position 才能判断前缀连续。73–76 页为六代演进：385K → 4M（Radix Tree 用 context 约束碰撞）→ 170M（Jump Search，O(D/J+W)），累计 440x/42x。77–78 页拆出 Standalone 索引服务，79–80 页说明为何要换轨到 trajectory / session 级 SLA。
