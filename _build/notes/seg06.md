# 第 81–96 页 OCR 结构化摘要

> 来源：`_build\ocr\text\081_*.txt` ～ `096_*.txt`（课堂投影片手机翻拍照片的 OCR 文本）
> 说明：术语、缩写、模型名、内核名、硬件名、精度格式、数值与倍数均按 OCR 原样保留；粘连英文按语义拆分；`·` 统一视为项目符号/分隔符；不确定处在词末标 `(?)`；凡 OCR 未出现的内容不作补充。
> 页码范围：081–096 共 16 个文件全部存在，无缺页。

---

## 页 81｜Single AgentX Session Characteristics

- 页面分左右两张图，主题是**单个 AgentX 会话的特征**：左图"单步时延分解"，右图"ISL 增长曲线"。
- 左图（单步时延分解，堆叠柱状图）：
  - 纵轴为时延刻度：`100s`、`75s`、`50s`、`25s`；横轴为 `agent step →`，刻度 `20 30 40 50`。
  - 图注：**59 steps，主线程请求，无 subagent**。
  - 图例/分项文字：`tool / user gap（>60s）`(?)（OCR 作 `t顶60s`）、`prefill(TTFT)`、`decode`；柱内散落数值 `70g`、`120g`、`1808`、`1328`、`47h`、`61a`、`66a` 等，OCR 严重失真，**具体数值不可靠**(?)。
  - 图描述：每步时延被拆成 tool/用户思考间隔、prefill（TTFT）、decode 三段，其中 `tool / user gap（>60s）` 一段占比明显最大。
- 右图（ISL 增长曲线，累积输入 token，逐 query）：
  - 纵轴刻度 `50K / 100K / 150K / 200K`，**峰值 219K**；横轴为 query 序号，刻度 `10 20 30 40 50`。
  - 结论行：**ISL 从 448 单调增长到 219K，每步新增 p50 约 2K token**。
  - 关键事件标注：**第 42 步：间隔 46.7 小时后恢复**，并注明**代码上下文 KV 早已被逐出，187K 全量重算**。
  - 图描述：曲线严格单调上升，在第 42 步处因 46.7 小时的空档出现代价巨大的全量重算，是"长会话 + KV 逐出"问题的直接证据。

---

## 页 82｜3 Layer Software Stack of Agentic Inference

- 副标题：**Dynamo Agentic Inference-System Architecture** —— 三层软件栈总览图。
- **HARNESS LAYER / Layer 0**（接入层）：
  - 五个入口并排：`Claude Code`、`Codex`、`OpenCode`、`OpenCode`、`Your Agent`。
  - 对应说明：`Coding Agent (this tool)`、`OpenAI Coding Agent`、`Open Source Coding Agent`、`Open Source Coding Agent`、`Any agent that calls LLM API`。
  - 与下层接口：**HTTP API、`next.agent_hints`、`cache_control`**。
- **ORCHESTRATOR LAYER (Dynamo) / Layer 1**（编排层），三个组件：
  - **FRONTEND**：`Multi-protocol support`；`v1/chat`、`v1/responses`、`v1/messages`；`Block boundary awareness`(?)（OCR 作 `Blockboundary ereness`）。
  - **ROUTER**：`KV-Aware Placement`；**`FlashIndexer` 170M ops/s**；`BinaryHeap priority queue`；`ThompsonSampling routing`。
  - **KV CACHE MGR**：`4-tier memory hierarchy`；`Selective evict priority/TTL`；`Agent lifecycle awareness`；**`<think>` block auto-ephemeral**。
- **RUNTIME / Layer 2**（运行时层）：
  - 两个引擎：**`vLLM`**（`High throughput`）与 **`NVIDIA TRT-LLM`**（`Max performance`）。
  - 共性机制：`Priority eviction heap`、`KV Store (HiCache/KVBM)`、`TokenRangeRetentionConfig`、`GPU-CPU-Disk-RDMA SharedBlocks`。
  - `Priority max`(?)（OCR 作 `Priorityraax`，疑为 `Priority max`）。
