# 模块 4 · OpenShell 安全机制（OpenShell / 现代 CLI / 深入探索）

> 本摘要仅依据 `_extract/lessons/04a-OpenShell.md`、`_extract/lessons/04b-现代-CLI.md`、`_extract/helpers-API.md` 三份已提取文本；04c 页面文件缺失，见对应小节。

## 04a OpenShell 沙盒

- **一句话主旨**：OpenShell 用生效中的策略及其强制执行机制，把智能体进程可用的权限限制在文件、网络目标与操作系统操作三条边界之内。
- **解决的问题**：模块 3 中文件提供持久上下文、定时任务启动无人值守的工作，这些操作的效果取决于智能体进程实际拥有的权限；本页回答“这些权限由谁、在哪一层、以什么机制被削减和拦截”，并要求学习者不满足于“提示词写得对”。
- **关键概念**：
  - 防御层 —— 三个层级各回答不同问题：提示词塑造意图（规则告诉模型应如何行事，但模型仍可能被对抗性检索内容、恶意工具输出或循环中其它智能体欺骗，且智能体仍保留运行时授予的全部权限）；智能体工具框架验证请求（OpenClaw 或 Hermes 在请求到达操作系统前拒绝不受支持的 shell 形式、被禁止的工具调用或格式错误的参数，但属应用逻辑，可能配置错误、版本过时或被入侵）；沙盒限制操作结果（OpenShell 仅授予策略允许的权限，即使前两层都未拦住，操作系统仍可在文件、网络或进程操作完成前拒绝）。
  - 最小权限 —— Saltzer 和 Schroeder 提出的原则：每个组件只获得完成其工作所需的权限；该原则早于智能体出现，因此可自然套用到当前场景。
  - 边界而非意图 —— 由 Rice 定理推出：对任意程序的非平凡行为无法通用判定，因此对具备代码执行能力的智能体应检测运行内容周围的边界，而不能假定静态检查能证明未来每项操作都安全。
  - 网络策略 —— 网络命名空间（netns）给智能体隔离的网络栈，初始出站访问关闭，HTTPCONNECT 代理是唯一出站路径，Open Policy Agent（OPA）依据策略检查“发起请求的二进制文件、主机、端口和路径”；策略编辑者决定允许哪些连接，默认拒绝意味着除非策略明确允许，两个方向都不开放。
  - 文件系统边界 / Landlock —— Landlock 是允许非特权进程限制自身未来访问权限的 Linux 安全模块，此处把新的文件操作限制在策略授予的路径内（工作区目录树）；它是强制执行机制，但仍需考虑兼容模式、OverlayFS、绑定挂载、符号链接竞态，以及施加限制前已打开的句柄。
  - 系统调用边界 / seccomp —— seccomp 是 Linux 的系统调用过滤机制，其 BPF 过滤器按允许列表检查每项请求，被拒调用在操作执行前返回 EPERM（“操作不允许”）；本课本地运行时排除了 ptrace、mount、setuid 等危险的底层操作。
  - 进程身份 —— 智能体以非 root 进程、无特权的 sandbox 用户（非零 UID）运行，因此攻击成功时初始权限较少；较低初始权限缩小影响范围，但不证明权限提升不可能，主机、容器配置和系统调用策略仍是安全边界的一部分（涉及 capability 如 CAP_SYS_ADMIN、CAP_SETUID）。
  - 控制平面 —— 位于沙盒之上、由 operator token 平面管理的一层：用 operator.admin 范围调用角色设定、计划任务、会话、模型和配置的读取方法；读取成功不代表获准写入。
  - 沙箱拦不住的风险 —— 不可信输入 + 私有数据 + 外部通信构成的“致命三要素”：策略可正确允许某个出站 API 入口，但该入口是全双工的，网络允许列表批准的是目标地址，而不是获准连接中所传字节的含义。
