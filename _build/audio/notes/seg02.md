# 第 17–32 页 逐页口头要点稿（录音 ASR × 投影片 OCR 对齐）

> 来源：`_build\audio\pages\017.txt` ～ `032.txt`（每页照片拍摄时刻起的录音片段）× `_build\notes\seg02.md`（同段的投影片 OCR 摘要）。
> 规则：只写录音里能推断出的内容；ASR 明显错译的词按上下文还原并在「ASR 存疑」里留痕；凡不能坐实处标 `(?)`。时间戳为该片段内的音频时间（`时:分:秒`）。

---

## 第 17 页｜Overall Architecture: One Kernel Does Everything

- **口头要点**
  - 讲者顺着数据流讲一遍整条链：FC1 算完把结果写到**本地 GMEM**（ASR 作"罗go my / 俄罗my"），随后给出**一个信号量**。
  - FC2 相关的 CTA 在该信号量上**等待**，等到之后把 FC1 的结果 load 出来，开始 FC2 的矩阵乘计算。
  - FC2 算完，在 **epilogue** 里调用 **combine** 相关逻辑，把数据**写回原始的（source）rank**。
  - 这一整块被设计成**一个 kernel**（ASR"噢新的科能"），内部用 **warp specialization**，不同 warpgroup 负责不同工作。
  - 最要紧的是 **epilogue 与它的 WGMMA 融合在同一组 warp 里**（ASR"IP服务 + 他们既然的aw"）。
  - 融合的理由讲者当场说了：WGMMA 最后计算的结果是**写在寄存器里**的，因此没法拆成独立的一组，所以整体上是融合的。
  - 一个 warpgroup 一般以 **4 个 warp 为一个单位**；实际使用中只有 **1–2 组** epilogue，且它们的**寄存器用量很大**。
- **口头补充（幻灯片上没有的）**
  - "为什么 epilogue 不能独立成一个 warpgroup"的因果解释：accumulator 落在寄存器 → 必须同一个 WG 内完成 WGMMA 与 epilogue，这是架构页上只画结构、不写理由的部分。
  - 部署经验值：实际只用 **1–2 组** epilogue WG（对应幻灯片 18 页的"×1-2"）。
- **ASR 存疑**
  - "罗go my / 俄罗my"≈local memory / GMEM；"漏得出来"≈load 出来；"抗办"≈combine；"科能"≈kernel；"司出来a选"≈warp specialization。
  - "IP服务"≈epilogue（warpgroup）(?)、"既然的aw"≈其 WGMMA(?)——按上下文定为 epilogue WG 与其 WGMMA。
  - 片段开头"啊融合进去，然后FC计算完以后"是被截断的前一句，本页真正的起点在上一段末尾。

---

## 第 18 页｜Warp Specialization

- **口头要点**
  - 先讲 epilogue 之外的分工：剩下的 warp 里 **TMA-A / TMA-B** 分别去 load **token** 与 **expert 的权重**。
  - **scheduler warp** 负责**任务的分配**；**dispatch warp** 负责去拉**远端 GPU 的数据**。
  - **token-back** 是**可选的**（ASR"中代理"）：可以单独给它 **4 个 warp** 专门做 push，也可以不开、把这些 warp 复用来做数据搬运。
  - 设计时要同时兼顾**训练场景与推理场景**，两者对（通用）GEMM 的用量差别很大。
  - 不做 swapAB 时，**M 维度一般放 expert / channel**；token 数较大（如大于 64）时一般能把 **WGMMA 打满**。
  - 推理场景 token 数很小，极端情况**只有 8 个 token**，而 **WGMMA 的 M 是 64 起步**的。
- **口头补充（幻灯片上没有的）**
  - "训练 vs 推理"这条设计约束是口头补的：同一份 warp 分工要覆盖两种迥异的工况。
  - token-back 的取舍说明：**单独 4 warp 专用** 或 **复用现有 warp**，两种都可。