- 图描述：自上而下的分层架构图，Layer 0 是各类 coding agent，经 `agent_hints`/`cache_control` 进入 Dynamo 的 Frontend→Router→KV Cache Mgr，最终落到 vLLM / TRT-LLM 两个 runtime；页脚为 `nVIDIA` logo。

---

## 页 83｜AgentX Dashboard

- 该页是 **AgentX 基准测试 Dashboard** 的界面截图（配置面板 + 散点/曲线图 + 长图例）。
- 配置区：
  - `BENCHMARK CONFIG` / `CHART CONFIG`；`MODE`、`X METRIC`、`Y METRIC`，带 `log x`、`log y` 开关。
  - 指标选项：`Output throughput (tok/s)`、`agent perf`(?)、`accuracy`、`Per-user speed p50 (tok/s/user)`。
  - 操作：`COMPARE HISTORY`、`Reset`、`Copy link`；筛选：`CONFIGURATION`、`RUN DATE`、`VALIDITY`，选项 `All` / `Latest per configuration and concurrency` / `Everything`。
  - 页签：`Performance`、`Trends`、`Capacity`、`Runs`。
- 坐标轴：横轴 **Per-user speed p50 (tok/s/user)**，刻度 `20 30 40 50 60 70 80`(?)（OCR 作 `BO`）；纵轴 **Output throughput (tok/s)**，刻度 `200 / 400 / 600 / 800`；每条曲线上的并发标号 `c22a80c4`(?) 中的 `c48`、`c64`、`c96` 等为并发档位。
- 图例中的被测配置（含 run id 与副本数），按 OCR 可辨识部分：
  - `unknown · mvp · aff (1)`、`unknown · official · aff (2)`
  - `SGLang direct · agg · 1xTP8 · radix` … `44c7ebac (2)`
  - `c96` / `c64` / `c48` 与 `c22a80c4 (2)`
  - **`Dynamo · agg · SGLang · 4xTP8 · HiCache L2 + Mooncake L3 · 1Mctx · bigKV pool`** … `3c53ab66 (2)`
  - `3c53ab66 · mvp · noaff (2)`、`3c53ab66 · official · aff (4)`
  - **`Dynamo · agg · SGLang · 4xDEP8 · HiCache L2 + Mooncake L3 · 1Mctx · bigKV pool`** … `d22a02Ba · official · aff (7)`(?)（run id OCR 不清）
  - **`Dynamo · disagg 2P2D · SGLang · 4xDEP8 · HiCache L2 + Mooncake L3 + rdma-rails · 1Mctx · bigKV pool`** … `213a5444 · official · aff (4)`、`092c10c0 · official · aff (2)`
- 图描述：多条"吞吐 vs 单用户速度"权衡曲线叠在同一张图上，从 `SGLang direct`、`Dynamo agg`（TP8/DEP8）到 `Dynamo disagg 2P2D` 逐步演进；图例长列表说明不同配置（`agg`/`disagg`、`aff`/`noaff`、HiCache L2 + Mooncake L3、`1Mctx`、`bigKV pool`）各跑一次并保留 run 副本。
- 图例文字渲染较小，部分 run id 与后缀数字 OCR 失真，标 `(?)`。

---

## 页 84｜Observability – Dynamo Provider Plugin

- 该页是 **Dynamo Provider Plugin 的可观测性（tracing）界面**截图，主体为多泳道的 trace 时间线。
- 顶部时间轴刻度：`00:02:30`、`00:03:00`、`00:03:10`、`00:04:00`（OCR 重复出现一轮，疑为标尺上下两行）。
- 点击/悬浮信息：`Workspace`(?)、`8.3`(?) 等字段值，OCR 不可辨。
- 泳道（每组一个 batch，括号内注明 `main thread`）：
  - `swebench_p18taskpl-batch-1780049… traj-astropy_astropy-693 (main thread)`
  - `swebench_p18taskpl-batch-1780049… traj-django_django-109 (main thread)`
  - `swebench_p18taskpl-batch-1780049… traj-astropy_astropy-774 (main thread)`
  - 另有多条同前缀泳道（`swebench_p18taskpl-batch-1780049…`），OCR 只保留了重复前缀。
  - 前缀 `swebench_p18taskpl` 疑为 `swebench_pl8task…`/`swebench_p8task…` 之类批次名，`p18` 具体写法不确定 **(?)**。