- **四个可测试问题**（原文列出的 1–4 条）：
  1. 此进程可以连接到哪里？—— 由 netns + CONNECT 代理 + OPA 依据二进制文件、主机、端口、路径作答。
  2. 它可以访问哪些文件？—— 由 Landlock 把新文件操作限制在策略授予的路径内。
  3. 它可以请求哪些内核操作？—— 由 seccomp 的 BPF 允许列表在请求执行前返回 EPERM。
  4. 它最初拥有多大权限？—— 以非 root 的 sandbox 用户运行，初始权限较少但不等于无提权风险。
- **核心机制/步骤**：
  - 页面九步主线：1 各防御层在何处介入 → 2 沙盒机制如何回答可测试的问题 → 3 先调整运行时 → 4 检查命令结果 → 5 进一步探索：完整轨迹 → 6 读取可启动环境的实时策略，然后以地图形式查看 → 7 比较策略预测与实际请求 → 8 沙箱之上：控制平面 → 9 沙箱无法拦截的风险。
  - 三种产品角色：OpenClaw 是智能体框架（决定用哪个工具、尝试做什么）；OpenShell 是安全运行时（限制可访问的文件与网络目标、可执行的操作系统操作）；NemoClaw 是参考技术栈，把前两者与生命周期命令、策略预设、推理指南及部署默认配置封装在一起。OpenShell 与具体智能体无关，同一道边界可封装 OpenClaw、Hermes、LangChain deepagents 等。
  - 先调整运行时（与 Kickstart 使用同一运行时、同一个 OpenClaw 智能体）：🩺 健康检查（检查环境状态、toolSearch、卡住的审批和一条简单命令，HEALTHY 表示无需修复，DEGRADED 指出接下来检查什么）；🛠 恢复（仅当实时配置启用 `tools.toolSearch` 时才将其禁用，默认不清除会话、不重启）；📜 运行时日志（持续读取网关/智能体日志 `logs.tail`，含模型调用、工具分派、错误和卡顿；网关本身不公开推理过程）。
  - 检查命令结果：一次一个命令，检查输出、退出状态与是否完成；失败可能来自策略、缺少软件、无效请求或服务本身；初始目录从访问开放互联网一直到改写智能体自身人设，探测会清理临时文件、列出 `SOUL.md` 而不修改它、丢弃读取的环境内容。
  - 完整轨迹：智能体可为一个目标规划多个命令，需比较每个命令的输出与退出状态；一旦允许执行的命令打印出秘密，秘密已进入输出通道，后续网络拒绝无法撤回先前泄露。
  - 读实时策略：通过 operator 终端调用 `helpers.policyGet()`（内部执行 `openshell policy get <agent> --full` 并解析 YAML 正文），显示状态与解析后的 YAML；地图用同一策略评估候选目标地址，切换发起调用的可执行文件即可看到授权差异，`View policy source` 显示规则来源 YAML。琥珀色区域位于检查点上方，代表出站规则完全无法感知的权限提升轴。
  - 比较预测与实际：🧮 预测（静态，在浏览器中，用浏览器评估器按可执行文件身份、目标地址、端口、方法和路径给出判定）；🛂 确认（实时，在沙盒中，用 `openshell sandbox exec` 执行选中的 `curl` 请求，如 `list available models · /usr/bin/curl → inference.local:443 GET /v1/models`）；✅ 两者一致吗？（不一致时检查请求、已生效策略、响应来源与评估器假设；HTTP 错误可能来自代理或目标应用，先确认错误来源）。
  - 控制平面：🔌 以 operator.admin 身份连接（用现有网关令牌请求 `operator.admin` 并检查是否被接受）；🗝️ 调查访问范围（调用角色设定、计划任务、会话、模型、配置的读取方法并记录结果，未测试写入；该单元不发送编辑请求，但连接和读取仍可能产生日志）。
  - 相关 helpers 函数：`helpers.policyGet()`、`helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?)`、`helpers.evalSandboxFs(path, mode, policy?)`、`helpers.sandboxExec(command, {agent})`、`helpers.mountPolicyMap(target, opts?)`。
  - 策略输入字段（出站）：二进制文件（可执行文件标识）、主机、端口、路径；另有 HTTP 方法。