- **ASR 存疑**
  - "4个w铺/沃克"≈warp；"派出网们"≈dispatch warps；"中代理"≈token-back(?)、"腐败 / 白"≈push(?)，语义按"可选、4 个 warp"定为 token-back。
  - "1~2组的o部"≈1–2 组 warpgroup；"6次"疑为 **64**(?)；"打出线开始后"疑为 MMA/WGMMA 指令(?)。
  - **对应关系错位**：本页窗口从 `[00:15:02]` 起，"训练/推理差异、M 是 64 起步"这段（`[00:16:02]`–`[00:16:41]`）讲的其实是**第 19 页 swapAB 的动机**，比照片早了一页。

---

## 第 19 页｜The swapAB Variant: the Cure for Small Token Counts

- **口头要点**
  - 承上：极端只有 8 个 token 时，**有 50 多个位置（约 56 行）根本没参与计算**，padding 浪费很严重 —— 这就是要换策略的原因。
  - swapAB 的原理：用 WGMMA 计算时 **M 维度必须是 64**，但 **N 维度只要是 8 的倍数**（8 / 16 / 32…）即可。
  - swapAB 之后 **M 放 channel、N 放 token**；token 数少时可调用 **N 较小的 MMA 指令**，整体计算效率得到提高。
  - MegaMoE 的 kernel 提供**两种量化方式**。其一是 **per-tensor**：与常见做法一致，activation 一个 scalar、**weight 每个 expert 单独一个 scale**，FC1/FC2 的 accumulation 都同样处理。
  - 另一种是 **DeepGEMM 式的 blockwise**：每个 expert 内按 **128×128** 的块做量化。
- **口头补充（幻灯片上没有的）**
  - 把 padding 的实际浪费量说成"50 多个位置没做计算"，是图上"56 of 64 wasted"的口头版。
  - 明确把两种量化方式**并列**讲（per-tensor 与 blockwise 都可选），而不是只讲 blockwise。
- **ASR 存疑**
  - "sab / swpab"≈swapAB；"开测后 / 开摄措施"≈WGMMA(?)；"托 / 圈了"≈token；"6次"疑为 64(?)。
  - "不探色 / 不探测"≈per-tensor；"d个GS"≈DeepGEMM；"一个MP3546"(?)、"1128×128"≈128×128。
  - 本页窗口（`[00:16:32]`–`[00:18:11]`）前半是第 19 页内容，后半 `[00:17:34]` 起已经在讲**第 20 页**的量化对照，照片滞后约一句。

---

## 第 20 页｜FP8 Quantization: per_tensor vs. blockwise

- **口头要点**
  - blockwise 下 **FC1 与 DeepGEMM 一样用 1×128**（per-token × K128）的块。
  - **FC2 没有采用 1×128**，而是 **1×64**。
  - 限制来自 FC1 的形状：FC1 的 tile 一般是 **64×128**，其中 **128 是 K 维度**。
  - 因为把 **SwiGLU** 融进了这一步，**做完 SwiGLU 后 128 的维度变成 64**，所以在该维度上做量化只能是 **1×64**。
  - 为什么不用 **1×256**（即 64×256 的 tile）：**寄存器压力**会比较大。
  - 为什么不拆成两个 64×128：那样**两个 warpgroup 之间需要一次同步操作**，会影响耗时。
  - 讲完量化转入 kernel 优化：**第一个优化 cooperative warpgroup** —— 用两组 warpgroup，第一组处理 **0–127** 的 token、第二组处理 **128–255**，两者**并行执行、结果互不影响**。
- **口头补充（幻灯片上没有的）**
  - 1×64 这个选择是**被 SwiGLU 折叠后的 K 维决定的**（滑片上只列三种粒度，不解释为什么选 K64）。
  - 两条被否掉的备选方案及其代价：**1×256 → 寄存器压力**；**两个 64×128 → 跨 WG 同步**。