- 子 span 标签：大量 `tool:bash` 短块在同一泳道内首尾相接；`Category` 列显示 `tool`。
- 模型与 token 数：**`Qwen3.5-27B (2149 tok)`**(?)（OCR 作 `Qwan3.5-27B(21491ok)`）；一条 span 显示 `58s 344ms` 与 `299`、`10`(?) 等数值。
- 图描述：横轴为真实时钟的甘特式 trace，每条泳道对应一个 SWE-bench 任务的 trajectory 主线程，泳道内是一串以 `tool:bash` 为主的工具调用块，直观呈现"多 agent/多任务并行、工具调用密集"的形态，用于定位单次请求内部的耗时构成。
- 该页文字被界面元素的截图严重割裂，多数 span 名称与数值残缺，**该页识别内容不足**，以上仅为可辨识标签。

---

## 页 85｜How many tokens fit in 1 GB

- 主题：**1 GB 显存能装多少 KV token**，以 GLM-5.2 的实际配置为例。
- 配置行：**`GLM-5.2 · MLA + DSA · FP8 KV · 78 layers · 4 nodes / 32 GPUs`**。
- 单 token KV 占用：**`55.9 KB /token`**，分项为 **`MLA 43.9`** KB + **`DSA 9.8`** KB + `2.3` KB（第三项名称 OCR 未捕获；43.9+9.8+2.3≈56.0，与 55.9 吻合，推测为索引器/额外开销 **(?)**）。
- 容量表（列：`1GB` / `Per node · 8 GPUs` / `4 nodes`）：
  - **TP8 行**：`2.2K` / **`1.26M`** / `5.0M` token；标注 **`8x replicated`**、**`~33 sessions`**；旁注总量 **`577GB`**。
  - **DEP 行**：`17.9K` / **`7.6M`** / `30.6M` token；标注 **`no replication`**、**`~200 sessions`**（OCR 作 `~2o0`）；旁注总量 **`427GB`**。
- 图描述：以 55.9 KB/token 为单价，把 1GB → 单机 8 卡 → 4 节点 32 卡逐级放大成 token 容量；对比两条路线——**TP8 全卡 8 份复制**只有 ~33 会话容量，**DEP（无复制）**把容量提到 ~200 会话，token 容量差约 6 倍（1.26M vs 7.6M per node），这是后续所有 DEP 结论的前提。

---

## 页 86｜Goal 1: actual KV hit rate vs theoretical max

- 配置行：**`GLM-5.2 · AgentX replay · 4 nodes / 32 GPUs · DEP · concurrency 64/96/128`**。
- 三个指标定义：
  - `Ideal = reusable ÷ input`
  - `Actual = engine hits ÷ input`
  - **`Gap = recompute (capacity)`** —— 差距来自容量不足导致的重算。
- 柱状图（Ideal vs actual hit rate）：
  - 纵轴 `KV hit rate (%)`，刻度 `100 / 80 / 70 / 60`(?)（OCR 刻度零散）。
  - 横轴三档并发：`c64`、`c96`、`c128`；图例 `Ideal` / `Actual`。
  - 数值标签：`100`、**`96.3`**、**`96.2`**、**`95.8`**、**`91.9 (-3.9 pt)`**。
  - 读法：`c128` 档 ideal ≈95.8%、actual ≈91.9%，**差距 −3.9 pt**（即 `96.3→96.2→95.8` 与 `91.9` 的对应关系为推测 **(?)**）。