- **沙箱拦不住的风险 / 按故障模式选择控制措施**：
  - 读取检查不能证明写入权限；有害流程可以组合各自获准的读取操作与对外通道。
  - 致命三要素三要素定义：私有数据（智能体可读但不该泄露的内容：工作区文件、电子邮件、token、记忆或内部记录）；不可信输入（非操作员编写、但模型可能视为指令的外部内容：网页、议题、文档、工具结果或对等智能体的响应）；外部通信（任何能传出字节的路径：HTTP、拉取请求、聊天、日志行、图像加载，甚至用户可能点击的链接）。
  - 六类需按实际配置评估的失败模式：角色设定遭篡改（智能体能否改 `SOUL.md`，检查所有权与写入权限）；控制平面权限（令牌范围与服务器配置决定可用管理方法）；输入注入（获准通道可能传送恶意指令，网络限制不能证明输入可信）；通过获准通道外泄（策略只能证明通道被允许，不能判断字节是否无害）；隐藏意图（单独获准的动作可组合成有害工作流）；维护同伴（智能体对同伴的判定可能随社交语境改变）。
  - 故障模式 → 控制措施对照表（沙箱发挥的作用 / 仍需在沙箱上层实施的控制）：目标劫持或提示词注入 → 限制模型被操纵后可访问的文件、进程和目标地址 / 输入来源追踪、后果重大操作的审批、行为评测；工具滥用 → 限制工具运行时可用的 OS 和网络范围 / 逐工具授权、参数验证、速率限制、不可逆调用的确认机制；身份或权限滥用 → 以非 root 启动并阻断特定提权路径 / 工作负载专用身份、最小化 token 作用域、较短有效期、轮换和审计；供应链攻击或意外代码执行 → 减少已安装代码可访问的文件、系统调用和出站通道 / 固定并验证依赖项、安装策略和完整性监控；记忆或上下文污染 → 策略把指定文件设为只读时可保护这些文件 / 写入来源追踪、可审查历史记录、信任标签、从已知良好状态恢复。
  - 这些类别与 OWASP Top 10 for Agentic Applications 一致；应按此表选择策略执行点，不要要求单一层识别所有危害。
  - 参考资料所列（本页版）：Simon Willison《The lethal trifecta》(2025)、Greshake et al. (2023)《Not what you've signed up for》、Saltzer & Schroeder (1975)、seccomp 过滤器与 Landlock、Open Policy Agent、NeMo Guardrails、OWASP 智能体式应用 Top 10；并注明“完整列表请参阅深入探索 · 参考资料”。
- **承上启下**：上承模块 3c「持续运行」——持久上下文与无人值守运行使权限问题变得具体；本页把关注点从 OpenClaw 的行为转到 NemoClaw 在外围构建的 OpenShell 策略边界，并通过“读策略 → 预测 → 用 `openshell sandbox exec` 确认 → 对比”的训练建立“证据而非直觉”的方法；下接模块 4b「现代 CLI」，在那里比较各智能体应用的默认设置与自由度差异（原文页脚：`← 模块 3c：持续运行` / `模块 4b：现代 CLI →`）。

## 04b 现代 CLI 智能体