- **ASR 存疑**
  - "MC1 / MCU / MC二"≈FC1 / FC2；"思维接入"≈SwiGLU；"方形/太l"≈tile。
  - "第三都是46 / 一个MP3546"疑为 **FP8**(?)；"fdv信的话"为本句起头的杂音(?)。"x那个0到第一百二十七个圈了"≈token 0–127。

---

## 第 21 页｜Optimization 1: Cooperative Warp-group Scheduling

- **口头要点**
  - 两个 warpgroup **同时、按序地**做 MMA；MMA 算完进入 **epilogue** 做 **SwiGLU / 量化 / store**。
  - 好处：**单个 warpgroup 发 MMA 时排布不满**，两组同时发射可以让 MMA 在 tensor core 上排得比较满。
  - 因此 **MMA 的耗时占比提升**，相应地 **epilogue 暴露出来的耗时占比减小**。
  - **第二个优化 ping-pong** 与 cooperative 比较相似，也是 CUTLASS 里比较典型的一种做法。
  - 区别在于依赖关系：cooperative 的两组**没有依赖**、时间上同时做 MMA；**ping-pong 强制**它们按某种依赖顺序推进 —— 第一个 WG 先做 MMA，做完进 epilogue，epilogue 做完再回去做 MMA。
- **口头补充（幻灯片上没有的）**
  - 把收益讲成"占比的此消彼长"（MMA 占比升、epilogue 暴露占比降），比滑片上的 trade-off 表述更直白。
- **ASR 存疑**
  - "iplg / iplog / IPL"≈epilogue；"ma / m后a / WMA"≈MMA / WGMMA；"顾客/我顾客/我本部的"≈warpgroup。
  - "叫做通通"疑为 **ping-pong** 的音译吞音(?)；"和vt有的上面at"疑为"和 CUTLASS 里的 pattern 比较相似"(?)。
  - "所以全服人啊还有n"一句不可辨(?)——按上下文当作"epilogue 里做 SwiGLU、量化、store"。

---

## 第 22 页｜Optimization 2: Task-tile Ping-pong

- **口头要点**
  - ping-pong 里**第二个 WG 的时间顺序与第一个正好相反**：第一个做 MMA 时第二个做 epilogue，第二个做 epilogue 时第一个做 MMA。
  - 效果是**把 epilogue 部分完全隐藏掉**。
  - 实际做优化时，**两种策略（cooperative / ping-pong）会按具体配置各跑一遍实测**，用实测性能来挑更好的那个。
  - 接着讲 **TMA multicast**：像 CUTLASS 里那样，两个 CTA **以一个 cluster 的形式同时执行**。
  - 具体例子：沿 **M 维度放两个 CTA**，第一个处理 **64 个（K）**、第二个处理**另外 64 个 K**，而**它们调用的 expert 可能是同一个**。
  - 做 TMA load 时两个 CTA 加载**不同的 tile、但相同的 expert 权重** —— 这正是可以多播的地方。
- **口头补充（幻灯片上没有的）**
  - 经验判断：cooperative 与 ping-pong **不预设谁更好，按配置实测择优**。
- **ASR 存疑**
  - "毛巾ps / 猫t卡 / ca"≈multicast；"艾特的权重"≈expert 权重；"64个头k"疑为 64 个 K 行/列(?)，按"各 64 个 K"理解。
  - "通通"再次出现，仍按 ping-pong 理解(?)；"探后"≈tile/tensor core(?)。
  - 本页窗口 `[00:22:00]` 起已经在讲**第 23 页**的 multicast，照片滞后。

---

## 第 23 页｜Optimization 3: Multi-CTA CGA + TMA Multicast