- 分层保留（retention）容量标注：**`DEP · G2/G1 retention = G2 = 37M`**(?)（OCR 作 `G22G1`）。
  - **G1 GPU · `53GB/rank`**：`30.6M` token（`1,710GB`）；`evict` ↔ `refill`。
  - **G2 Host · `512GB/node`**：`37M` token（`2,048GB`）；另有 `18M`（`1,024GB`）一档；`evict` ↔ `refill`。
- 关键归因（c128 档）：**`c128: spills past G2 → G3 (1 TiB)`**，**`holds 41 min of writes → L3 hit 1.2%`**，**`recompute 8.2% → −3.9 pt`**，**`TTFT p95 290 s`**。
- 图描述：三档并发下 actual 命中率随并发升高而下降（96.3→96.2→91.9），与 ideal 的缺口在 c128 达到 −3.9 pt；原因不是算法而是**容量**：c128 的工作集溢出 G2，G3（1 TiB）只能承接约 41 分钟的写入，L3 命中只有 1.2%，于是 8.2% 的输入需要重算，直接把 TTFT p95 推到 290 s。

---

## 页 87｜KV capacity for diff session cc

- 配置行：**`GLM-5.2 · AgentX workload · 4 nodes / 32 GPUs · DEP`**。
- 核心公式：**`KV to keep = sessions × context × headroom`**。
- 参数假设（retention moves to G3 in-flight）：`150K`（每会话上下文）· **`session peak ~300K`** · **`57KB/token`** · **`headroom 1.5x`** · **`router sees G1 + G3 only`**。
- 容量表（四列：会话并发 `Sessions cc` / `In flight (HBM)` / `KV to keep · 300K × 1.5` / `G2 host · per node`）：
  - 表头另有两列并列：`staging only`（in-flight / node）与 **`buffer_only · external linker · no host cache mode · today`**，以及 **`G3 pool holds KV to keep`**（`DRAM→L3 segment`）。
  - **cc=16**：`2.4M` / `7.2M` / `460GB`（`400GB`）/ ≈`35GB`(?) / `400GB`（另见 `135GB` 括号值）。
  - **cc=32**：`4.8M` / `14.4M` / `490GB`（`810GB`）/ ≈`70GB` / `810GB`。
  - **cc=64**：`6M`(?)（按 4.8M×2 应为 9.6M，OCR 疑缺位）/ `28.8M` / `550GB`（`1,610GB`）/ `135GB` / `1610GB`。
  - **cc=128**：`57.6M` / `650GB` / `270GB` / `3,230GB`（`3,230GB`）。
- 图描述：随会话并发翻倍，`KV to keep` 呈线性放大（7.2M → 14.4M → 28.8M → 57.6M token），而本机 G2 host DRAM 容量（`512GB/node`）增长跟不上，差额被迫下沉到 **G3 pool（DRAM→L3 segment）**，其需求量从 400GB 一路涨到 3,230GB；结论是"today"的 `buffer_only / no host cache` 模式在 ≥64 并发就装不下工作集。表内部分被 OCR 挤到同一行的数值与括号值归属不清，标 `(?)`。

---

## 页 88｜Goal 2: decode concurrency must keep up

- 配置行：**`GLM-5.2 · same AgentX load · 4 nodes / 32 GPUs`**；**X 轴 = set session concurrency (lanes)**；注：**in-flight counts requests, incl. subagents**（in-flight 计的是请求数，含 subagent）。
- 两种部署对照：
  - **左：TP8 – KV replicated on all 8 GPUs**：画了 8 个（4 组）`KV ×1` 方块，标注 `x1 x1 x1 x1`、`#2 #3 #4`(?)；容量 **`1.26M tokens/node`**；结论 **`ceiling 33 requests in flight`**。
  - **右：DEP (dp8 + ep8) · no replication**：16 个 `KV` 方块；容量 **`7.6M tokens/node (6x)`**；结论 **`scales to 100+ sessions`**。