- **一句话主旨**：现代 CLI 智能体共用同一个“模型在循环中用工具”的结构，安全特征取决于各自默认开放哪些能力、是否启用无人值守执行，以及底层运行时能否拦截不当调用。
- **解决的问题**：模块 4a 已区分应用层决策与操作系统层强制执行；应用封装位于这条边界之上。本页在构建自己的浏览器端 CLI 智能体之前，先比较这些封装的默认设置，并说明“自由度”本身就是攻击面。
- **关键概念**：
  - 相同循环，不同应用默认设置 —— 所有比较对象都封装了同一组能力：一个工作目录、一组工具、一套记忆、可选的无人值守运行方式（cron、长时间任务或队列作业）、网络访问；差异在默认设置与内置能力，这些成本与便利性合称“框架负担”。
  - 各产品默认设置差异 —— Claude Code 使用 `CLAUDE.md` 指令，工具规则、权限模式和沙箱设置决定哪些操作可执行或需要批准；Codex CLI 使用 `AGENTS.md` 指令，沙箱设置限制访问范围、批准策略控制审查，工作区内的编辑和命令可在这些限制内自动执行；Cursor 使用 `.cursor/rules/*.mdc`，工作区编辑通常无需批准、终端命令默认需要批准，模式和设置可能改变这些检查；Hermes 提供技能、持久记忆、计划任务及经过配置的消息集成，批准模式与终端后端决定命令的处理和隔离方式；OpenClaw 使用 `SOUL.md`、`AGENTS.md` 等工作区文件、网关会话与定时触发器，本课程中它在 OpenShell 内运行，需检查生效策略与网关权限来评估可及范围。
  - 自由度就是攻击面 —— 六个可授予/不授予的维度：文件系统（哪些路径可读或可写）、网络出站访问（按二进制文件分别限定主机、端口及 HTTP 方法/路径）、进程身份（智能体以哪个用户运行）、二进制文件身份（哪个可执行文件可使用授权）、持久化（cron、技能和 `SOUL.md` 人设）、推理路由（模型调用通过哪个端点发出）；NemoClaw 参考配置分别给出：仅可写 `/tmp`、`/sandbox/.openclaw`、`/sandbox/.nemoclaw` 与工作目录、系统路径只读，由 Landlock（`best_effort`）强制执行；网络默认拒绝且只留一个简短允许列表（NVIDIA 推理、`inference.local`、clawhub/npm），每项限定一种 HTTP 形式并绑定特定二进制文件；以非 root 用户 `sandbox` 运行并由 seccomp 阻止 `ptrace`、`mount`、`setuid`；二进制身份通过可执行文件路径、沿父进程链向上检查、首次使用时信任的哈希值解析，`argv[0]` 可被伪造因此不受信任；持久化由工作区权限与主机管理的文件保护决定；推理经托管 `inference.local` 网关路由，Privacy Router 依据 operator 的策略（而非智能体的策略）决定哪些上下文可以传出。
  - 浏览器 shell CLI —— 浏览器智能体有一个在本页执行 JavaScript 的 `js` 工具，可在浏览器权限内读取 DOM、调用 `fetch`、使用课程辅助函数；停止会取消模型请求并阻止后续工具调用，但无法中断已在执行的同步 JavaScript，也无法撤销已完成的操作。
  - 本地宿主 shell —— NemoClaw 本地运行时通过模块 4a 策略探测所用的同一条 `/ws/terminal` 连接提供真实宿主 shell，宿主提供 `openshell` CLI（管理沙箱化智能体的 operator 工具），输入每一行都在本地运行时上执行、输出由它直接返回；每条命令在各自的短生命周期 shell 中运行，因此交互式对话要用面板而不是 `openclaw tui`。
  - 操作员平面 vs 智能体平面 —— 上方终端属于操作员平面：主机 Shell 管理沙箱中的智能体，通过 `agent <cmd>` 发送的命令在智能体环境内执行，主机命令则使用操作员权限；这两个边界都要按模块 4a 的方法检查。
- **章节清单（原文 1–6 条）**：
  1. 相同的循环，不同的应用默认设置。
  2. 自由度就是攻击面。
  3. 动手试试 · 在不同智能体框架间权衡同一项任务。
  4. 构建一个以此浏览器为 shell 的 CLI 智能体。
  5. 在本地运行时上打开真实 shell。
  6. 与智能体对话。