- **口头要点**
  - 有了 multicast，**CTA0 与 CTA1 不必各自重复 load 同一份权重，广播出来即可**。
  - 收益：**降低数据流量、降低整卡功耗、提升整体效率**。
  - 除了一个方向，也可以换另一个方向做多播（ASR"在电脑上"）：两个 CTA 做同样大小的量、但在**不同 expert 维度**上切分，此时可以多播 **activation**，让它们读同一份。
  - 转到 epilogue 写回：epilogue 做完 **SwiGLU 与量化**之后，**数据还在寄存器里**，必须写到 global memory 才能给后面的 FC2 或外部使用。
  - 写回有两条路：**直接 STG 写** —— 所有数据传输时间**完全暴露在 epilogue 里**；**或者做一个 pipeline 结构**（下一页展开）。
- **口头补充（幻灯片上没有的）**
  - 把 multicast 的收益链讲全：**省流量 → 降功耗 → 提效率**（滑片只写"L2/DRAM traffic halved"）。
  - 指出多播可作用在**两种 operand** 上（权重多播 / activation 多播），按切分方向不同而不同。
- **ASR 存疑**
  - "漏的"≈load；"头分 / 思头"≈channel 分片(?)；"第零个cta…60个头分"疑为 64(?)。
  - "在电脑上上去做p的"疑为"在另一个方向（列方向）上做"(?)；"做pass"≈multicast/broadcast(?)。
  - "IPO / IP"≈epilogue；"捐入"≈SwiGLU（与后文一致）；"ST机"≈STG。

---

## 第 24 页｜Optimization 4: Mainloop & Store Pipelines

- **口头要点**
  - pipeline 存储的做法：先把寄存器里的数据写到 **shared memory**，再由**另一个 warp 专门负责**把 SMEM 的数据用 TMA 写到 GMEM。
  - 把数据切成**一个个小片**：一部分继续做 寄存器→SMEM，另一部分并行做 SMEM→GMEM。
  - 这样 GMEM 方向的读写**可以被 寄存器↔SMEM 的读写掩盖掉**，降低 epilogue 写回耗时的暴露。
  - MegaMoE 里把 **SwiGLU 这一整块都 fuse 进 FC1**。
  - FC1 先做 MMA；因为 **gate 与 up 放在同一个 MMA 里算**，做完必须**拆开（deinterleave）**，然后做**反量化**（per-tensor 与 blockwise 两种）。
  - 反量化到 **FP32**、乘上量化 scale 之后，接下来就可以做 **SwiGLU**。
- **口头补充（幻灯片上没有的）**
  - 直接 STG 与 pipeline 两条路的**取舍结论**（前者把传输时间全暴露，后者能掩盖），是上一页没说完的补充。
- **ASR 存疑**
  - "拍卖的结构"≈pipeline(?)；"share业的 memory / 需要的my / 学m位 / 是有的m本r"≈shared memory；"我m / 罗go"≈global memory。
  - "例子和AP"≈gate 和 up；"不探索/不探色"≈per-tensor；"此微转入 / 活动"≈SwiGLU(?)、"量化一率"≈量化 scale；"卖票"≈MegaMoE(?)。
  - **对应范围缺失**：本时间窗（`[00:24:09]`–`[00:25:50]`）只讲 store path 与 epilogue 融合链，**听不到 mainloop 段落**（`k_pipe_mmas=1` 的 WGMMA 流水、TMA producer `try_acquire` peek、228 KB SMEM 动态填满、FC1/FC2 共用 4 KiB ring）的口头对应表述，可能这部分未被展开或落在相邻片段。

---

## 第 25 页｜Optimization 5: All-Register Epilogue Fusion Chain