- 两张折线图：
  - 左图纵轴 `Output throughput (tok/s)`，右图纵轴 `Requests in flight`；横轴均为 `set session concurrency (lanes)`，刻度 `c8`、`c16`、`c32`、`c64`、`c96`、`c128`（OCR 有 `c4B`、`c95`、`C4B` 等形近错字）。
  - 数值标签：`900`、`158`、`160`、`615`、`20`、`009`(?)、`53`、`24`、`101`，图例 `DEP (dp8+ep8)` / `TP8`、`DEP · requests in flight` / `TP8 · requests in flight`。
  - 结论行：`set sessions (1:1)`、**`TP8 ceiling ≈33`**。
- 图描述：TP8 因为 8 卡各持一份 KV 复制、单节点只有 1.26M token，请求在飞行数早早触到 **33** 的天花板，吞吐随之见顶；DEP 去掉复制后单节点 7.6M token（**6x**），in-flight 随并发线性上升并支撑 100+ 会话。即"**解码并发必须跟得上**"。

---

## 页 89｜Hard affinity mode DEP 下的负载均衡问题

- 配置行：**`AgentX · DEP dp8+ep8 · cc 64 · hard session affinity · 1 hour · 4 node 32 dp ranks`**。
- 主图：**`Device KV occupancy of the 32 dp ranks, one cell per minute (red = ≥90%, full)`** —— 32 个 dp rank × 每分钟一格的 occupancy 热力图。
  - 纵轴分组：`node`、`node2`、…、`ep ou`(?)（疑为 `ep0..`）；横轴 **`Minutes since the start of the measurement window (c64, 3600 s)`**，刻度 `20 30 40 50 60`。
  - 右上角统计：**`Minutes at ≥90%`**，标注 **`(of 61)`**。
  - 色带：`0%` → `30%` → `60%` → **`90% full`** → `100%`。
- 结论性注脚：**`KV aware routing for first round, then session affinity hard mode`**。
- 图描述：首轮用 KV-aware 路由把会话摊平，之后切到 hard 亲和（会话钉死在某个 dp rank），热力图随后出现明显**热点**——部分 rank 长期停在红色（≥90%，满），其余 rank 偏冷；`Minutes at ≥90% (of 61)` 用于量化"有多少分钟处于饱和"。这就是 **hard affinity 模式下的负载均衡问题**：亲和换来了 KV 命中，却牺牲了排队公平性与整体利用率。

---

## 页 90｜Goal 3: Agentic Routing Strategy

- 该页对比三种 **Agentic 路由策略**，左侧表格 + 右侧 Dynamo KV Router 流程图。
- 三列策略对比：
  - **KV-aware Router**：每轮独立打分，看全局；看的是**缓存前缀块 + in-flight 负载**。
  - **Hard Affinity**：首轮定终身，不看负载；看的是 **`X-Dynamo-Session-ID`**。
  - **Soft Affinity**：默认留原地，过载 `reroute` + `KVCR`；把绑定当**建议** + 过载值。
- 右侧流程图（Dynamo KV Router）三步机制，编号 ①②③：
  - **①** `route this turn: rank1 full → rank6`
  - **②** `hint: prefix is in rank1 host DRAM`
  - **③** **`NIXL peer-to-peer pull`**
- 图中元素标签：`GPU KV`、`bound session`、`soft → rank1`、**`KVCR host DRAM`**、`full` / `free`、**`deliver → GPU · prefill only the new tail`**、`free prefix copy`、**`G3 pool · one copy`**。
- 图描述：GPU KV 侧 rank1 已满、rank6 空闲，路由把本轮放到 rank6；通过 `X-Dynamo-Session-ID` 的 hint 得知前缀在 rank1 的 host DRAM，于是用 `NIXL` 做点对点拉取，**只对新增尾部做 prefill**，从而在"负载均衡"与"前缀复用"之间取得折中；`G3 pool · one copy` 说明跨 rank 共享时只需一份副本。

---

## 页 91｜Goal 4 – Clever Session Gateway – Thunder Agent

- 主题：**ThunderAgent**——一个"聪明的会话网关"，用 **program 状态机 + 全局控制回路**调度。
- 控制回路：**每 `Δt = 5s` 一个 tick，动作是 `resume → pause`**。
- KV 利用率门限（横轴示意 `0.80 / 0.85 / 0.95`）：
  - **`0.95` = pause 阈值**
  - **`0.85` = resume 上限（ceiling）**
  - **`0.80` = pause target**
  - 图中实测点：`97%`、`55%`。