- **核心机制/步骤**：
  - 框架对比练习：从三个维度比较复杂度——智能体框架隐藏的抽象（代码更少但了解更少）、内置的假设和默认设置（在你提出要求前框架会介入到什么程度）、开箱即用的一等功能（对照需要自行实现的同等能力）；可编辑单元公开其系统提示词与响应逻辑，编辑后重新运行即可重建交互页面，并标注每份附件是“完整 README”还是“课程编写的说明”。
  - 浏览器端 CLI 智能体：为已挂载的智能体设定目标，先观察其 JavaScript 工具调用，再打开实现代码修改工具边界、循环上限或最终答案规则；原文指出模块 4c 将回到这种浏览器形式，交互式 Web 界面中的状态和控件清晰可见且可在其他宿主环境复用，而身份验证、存储、网络访问和工具适配器取决于宿主环境。
  - 本地真实 shell：先在模块 3a 连接本地运行时；`openshell sandbox list` 显示智能体、`openshell status` 报告网关状态；命令前加 `agent` 让其在沙箱内运行——`agent ls` 会通过 `openshell sandbox exec` 列出智能体的文件；`openclaw tui` 是交互式全屏界面，单次运行终端无法让它持续打开。
  - 与智能体对话：面板通过 OpenClaw 网关与同一个实时智能体通信，使用 `/cli/gateway` 连接（模块 3b、3c 也用这条连接），流式显示回复并展示智能体运行的每项工具或命令；需先在模块 3a 连接（及其 URL 和 token）。
  - 出现的命令与标识符：`openshell`、`openshell sandbox list`、`openshell status`、`openshell sandbox exec`、`agent <cmd>`、`agent ls`、`openclaw tui`、`/ws/terminal`、`/cli/gateway`、`SOUL.md`、`AGENTS.md`、`CLAUDE.md`、`.cursor/rules/*.mdc`、`inference.local`、`Privacy Router`、Landlock `best_effort`、`argv[0]`。
  - 与框架差异配套的三种外来集成：OpenShell 可承载这类智能体应用，NemoClaw 是本课程使用的参考栈；NVIDIA 还记录了 Codex、Cursor 和 OpenCode 的相同 OpenShell 集成方式——所选 CLI 决定初始默认设置，其外层 OpenShell 封装控制这些默认设置获准触达的范围。
- **风险与选择（原文末尾三条要点）**：
  - 设置——此运行时已配置，独立的 CLI 需要另外安装和配置。
  - 可及范围——文件、网络和进程权限取决于环境，请检查实际授予的权限。
  - 影响范围——提示注入可能通过获准的能力造成伤害，请比较可用的操作、限制的执行情况及审计证据。
  - 另需注意：停止按钮不能中断已在执行的同步 JavaScript，也不能撤销已完成的操作；无人值守执行方式（cron、长任务、队列作业）会把这一风险窗口放大。
- **承上启下**：上承 04a 的“应用层决策 vs 操作系统层强制执行”——本页讨论的是边界之上的应用封装，并用自由度表把 04a 的策略与命令证据对齐；下接模块 4c「深入探索」（原文页脚 `模块 4c：深入探索 →`，正文亦称“模块 4c 将回到这种浏览器形式”）。

## 04c 深入探索（缺页说明）