- **口头要点**
  - SwiGLU 之后要看**是否需要吸收 top-k 的权重**：可以在这里直接乘掉，也可以留到最后单独 combine 的时候再乘。
  - 然后做 **FP8 量化**；量化完数据在寄存器里，用前面说的**两阶段方式**：先写 SMEM，再通过 TMA 写回 GMEM，供后面的 FC2 使用。
  - 特别强调 **gate 与 up 的 interleave 间隔**：它**取决于（该指令下）寄存器里数据的排布**。
  - 上面那张图在 **PTX 文档**里能查到，是 **M=64、N 为 8 的倍数**时的**寄存器排布**。
  - 图中红 / 蓝 / 绿框之间的**模式是重复的**；一般由 **4 个 warp** 分别负责计算，红、蓝、绿、紫各对应一个 warp。
  - 设计原则：**尽量避免 warp 之间的数据拷贝，以及一个 warp 内不同线程之间的数据交换**。
- **口头补充（幻灯片上没有的）**
  - 讲清图例怎么读：颜色框 = 不同 warp、图样重复；以及"这张图出自 PTX 文档"这条出处信息。
  - 给出 interleave 间隔的**判据是寄存器排布**（滑片只给结论 interleave=8）。
- **ASR 存疑**
  - "get和up p / I特利 / 一推特"≈gate/up 与 interleave；"偷的一个位置"≈top-k 的权重(?)；"客户k"≈combine(?)。
  - "tma特里面寄存器的数据的同步情况"疑为"该指令里寄存器的排布情况"(?)；"第零个现场/县城"≈线程(thread)。
  - 本页窗口 `[00:25:42]`–`[00:27:14]` 前半仍是第 24 页融合链的收尾，`[00:26:24]` 起才进入 interleave（即第 26 页内容）。

---

## 第 26 页｜Why Gate/Up Interleave = 8: the WGMMA Register Layout

- **口头要点**
  - 为什么必须避免数据交换：会牵涉**同步操作，影响性能**。
  - 红色框里一个 warp 内的数据排布是 **8 行 8 列**，右边蓝色框同样也是 **8 行 8 列**，**整个图样以 8×8 的形式重复**。
  - 所以做 gate / up 的 interleave，最好的方式就是**按这 8 行 8 列去排**。
  - 排完之后：**第 0 行第 0 列**的数据由**第 0 个线程**处理；**第 0 行第 8 列**（蓝色框最上面那个）**也是第 0 个线程**处理，只是落在**不同的寄存器**里。
  - 于是同一个线程**同时拿到 gate 和 up 的数据**，在**同一线程的不同寄存器里直接配对**就能计算，不需要 shuffle / SMEM。
  - 接着讲**第六个优化点**：EP 场景实测**只开 1 个 dispatch warp 就能打满带宽**；原设计 4 个太多，把另外 **3 个置为 idle**，只用 1 个，顺带把寄存器省出来。
- **口头补充（幻灯片上没有的）**
  - **实测结论**（1 个 dispatch warp 就够）来自实测，不是推导；以及"剩下 3 个 idle"的具体处理方式。
  - 早期的 warp 预算方案：一开始把**前 4 个或前 8 个 warp 留给 epilogue**，**后续 4 个**分别给 **TMA-A、TMA-B** 和**一个 scheduler**，另外还有**一个 idle 的 warp** 可以干别的事情 **(?)**。
- **ASR 存疑**
  - "沃克 / 县城 / 现场"≈warp / thread；"计术器 / 技术器"≈寄存器。
  - "只有一个例子开过了"中的"例子"≈warp(?)、"开过"≈kernel(?)，按"1 个 warp 即可打满带宽"理解；"HDM"疑为 **NVLink / HBM** 带宽(?)，与第 27 页 BDP 的说法更吻合。
  - "前4个或前8个是用做就是软件"疑为"用作 epilogue"(?)；"第六个优化点"之前的编号在本窗口内有过一次跳号（`[00:28:29]`）。
  - **对应关系错位**：本页照片（13:58:15）对应的窗口里，`[00:28:29]` 之后讲的已是**第 27 页 Optimization 6**；反过来说，第 26 页的 8×8 图样讲解实际发生在第 25 页照片的时间窗内。

---

## 第 27 页｜Optimization 6: A Single Active Dispatch Warp