- 会话状态机：`REASONING` ↔ `ACTING`（`ACTING 等 tool`）；`tool call 结果返回` 触发状态推进；状态迁移被标注为 **`step 未暂停`** 的边界条件（与页 92 的"只在 tool 边界迁移"一致）。
- 执行位置：`Worker1`、`Worker2`；暂停后 **`KV 已释放`**（OCR 作 `DKV已释放`），会话进入 **`全局等待队列（paused）`**。
- 调度优先级（OCR 残缺，按语义还原）：
  - **Resume**：`REASONING` 优先，其次是"占余量最大"者(?)（OCR 作 `装利余最大`）。
  - **Pause**：最小的 `ACTING` 优先；`worker` 侧同样参与选择。
  - **`ACTING` 计入 util 时权重 `2^(-t)`**，即 **等 tool 越久越先让位**（权重随时间衰减，等待久的 ACTING 最先被 pause）。
- 图描述：左侧是程序状态机，右侧是 KV util 曲线穿越 0.80/0.85/0.95 三条门限的示意，中间是多个 worker 与一个全局 paused 队列；核心思想是把"对话里等工具的时间"转化为可被撤销的 KV 占用。

---

## 页 92｜ThunderAgent · how it decides

- 决策规则总述：
  - **`one tick every 5 s`**；**`util = Σ of active programs ÷ GPU KV pool`**。
  - 每个 tick 做两类动作：`admit / resume`（进入）与 `pause`（退出）。
  - 三个门限：**`0.80 target`**、**`0.85 resume ceiling`**、**`0.95 pause`**。
- 打分与顺序：
  - **Pause order：`S = 1/c + 1{ACTING} · ACTING weight × 2^(-t)`** —— 以 `1/c`（上下文越小越该被牺牲）加上 ACTING 指示项，ACTING 项再乘时间衰减。
  - 选择逻辑：先 `waiting on a tool`，再 `smallest context → cheapest to recompute`。
  - Resume：`util < 0.85` 时触发，`S = 1/c + 1{REASONING}`；优先给 **`worker with most free KV`**。
  - 兜底：**`wait > 1800 s → forced resume`**。
- 状态机约束：**`State machine per program, transitions only at tool boundaries`** —— 每个 program 一台状态机，只在工具调用边界迁移。
- 示例（四个 program 的暂停顺序，`c` 为上下文大小）：
  - `P2 ACTING c=40K` → **第 1 个**被 pause
  - `P3 ACTING c=120K` → **第 2 个**
  - `C=30K` → **第 3 个**(?)（该条与 P4 的归属 OCR 串行，标 `(?)`）
  - `P4 REASONING`、`P1 REASONING c=180K` → **最后**被 pause（REASONING 受保护）
  - `util > 0.95` 触发 pause，`util < 0.85` 触发 resume，暂停者进入 `PAUSED`。
- 图描述：一组 program 在 REASONING / ACTING / PAUSED 之间沿 `tool call`→`tool returns` 的箭头迁移；示例中 ACTING 且上下文小的 program 先出队，上下文最大的 REASONING `P1`（`c=180K`）被留到最后，体现"重算代价最小者先让位"。

---

## 页 93｜Agentic Serving — ThunderAgent Benchmarks

- 测试设置：**`SWE-Bench Lite · GLM 5.2 · 8x NVIDIA Hopper GPUs · session concurrency = 32`**。
- 四张柱状图，指标（箭头为优劣方向）：
  - `TTFT p50 (ms) ↓`
  - `TPOT p50 (ms) ↓`
  - `gen 吞吐均值 (tok/s) ↑`
  - `e2e 均值 (s) ↓`