- **缺失项（明确标注）**：04c 的网页正文文件缺失——`_extract/lessons/` 下只有 `04a-OpenShell.md`、`04b-现代-CLI.md`，没有 04c 的 Markdown；归档目录 `智能体\` 中也没有 `深入探索 · 安全智能体.html`，只保留了资源目录 `深入探索 · 安全智能体_files\`（内含 codemirror/highlight 等代码单元依赖、`_style.css`、`_dli_activity_diagnostics.css`、`nemo-retriever-diagram-1920x1080.jpg`、`opengraph-image.jpg`）。因此本课时无法按原文结构做摘要，以下仅为**其它页面可推断**的内容，不含对正文的还原。
- **可推断的信息（均注明出处）**：
  - 该课时存在且是模块 4 的第 3 页：课程主页写“模块 4 · 约 1 小时 · 3 个页面 OpenShell 安全机制 · 现代 CLI · 深入探索”，页面按钮为“4a OpenShell · 4b 现代 CLI · 4c 进阶探索”，即 04c 的标题在主页作“进阶探索”、在页脚/导航作“深入探索”。
  - 它的 URL/文件名是 `04c-going-further.html`，`_links.json` 中该链接的标题为“深入探索 Brev · NIMs · Blueprints”，提示该页主题涉及 Brev、NIMs 与 Blueprints 等深入路径（此为该链接标题，不是正文内容）。
  - 它包含一个 `#refs` 锚点：01a–04b 共十个课时页的“参考资料”小节都写“完整列表请参阅深入探索 · 参考资料”，链接指向 `04c-going-further.html#refs`。可推断 04c 承担全课程统一参考文献表（原文各页只列本页几条，完整清单集中在此）。
  - 04b 正文称“模块 4c 将回到这种浏览器形式”，可推断 04c 仍以可启动的浏览器实验单元为主（与它保留的 codemirror/highlight 资源目录一致）。
  - 04a 的琥珀色“权限提升轴”、`helpers.mountPolicyMap` 的信任边界图、以及 helpers 表中的 `mountFigures`/`openFigureLightbox` 等图表辅助函数，提示深入探索页可能延伸讨论沙箱之上的控制与可视化——但这属于间接线索，**未在缺页正文中得到确认**。
- **建议**：如需补全，应重新抓取 `04c-going-further.html`（含 `#refs` 段）；当前归档仅可用于引用上述“指向 04c 的存在性证据”。

## 课程辅助函数 API 概览

原文（`_extract/helpers-API.md`）共 16 个分组、68 个条目（`helpers.signal`、`state` 等非函数成员也计入条目）。原文没有名为“其它”的分组，下表按任务要求把“课程内容”及其后的 6 组归入“其它”。

| 分组 | 条目数 | 备注 |
|---|---|---|
| 共享状态 | 2 | `state`、`helpers.randomId(prefix?)` |
| 模型调用 | 3 | `chat`、`chatStream`、`browserChatFetch` |
| 模型配置 | 7 | `getConfig`、`getEmbeddingConfig`、`getKey`、`getModelApiBaseUrl`、`setModelApiBaseUrl`、`isDefaultModelApiBaseUrl`、`mountModelEndpointProbe` |
| Web 搜索 | 3 | `webSearch`、`instantAnswer`、`formatSearchResults` |
| 嵌入与相似度 | 2 | `embed`、`cosineSim` |
| token 与上下文 | 2 | `contextWindow`、`estimateTokens` |
| 原始 HTTP | 2 | `fetch`、`fetchRetry` |
| 可启动实例终端 | 3 | `terminal`、`courseShell`、`courseRead` |
| OpenShell 策略 | 5 | `evalSandboxNetwork`、`evalSandboxFs`、`sandboxExec`、`policyGet`、`mountPolicyMap` |
| 其它 · 课程内容 | 5 | `coursePage`、`coursePages`、`mountFigures`、`openFigureLightbox`、`wireFigureZoom` |
| 其它 · 交互页面 | 5 | `mountChatUI`、`mountAgentChat`、`mountConsole`、`mountOpenClawCli`、`mountKeyPanel` |
| 其它 · 图表字符串 | 2 | `diagramSVG`、`ganttBarsSVG` |
| 其它 · OpenClaw 网关 | 14 | `openclawBootstrapRequest`、`openclawChat`、`courseTurn`、`openclawLoopbackProbe`、`openclawGatewayWsUrl`、`runOpenClawConnectionAudit`、`redactOpenClawDiagnostic`、`refreshOpenClawGatewayToken`、`getOpenClawConnection`、`setOpenClawConnection`、`filterOpenClawRuntimeNoise`、`filterOpenClawRuntimeValue`、`openclawMessageText`、`openclawResultText` |
| 其它 · 运行控制 | 2 | `helpers.signal`、`helpers.delay(ms)` |
| 其它 · 追踪与日志 | 2 | `helpers.trace(name, attrs)`、`helpers.log(...args)` |
| 其它 · 可视化 `helpers.viz.*` | 9 | `diagram`、`lineChart`、`scoreBarChart`、`messageList`、`ganttBars`、`retrievalBars`、`diffTable`、`chat`、`sideBySide` |