- **口头要点**
  - 接着上一条：**4 个 dispatch warp 按实测结果优化成 1 个**，warp 数量**直接砍掉 4 个**。
  - 于是整个 kernel 就可以用 **8 个或 12 个 warp** 来做（可用 warp 预算变宽）。
- **口头补充（幻灯片上没有的）**
  - 砍掉的**绝对数量（4 个）**与由此得到的 warp 总数（8 或 12），是滑片上"1 / 2 / 4 可配"之外的口头账。
- **ASR 存疑**
  - "例子派出我"≈dispatch warp；"我们的数量"≈warp 数量(?)、"卧铺"≈warp。
  - "I豆的"≈idle。
  - **该页音频窗口极短**：照片 14:00:17 与下一页 14:00:37 只隔 20 秒，片段覆盖 `[00:29:05]`–`[00:29:36]` 约 28 秒，本条 optimization 的正文大多落在上一页窗口与缺口里，与照片严格对应的讲述量很少，**对应关系可能错位**。

---

## 第 28 页｜Optimization 7: Folding the Producer Warpgroup + Register Refit

- **口头要点**
  - 少 4 个 warp 的**最大好处是寄存器压力缓解很多**。
  - 对于较大的 tile（如 **64×128**），用原来的方式 **epilogue 没法开两组**去做（ping-pong / cooperative 都开不起来）**(?)**。
  - 把 dispatch 那 4 个 warp 省出来之后，就能**成功开启（双 WG 的）配置**，整体性能有一定提升 **(?)**。
  - **第八个优化点**（`fc1_done` 发布提前）：原顺序是 FC1 做完 epilogue → **R2S** → **TMA store** → **等 scheduler 分配下一个任务**（这里有一段空闲等待）→ 任务分到之后**才**去发布"FC1 已完成"的信号量。
- **口头补充（幻灯片上没有的）**
  - 把"折叠 producer WG"的收益落到**寄存器压力**上（而不是只报 geomean +15.8%）。
  - 明确指出旧布局下**大 tile 无法启用双 WG** 这一具体受限场景。
- **ASR 存疑**
  - "去开两桌户的去做平台或者靠微信"疑为"开两组 WG 去做 ping-pong 或者 cooperative"(?)；"和t和呃天空"不可辨(?)。
  - "第般个月发点"≈第八个优化点；"C一杠"≈`fc1_done`；"r图s"≈R2S；"TS"≈TMA store；"信号量的外"≈release/发布(?)。
  - 本页窗口 `[00:29:27]` 起的 Opt 6/7 收益描述与照片（14:00:37）大致同步，但 `[00:30:07]` 起已进入 Optimization 8（第 29 页内容）。

---

## 第 29 页｜Optimization 8: Early fc1_done Publish

- **口头要点**
  - 为什么要提前：一个 FC2 tile 的数据来自**很多个 FC1 的 tile**，只要**某一个 FC1 tile 发布晚了**，就会把整个 FC2 的开始时间往后推。
  - 所以希望**被依赖的 FC1 tile 一算完就立刻 arrive 这个信号量**，让下游的 FC2 尽早开始。
  - 具体改法就是把发布位置前移：**FC1 做完先 release 一次"FC1 已完成"，然后再去等下一个任务**。
  - **第九个优化点**：blockwise FC2 用**两组 accumulator**。
  - 先讲原来的 blockwise 内层流程：做 WGMMA（半边）→ **wait 这个 MMA** → 把寄存器数据取出来、乘上 **1×128 / 128×128** 对应的 scale → 放到**单独的 FP32 寄存器** → 再做 blockwise 特有的 **promotion**。
- **口头补充（幻灯片上没有的）**
  - FC1→FC2 的**多对一依赖关系**（一个 FC2 tile 吃多个 FC1 tile）是提前发布的真正动机，滑片只写"依赖链变短"。