- 三组对照（图例）：**`B·TA`**（Baseline ThunderAgent(?)）、**`A·LRU`**、**`SLRU`**。
- 图上数值标签（OCR 顺序，未与柱子一一绑定）：`116.3`、`502`、`847`、`837`、`1866`、`112.5`、`1729`、`305`、`55.9`、`241`、`409`、`250`。
- 总结行（原文）：**`时延：e2e 均值 −51% · TTFT p50 −87% · TPOT 减半 | 吞吐：均值 ×1.6`**。
- 图描述：四联柱状图横排，每组三根柱（`B·TA` / `A·LRU` / `SLRU`）；随横轴从基线到 LRU/SLRU 再到 `B·TA`，三个时延指标一致下降、吞吐指标上升，右下角用一行结论给出 e2e −51%、TTFT p50 −87%、TPOT 减半、吞吐 ×1.6 的整体收益。

---

## 页 94｜ThunderAgent + KV offload

- 主题：**ThunderAgent 与 KV offload（分层缓存）的配合**，右侧为 program table，左侧为 G1/G2/G3 三层示意。
- 程序状态与所在层：
  - `A · decoding` / `A running` → **`G1 GPU`**（标注 **`G1 95%`**）；`resume → refill`
  - `D · idle, kept hot` → 仍留在 **G1**（`idle, kept hot`：空闲但保热）
  - `B · waiting tool` → **`G2 Host`**（`A copy`、`B copy`；`G2 60%`）
  - `C · offloaded` / `paused` → **`offloaded`**（`pause → cold → offloaded`）
  - **`G3 Pool`**：`A B C · one shared copy`
- 门限：**`pause when 95%`**；`admit while …`(?)（OCR 截断，未取到门限值）。
- 关键结论（原文）：**`TA never moves KV · it only changes who is cold · the tiers do the moving`** —— ThunderAgent 自己从不搬运 KV，只改变"谁变冷"，真正的搬运由分层缓存完成。
- 图描述：右侧 program table 逐行列出各 program 的 phase 与冷热；左侧三条水平层（`G1 GPU` 95% 占用、`G2 Host` 60% 占用、`G3 Pool` 单副本）标出 A/B/C 三份 KV 的落点，箭头表示 `pause → cold → offloaded` 与 `resume → refill` 的双向流动。

---

## 页 95｜ThunderAgent in RL rollout – Dynamo VeRL Integration

- 测试设置：**`Uni-Agent SWE-Bench · Qwen3-Coder-30B-A3B-Instruct · 8x NVIDIA Hopper GPUs · rollout-only`**。
- 折线图：纵轴吞吐（刻度 `500 / 1000 / 1500 / 2000 / 2500 / 3000`），横轴 **`Agent admission concurrency (cc)`**，刻度 `32 / 64 / 80 / 96 / 128 / 256 / 384 / 512`。
- 三条曲线（图例）：**`Default LB`**、**`Dynamo Python TA`**、**`Dynamo native Session Aware`**。
- 增益标注：**`+16.5%` VSTA**(?)、**`+6.8%`**（`VSTA` 三字 OCR 不清，标 `(?)`）。
- 图上文字：**`Default LB collapse.`** 与 **`high-concurrency regime`** —— 高并发区间基线发生塌陷。
- 结论行（原文，OCR 有粘连）：**`Dynamo SessionAware (TA based) can be leveraged in agentic RL rollout: throughput driven boost, tict / tpoi h limit`**(?)（后半段 `througnputdrivenbostticttpoihimit` 严重粘连，疑为 "throughput-driven boost, … limit"）。
- 交付与致谢：**`Deliver … with VeRL: github.com/verl-project/verl-recipe/tree/main/dynamo`**；参与人/联系人一行：`…ingyi Yang, Jinyan Chen, Aichen Feng, Yilin Hou etc.`（首个姓氏 OCR 残缺，疑为 `Jingyi Yang` **(?)**）。
- 图描述：三条吞吐曲线随 `cc` 增大而上升，`Default LB` 在中间并发段即出现"塌陷"（掉头下降），而 `Dynamo Python TA` 与 `Dynamo native Session Aware` 在高并发区间继续抬升，两条增量分别标 `+6.8%` 与 `+16.5%`；页码框为 `3264x2448`，为投影屏截取而非手机翻拍。