合计：9 个具名组共 29 条，“其它”7 组共 39 条，总计 68 条。（原文说明：该表由全部 11 个课时的“辅助函数”面板汇总去重而成，课时间内容一致。）

**10 个最关键的辅助函数**：

1. `helpers.policyGet(agent?)` —— 读取可启动实例的实时 OpenShell 策略（内部运行 `openshell policy get <agent> --full` 并解析 YAML），返回 `{ agent, command, raw, status, policy, parseError }`，是 04a“先读策略再解释结果”的入口。
2. `helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?)` —— 静态评估候选连接与网络策略，返回 `{action, matched, reason}` 且不发网络请求，默认用课程内置策略快照。
3. `helpers.evalSandboxFs(path, mode, policy?)` —— OpenShell 文件系统（Landlock）策略的静态实现，对某路径的读或写返回 `allow` / `deny`。
4. `helpers.sandboxExec(command, {agent})` —— 经 `openshell sandbox exec` 在实时 sandbox 内运行命令，返回内核实际允许或拒绝后的输出，用于验证上面两个预测。
5. `helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk})` —— 通过 `/ws/terminal` 打开 PTY 执行命令（`"bash"` 进虚拟机 shell，`"openshell sandbox connect <agent>"` 进受保护的智能体），返回 `{ output, raw, frames, exitCode, completion, transport }`。
6. `helpers.openclawChat(message, {session, onToken, onTool, view})` —— 通过 `/cli/gateway` WebSocket 与实时 OpenClaw 智能体对话并流式接收，传入 `view` 会完整驱动工具调用与 token 预算的可视化；网关不传输推理通道。
7. `helpers.chatStream(opts)` —— 流式模型调用，先到 token 实时显示，返回含 `.content`、`.reasoning`、`.tool_calls`、`.finish_reason`、`.usage` 的摘要。
8. `helpers.getConfig()` —— 返回当前聊天配置 `{ mode, url, model, needsKey, iframeProxy }`，决定后续所有模型调用走哪条路由（含中继与直连选择）。
9. `helpers.webSearch(q, {maxResults})` —— 无需密钥即在课程资料目录 `assets/materials_index.json` 上做排序检索，返回 `{ results:[{title, body, href, tier, kind}], count, unreachable }`，`tier` 区分 cached 与 on_demand。
10. `helpers.embed(text, {model, inputType})` —— 向持久化嵌入路由 `{cfg.url}/embeddings` 发 POST，返回向量数组；NVIDIA 嵌入模型要求 `inputType` 为 `"query"` 或 `"passage"`（配合 `cosineSim` 即标准检索基本操作）。

## 模块级要点

- **主线**：模块 3 让智能体“能持续做事”（持久上下文、`SOUL.md`、定时任务），模块 4 回答“它凭什么被允许做这些事”。04a 把权限问题下沉到操作系统四机制（netns + CONNECT 代理/OPA、Landlock、seccomp、非 root 进程身份），并建立一套方法：**先读生效策略 → 静态预测 → 用 `openshell sandbox exec` 实测 → 对比一致性 → 再解释证据**；同时强调证据的边界（命令失败不能指出是哪一机制拦住、一致不能证明全部规则、读权限不能证明写权限）。04b 把镜头抬高到应用封装层，说明同一循环下各产品的默认设置差异与六个“自由度”如何构成攻击面，并演示操作员平面（宿主 shell、`openshell` CLI）与智能体平面（`agent <cmd>`，沙箱内）的分野。04c（缺页）本应是“深入探索 + 全课程参考资料总表”，把前面的边界延伸到 Brev/NIMs/Blueprints 等路径。贯穿全模块的判断是：**边界可强制，含义不可强制**——沙箱能限制文件、网络与系统调用，但无法判断获准通道里传输的字节是否有害，因此还需要输入来源追踪、审批、最小化 token 作用域、审计与可审查的历史记录。
- **术语表（中文术语 —— 英文/代码标识符）**：