- **ASR 存疑**
  - "wet"≈wait；"第三二的寄存器"疑为 **FP32** 寄存器(?)；"合模型"≈promotion(?)；"太l / 太度"≈tile。
  - "1×128或者128128"≈1×128 与 128×128（blockwise 的 activation / weight 粒度）。
  - 本页窗口 `[00:30:41]` 起讲 Opt 8，与照片（14:01:52）基本同步；`[00:31:39]` 起进入 Opt 9，属第 30 页内容。

---

## 第 30 页｜Optimization 9: Blockwise FC2 Dual-Accumulator Overlap

- **口头要点**
  - 这个 promotion 操作**与 WGMMA 不并行、完全顺序**，所以做 promotion 时 **tensor core 完全空闲在那里**。
  - 做完再进入**下一个 tile 的 MMA**，然后再 wait WGMMA，再做 promotion —— 结果是一部分 **promotion 的耗时被暴露出来**。
  - 改法：用**两组 acc（两组 WGMMA）**，让它们处理**不同的 N 维度**，从而**互相不依赖**；第一组发射完立刻发射第二组。
  - 然后先做第一组的 promotion —— 它**只等最前面那个 MMA，与第二个无关**，因此可以和第二个 MMA 的耗时重叠。
  - 于是做第一组 promotion 的时候，**第二组的 MMA 已经在执行**，整体性能提高。
  - 限制条件：两组 acc 会占更多寄存器；**开启条件是 N=64 时寄存器数量足够**才开。
- **口头补充（幻灯片上没有的）**
  - "tensor core 完全空闲"这一现象描述是口头给的。
  - 具体的**开启门限（N=64、寄存器够）**比滑片上"≤64 regs + single-WG 或 ≥224 epi regs"的说法更偏工况化。
- **ASR 存疑**
  - "广模式 / 和模型 / promot型"≈promotion；"探后 / 太阳的w推线"≈tile / MMA 序列(?)；"项目"疑为 SM/CTA(?)，第 31 页同处亦作此解。
  - "当它n等于4的时候"疑为 **N=64**(?)；"两组的这个 later"≈两组 accumulator(?)。

---

## 第 31 页｜Optimization 10: Scheduler Groups and the fc1_done Spin

- **口头要点**
  - **第十个优化点**：调度时 **group 的大小可以调**；MegaMoE 实际调度不是"所有 expert 的 FC1 全做完再统一做 FC2"。
  - 实际顺序是：**两个 expert 的 FC1 → 这两个 expert 的 FC2 → 再两个 expert 的 FC1 → 再它们的 FC2**，依次循环。
  - 所以要有一个"**一次塞进几个 expert**"的 group 大小来把控。
  - group 太小的问题：expert0 的 FC1 做完后 expert1 的 FC1 开始，但 **expert1 的 FC1 tile 很少**、很快做完，于是马上进入该 expert 的 FC2。
  - 此时**它的 FC1 可能还占着 SM 没做完**，于是这个 **FC2 的开始时间被拖后**。
  - 办法是把 **group 打得更大一点**，一次塞进更多 expert，让 FC2 的开始**往后推一些**；真正开始时已经有足够的 FC1 计算完。
  - 这个调整**要按实际的 expert 数量与 token 数量动态决定**。
  - **第十一个优化点**：epilogue 写回 global 有两条路 —— **先到 SMEM 再走 TMA**，或**直接从寄存器 STG 写回**；选哪条看具体配置。
- **口头补充（幻灯片上没有的）**
  - 把"spin 空转"的**成因讲成一条时间线**（小 expert 的 FC1 太快做完 → FC2 提前到场 → 依赖未就绪），而滑片只给 25% 这个数。
  - 明确 group 大小**没有唯一解，需按 expert 数与 token 数动态调**。