---

## 页 96｜Assets & Future Work

- **该页为收尾页**：分 `Assets`（已有产出）与 `Ongoing Works`（在研方向）两栏，并附 PR 与代码链接。
- **Assets — Docs**：
  - **Flash Indexer – Dynamo Digest**：`docs.nvidia.com/dynamo/digest/flash-indexer`
  - **ThunderAgent Program Scheduler – User Guide**：`docs.nvidia.com/dynamo/user-guides/agents/thunder-agent-program-scheduler`
- **Assets — PRs · ThunderAgent & SessionAware**：
  - **`#11447`** `feat(router): ThunderAgent admission strategy`
  - **`#11787`** `refactor(router): policy-class admission`
  - **`#11616`** `feat(admission): session-aware admission policy`
  - 汇总链接：`github.com/ai-dynamo/dynamo/pull/11447 · /11787 · /11616`
- **Assets — 代码仓库**：
  - `agent-plugins`：`…/ai-dynamo/agent-plugins/tree/main/pi-plugin`(?)（OCR 作 `gin-agent-plugins` / `pi-plugin`，路径片段残缺）
  - `verl-recipe`：`…/verl-project/verl-recipe/tree/main/dynamo`（另见 `/pull/126`(?) 片段）
- **Ongoing Works**（五个方向）：
  - **Simulation for Agentic Infra**：`simulate, tuning engine, scheduling and KV management before deploy` —— 部署前用仿真做引擎、调度与 KV 管理的调优。
  - **Enhance program aware routing** —— 增强 program 感知的路由。
  - **More advanced admission control**：**`ThunderAgent v2`**，`deal with moderate cc`（处理中等并发区间）。
  - **`Soft affinity mode + KVCR`**。
  - **`Programmatic KV block hints`（SGLang RFC `#27574`）etc.**：Dynamo router 下发 **`Share / Prefetch / Demote / Pin / Retain`** 等 soft hint。
- 该页为**总结/资源页（非致谢页）**，无数据图表。

---

## 本段主题与脉络

这 16 页是整场分享的**收束与验证段**，主题是"**Agentic 推理的系统级落地**"：把一套面向长会话 Agent 的推理栈（Dynamo 三层架构）从"能力清单"推进到"目标 + 实测 + 资源"的闭环。脉络很清晰：先由第 81 页单会话特征给出问题定义——ISL 从 448 单调涨到 219K、每步新增 p50 约 2K token，且 46.7 小时空档会导致 187K 全量重算；第 82–84 页铺出 Harness / Orchestrator（Frontend·Router·KV Cache Mgr）/ Runtime 三层栈与 Dashboard、trace 观测手段；第 85–87 页把"1 GB 装多少 token"算成 55.9 KB/token，对比 TP8 8 份复制（~33 会话）与 DEP 无复制（~200 会话），进而用 Goal 1 的命中率实验（c128 溢出 G2 落到 1 TiB 的 G3，L3 命中 1.2%、重算 8.2%、−3.9 pt、TTFT p95 290 s）证明瓶颈在**容量**。第 88–92 页依次立四个 Goal：解码并发要跟上（TP8 ceiling 33 vs DEP 6x 容量）、路由策略三选（KV-aware / Hard / Soft Affinity，含 NIXL 点对点拉取）、以及 ThunderAgent 以 5 s tick、0.80/0.85/0.95 门限和 S=1/c+1{ACTING}·2^(-t) 的换出打分做会话网关。第 93–95 页给出验证：SWE-Bench Lite 上 e2e −51%、TTFT p50 −87%、TPOT 减半、吞吐 ×1.6；RL rollout 高并发下 Default LB 塌陷而 SessionAware +16.5%。第 96 页以 Docs、三个 PR（#11447 / #11787 / #11616）与在研方向（ThunderAgent v2、soft affinity + KVCR、Programmatic KV block hints）收尾。