| 中文术语 | 英文 / 代码标识符 |
|---|---|
| 沙盒 / 沙箱 | sandbox；`openshell sandbox exec`、`openshell sandbox connect <agent>`、`openshell sandbox list` |
| 安全运行时 | OpenShell |
| 智能体框架 | OpenClaw、Hermes、LangChain deepagents |
| 参考技术栈 | NemoClaw |
| 沙盒用户 | `sandbox`（非 root 用户 / 非特权用户） |
| 网络命名空间 | netns / `network_namespaces(7)` |
| CONNECT 代理 | HTTP CONNECT proxy（MDN CONNECT） |
| 策略引擎 | OPA / Open Policy Agent |
| 策略即数据 | policy-as-data（原文评 OPA 为“策略即数据引擎”） |
| 文件系统边界 | Landlock（`best_effort`、环境权限 ambient authority、工作区目录树、绑定挂载 `mount(2)`、符号链接竞态 `symlink(7)`） |
| 系统调用边界 | seccomp（系统调用允许列表、BPF 层、`ptrace(2)`、`mount(2)`、`setuid(2)`） |
| 系统调用 | syscall |
| 操作不允许 / 权限被拒绝 | `EPERM` / `EACCES`（`errno(3)`） |
| 检查竞态 | TOCTOU |
| 进程身份 | 智能体进程、非 root UID、`capabilities(7)`（`CAP_SYS_ADMIN`、`CAP_SETUID`） |
| 权限提升 | privilege escalation（04a 图中“权限提升轴”位于检查点上方） |
| 控制平面 | operator 平面 / `operator.admin`、operator token 平面、`openshell status` |
| 操作员平面 / 智能体平面 | operator plane / agent plane（`agent <cmd>`、`agent ls`） |
| 最小权限 | least privilege（Saltzer & Schroeder, 1975） |
| 边界而非意图 | Rice 定理：评估边界，不试图证明意图 |
| 致命三要素 | lethal trifecta（私有数据 + 不可信输入 + 外部通信） |
| 提示词注入 / 目标劫持 | prompt injection / goal hijacking（OWASP Top 10 for Agentic Applications） |
| 默认拒绝 | default deny（入站/出站 inbound/outbound） |
| 框架负担 | framework burden（默认设置与内置能力的成本与便利性） |
| 自由度 | degrees of freedom（文件系统、网络出站访问、进程身份、二进制文件身份、持久化、推理路由） |
| 可执行文件标识 / 二进制文件身份 | binary identity、`argv[0]`（可被伪造，不受信任） |
| 推理路由 | `inference.local`、Privacy Router |
| 网关 | gateway（`/cli/gateway`、`/ws/terminal`、`openshell status`） |
| 交互式全屏对话界面 | `openclaw tui` |
| 角色设定 | `SOUL.md`、`AGENTS.md`、`CLAUDE.md`、`.cursor/rules/*.mdc` |
| 定时任务 | cron、计划任务、定时触发器 |
| 可启动实例 | launchable instance（`helpers.terminal`、`helpers.sandboxExec`、`helpers.policyGet` 仅适用于此） |
| 运行时日志 | `logs.tail`；工具搜索开关 `tools.toolSearch` |
| 故障模式 | failure mode（目标劫持、工具滥用、身份或权限滥用、供应链攻击、意外代码执行、记忆或上下文污染） |
| 深入探索 | 04c `04c-going-further.html#refs`（本归档缺页） |