- **ASR 存疑**
  - "SP / xp / xper / XP"≈expert；"Google / 顾客性质的一个大小"疑为 **group 的大小**(?)；"微"疑为"次/轮"(?)、"头"疑为 token(?)、"ac"疑为 FC1 tile(?)、"项目"疑为 SM(?)、"驻留"可辨。
  - 该页窗口 `[00:34:37]`–`[00:36:44]`，**开头 34:22–34:38 有约 16 秒缺口**（第 30 页片段止于 34:19），Opt 10 的第一句（"不是所有 expert 的 FC1 做完…"）可能落在这个缺口里——本页首条要点部分依据缺口前的第 30 页尾部与后续描述推得 **(?)**。

---

## 第 32 页｜Optimization 11: 16-byte FC2 Output Stores

- **口头要点**
  - 直接 STG 写回的问题：每个线程拿到的元素**可能是不连续的**，比如第 1、第 8、第 9 个，写到 GMEM 只能发 **`STG.16`** 这种窄指令。
  - 更好的方法：用 **shuffle** 把不连续的数据**重新排成连续**，让一个线程去拿 0,1,2,…,8 这样连续的八个元素。
  - 这样就能调用**位宽更高的 `STG.128`** 写回 global，**指令数更少、运行效率更高**。
  - 最后看整体性能：**通信侧调用 NVIDIA 的（NVSHMEM）**，**compute 侧是 CUTLASS 的 FP8 实现** **(?)**。
  - 两张表分别对应 **per-tensor** 与 **blockwise**；token 数从最左端（8 起）一路增大，**加速比不断提升**。
  - token 数较小时加速比约 **3%**；token 数较大时，per-tensor 可以到 **24%**。
  - 为什么小 token 时加速比不高：**实测发现 token 数少时通信量小、计算量也小，计算侧基本不饱和**。
- **口头补充（幻灯片上没有的）**
  - 把 16 字节写回的价值讲成"**指令数更少**"（滑片讲的是 sector 填充率，两者是同一件事的两种说法）。
  - 给出 **3% / 24%** 两个端点数字，并**当场解释了小 token 端为什么涨不上去**（通信与计算都不饱和）——滑片没有这条归因。
- **ASR 存疑**
  - "销售"≈shuffle；"stg16 / ST及128"≈`STG.16` / `STG.128`；"县城"≈线程。
  - "e蔻的"疑为 NVSHMEM / NVIDIA 的通信库(?)、"包括a的和s"不可辨(?)；"卡拉斯的"≈CUTLASS；"非q的排名"疑为 FP8(?)；"QQ的个版本"疑为 DeepGEMM 的某个版本(?)、"橙色这条线"对应另一条对比线。
  - "后客的大概工艺"疑为"MegaMoE 的大概收益/性能"(?)；"从最下面最左边的8~37度8"中的上界不可辨，疑为 **32768**(?)；"加速比过高"按上下文应为"**不高**"。
  - 该片段 `[00:37:31]` 之后已转入**全片性能总结**（不属于本页滑片内容），第 32 页照片与讲述基本同步。

---

## 本段口头讲解的特点

张毅这一段是"照着数据流讲一遍、再逐条讲为什么这么改"的工程讲法：口语化、中英术语混读，习惯先报现象（"50 多个位置没计算""tensor core 完全空闲""等调度白等一段"）再给手段；每条优化都交代原做法、暴露的瓶颈、收益，并反复附加限制条件（寄存器够不够、N 是多少、一次塞几个 expert）。幻灯片没写而口头补上的主要是动机与踩坑：epilogue 必须与 WGMMA 融在同一 WG，是因为结果落在寄存器里拆不开；FC2 量化取 1×64 而非 1×256 或两个 64×128，是怕寄存器压力与跨 WG 同步；dispatch 只留 1 个是实测 1>2>4 而非推导；ping-pong 与 cooperative 要按配置各跑一遍择优；双 acc 的门限是 N=64 且寄存器够；group 大小要按 expert 数与 token 数动态调；小 token 端加速比只有 3%，是因为通信与计算都不饱和。
