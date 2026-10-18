模块 4 · 课时 1 / 3

# OpenShell 沙盒

在模块 3 中，文件提供持久上下文，定时任务则启动无人值守的工作。这些操作取决于智能体进程可用的权限。OpenShell 通过生效中的策略及其强制执行机制限制这些权限。

在沙箱中执行命令，检查输出和退出状态，并调查原因。接着通过操作员控制平面检查读取权限。

**章节**

1. 各防御层在何处介入
2. 沙盒机制如何回答可测试的问题
3. 先调整运行时
4. 检查命令结果
5. 进一步探索：完整轨迹
6. 读取可启动环境的实时策略，然后以地图形式查看
7. 比较策略预测与实际请求
8. 沙箱之上：控制平面
9. 沙箱无法拦截的风险

*OpenShell 将控制入口、策略执行、智能体状态、工具访问和模型路由彼此分离。本页从沙盒原理转入实时策略检查时，请随时参照此图。*

- OpenClaw 是智能体框架。它决定使用哪个工具以及尝试执行什么操作。
- OpenShell 是安全运行时。它限制该操作能够访问的文件和网络目标，以及能够执行的操作系统操作。
- NemoClaw 是参考技术栈，将 OpenClaw 和 OpenShell 与生命周期命令、策略预设、推理指南及部署默认配置封装在一起。

OpenShell 与具体智能体无关。同一道边界可以封装 OpenClaw、Hermes 、LangChain deepagents ，或其它需要操作系统级隔离的进程。

## 各防御层在何处介入

假设不受信任的内容指示智能体读取凭据并将其发送出去。三个不同层级都有机会阻止该操作，且每一层要回答的问题各不相同。

- 提示词塑造意图。 “不得泄露凭据”之类的规则会告诉模型应如何行事。但模型仍可能被对抗性检索内容、恶意工具输出或循环中的其它智能体欺骗。此层会影响决策，但智能体仍保留运行时授予它的所有权限。
- 智能体工具框架验证请求。 OpenClaw 或 Hermes 可以在请求到达操作系统前，拒绝不受支持的 shell 形式、被禁止的工具调用或格式错误的参数。这种确定性检查很有用，但它仍属于应用逻辑，可能存在配置错误、版本过时或遭到入侵的问题。
- 沙盒限制操作结果。 OpenShell 仅向进程授予策略允许的权限。即使提示词和工具框架均未能阻止操作，操作系统仍可在文件、网络或进程操作完成前将其拒绝。

**为什么策略执行应位于模型之下**

### 假定看似有效的请求仍可能造成危害

零信任 拒绝仅根据请求来源对其给予隐式信任。 OWASP 的提示词注入指南 将同样的原则应用于智能体：约束工具、限制权限，并假定外部内容可能引导模型。

### 仅授予任务所需的权限

Saltzer 和 Schroeder 将此描述为最小权限原则：每个组件只获得完成其工作所需的权限。由于这一原则早于智能体出现，因此可以自然地应用于当前场景。

### 评估边界，而非尝试证明意图

Rice 定理 排除了对任意程序的非平凡行为进行通用判定的可能性。对于具备代码执行能力的智能体，同样应保持谨慎：应对运行内容周围的边界进行检测，而不能假定静态检查能够证明未来的每项操作都安全。

## 沙盒机制如何回答可测试的问题

此本地运行时组合了四种操作系统机制。每种机制都回答一个可以测试的问题，它们共同在多道边界上应用策略。在将任何一项保证视为普遍适用之前，请先阅读本页后面的实时策略。

*被阻挡的箭头示意可能遭拒的操作。仅凭命令结果无法识别负责限制的机制。*

### 1 · 此进程可以连接到哪里？

网络命名空间 （netns ）为智能体提供隔离的网络栈。初始状态下，出站访问处于关闭状态。 HTTPCONNECT 代理 是唯一的出站路径。Open Policy Agent（OPA） 会依据策略检查发起请求的二进制文件、主机、端口和路径。策略的编辑者决定允许哪些连接。

### 2 · 它可以访问哪些文件？

Landlock 是一种限制后续文件系统访问的 Linux 安全模块。在此处，它将新的文件操作限制在策略授予的路径内。这是一种强制执行机制，但仍需考虑兼容模式、OverlayFS，以及施加限制前已打开的句柄。请阅读实时策略，并测试您打算暴露的路径。

### 3 · 它可以请求哪些内核操作？

系统调用 (syscall) 请求 Linux 内核执行一项操作。seccomp 是 Linux 的系统调用过滤机制；其 BPF 过滤器会根据允许列表检查每项请求。被拒绝的调用会在操作执行前返回EPERM ，表示“操作不允许”。此本地运行时排除了ptrace 、mount 和setuid 等危险的底层操作。

### 4 · 它最初拥有多大权限？

智能体以非 root 进程 的身份运行，使用无特权的sandbox 用户。因此，即使攻击成功，最初获得的权限也较少。较低的初始权限可以缩小影响范围，但不能证明权限提升不可能发生。主机、容器配置和系统调用策略仍是安全边界的一部分。

**这四种机制中的术语**

### 网络策略
网络命名空间 /
隔离的 Linux 网络栈：设备、路由、防火墙规则和套接字端口。
入站 / 出站
入站流量是进入沙箱的流量，出站流量是离开沙箱的流量。默认拒绝意味着，除非策略明确允许，否则两个方向均不开放。
CONNECT 代理
HTTP 隧道代理，用于连接请求指定的主机和端口；安全的部署会限制允许访问的目标。
OPA
对结构化输入进行评估，并将决策返回给策略执行代码的策略引擎。
二进制文件、主机、端口、路径
出站策略的输入包括：可执行文件标识、目标名称、TCP 端口以及请求的 URL 路径。

### 文件系统边界
Landlock
一种 Linux 安全模块，允许非特权进程限制自身未来的访问权限。
环境权限
进程原本会从 OS、父进程、挂载点或凭据继承的访问权限。
工作区目录树
策略授予访问权限的目录子树。在将其视为完整的文件系统边界之前，请先验证当前生效的策略及其与内核的兼容性。
绑定挂载
将文件系统子树显示在另一条路径下，包括跨越 chroot 边界的情况。
符号链接竞态
已检查的路径在使用前因符号链接而发生变化。

### 系统调用边界
seccomp
Linux 系统调用过滤机制，用于缩小进程可触及的内核攻击面。
系统调用允许列表
允许执行的系统调用集合；其余系统调用都会触发策略指定的处置。
BPF 层
在执行前检查系统调用编号和参数的过滤程序。
TOCTOU / 检查竞态
检查时与使用时之间的竞态缺陷；seccomp 可避免过滤器内部发生指针解引用竞态。
/
Linux 中表示“不允许执行操作”和“权限被拒绝”的 errno 名称。

### 进程身份
智能体进程
在这些边界内运行智能体和工具的 OS 进程。
非 root 用户/非特权用户
受常规内核权限检查约束的非零 UID。
Linux capability
从 root 权限中拆分出来的某项能力，例如
或者
.
,
,
可用于控制进程、挂接文件系统和更改身份的危险底层操作。
·
·
权限提升
获得超出所分配范围的权限，例如 root 权限、额外的 capability、更广泛的文件访问权限或网络访问权限。

## 先调整运行时

在您亲自操作沙箱之前，如果运行时处于降级状态，请先将其恢复，使智能体恢复正常，以便下方每个实时单元都能与可用的智能体交互。

图中概述限制的边界。以下命令会返回观察结果；要识别负责的机制，需要策略或审计证据。

与 Kickstart 使用相同的运行时。 此处的每个单元都会操作您在 Kickstart 页面上连接的同一个 OpenClaw 智能体。
共享 OpenClaw 运行框架的健康检查、条件修复和日志。健康检查会运行命令并读取 toolSearch。仅当 toolSearch 已启用时，恢复操作才会更改它；清除会话和重启是独立的可选操作。运行时日志会在执行停滞时持续读取日志。

**辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

*被阻挡的箭头示意可能遭拒的操作。仅凭命令结果无法识别负责限制的机制。*

## 检查命令结果

一次执行一个命令，检查其输出、退出状态以及是否完成。失败可能来自策略、缺少软件、无效请求或服务本身。利用证据和当前策略调查原因。

初始目录涵盖了您可能向此类环境提出的各种问题，从访问开放互联网，一直到改写智能体自身的人设；可以自由编辑任意命令，也可以添加自己的命令。
执行准备好的问题并比较每个命令的结果，再打开实现代码以修改命令或添加探测。这些探测会清理使用的临时文件，列出 SOUL.md 而不修改它，并丢弃读取的环境内容。

**辅助函数位于此单元格的作用域内。点击行可查看其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS javascript · 可编辑 · 57 行**
在您运行前为空

**运行多命令沙盒轨迹？**

## 进一步探索：完整轨迹

智能体可以为一个目标规划多个命令。检查计划，再将每个命令与沙盒返回的输出和退出状态进行比较。判断哪些结果提供了访问被拒绝的证据，哪些还需要进一步调查。

允许执行的命令一旦打印出秘密，秘密就已经进入输出通道。成功与失败的步骤都要检查；后续的网络拒绝无法撤回先前的泄露。

**辅助函数位于此单元格的作用域内。点击行可查看其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS javascript · 可编辑 · 84 行**
执行轨迹控件已显示在下方。

**模型与上下文选项**
描述一个目标。检查规划的命令，再比较每个命令的输出和退出状态。仅凭命令失败，无法判断是哪项策略或强制执行机制造成的。
前提条件：请先在模块 3a 连接运行时。命令会在该沙盒中执行。

## 读取可启动环境的实时策略，然后以地图形式查看

解读命令结果前，先读取运行时策略。此代码单元通过 operator 终端调用helpers.policyGet() ，并显示其状态和解析后的 YAML。检查返回的策略是否已生效。
通过 operator 终端获取实时策略 YAML，并将其与映射快照进行比较。请先在模块 3a 中连接。

**辅助函数位于此单元格的作用域内。点击行可查看其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS javascript · 可编辑 · 39 行**
在您运行前为空

此图会根据加载的策略评估候选目标地址。切换发起调用的可执行文件，检查授权有何不同，再查看匹配的规则。这些是浏览器的预测；实际请求提供另一份观察结果。

点击任一目标，就会打开其适用规则，让您查看该端点允许哪些可执行文件，以及浏览器评估器使用的规则。View policy source 控件会显示规则来源的 YAML，也就是您刚才获取的内容。
琥珀色区域位于检查点上方，代表出站规则完全无法感知的权限提升轴。

Run the live-policy cell above to draw your 本地运行时's policy as an interactive map.

## 比较策略预测与实际请求

选择一个操作，根据加载的策略预测结果，再通过沙盒执行相同请求。比较证据时，不要假定命令错误就能证明策略受到强制执行，也不要将结果吻合视为所有策略规则都已得到验证。

预测会考虑可执行文件身份、目标地址、端口、方法和路径。“确认”会执行选中的 curl 请求。其他可执行文件身份的结果仍只是预测，必须通过该程序自身的接口测试才能确认。
浏览器负责评估策略，
则返回命令输出和退出状态。HTTP 错误可能来自代理或目标应用程序；判断原因前，先确认错误来源。
智能体尝试 list available models · /usr/bin/curl → inference.local:443 GET /v1/models · 接下来运行“确认”，然后运行“比较”
加载实时策略，选择一项操作并预测其判定结果，然后使用 openshell sandbox exec 进行确认。比较两项结果。

**辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**
结果一致可以支持所测操作的预测。若结果不符，就应检查请求、已生效的策略、响应来源以及评估器的假设。

## 沙箱之上：控制平面

此单元使用现有网关令牌请求operator.admin ，并调用角色设定、计划任务、会话、模型和配置的读取方法。检查哪些请求成功。服务器配置可能允许管理写入，但这项检查并未测试写入。它不发送编辑请求；连接和读取仍可能产生日志。
使用现有 token 调用只读的 operator.admin 方法，并检查其原始响应。请先在模块 3a 中连接。

**辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

| 共享状态 |  |
|---|---|
| state | 所有节点共享的普通对象。在一个节点中设置字段，例如 state.question = "…"，之后的任意节点都可以读取。点击 ▶ 全部运行时，此对象会重置。 |
| helpers.randomId(prefix?) | 创建采用加密安全随机数的 UUID v4，可为会话或产物添加前缀。使用 getRandomValues，可在通过 HTTP 提供的实验环境中运行。 |
| 模型调用 |  |
| helpers.chat(opts) | 单次、非流式聊天补全。返回原始 OpenAI 格式响应。只需要最终消息时使用。 |
| helpers.chatStream(opts) | 流式聊天补全；token 到达时会实时显示在此面板的结果视图中。返回的摘要包含 .content、.reasoning、.tool_calls、.finish_reason 和 .usage。 |
| helpers.browserChatFetch() | 返回一个会移除 OpenAI SDK x-stainless-* 标头的 fetch。NVIDIA 模型路由还会收到 X-BILLING-INVOKE-ORIGIN 追踪标记；自定义路由会包含相应的浏览器会话凭据。在浏览器中构造 ChatOpenAI 时，将它传给 configuration.fetch。 |
| 模型配置 |  |
| helpers.getConfig() | 返回当前聊天配置 { mode, url, model, needsKey, iframeProxy }。学习者可以在课程主页保存一个兼容的聊天 API 入口和模型；嵌入服务使用独立路由。已发布的课程来源和本地文件预览默认使用受限的 NVIDIA DLI 中继，其它来源保持直连；自定义聊天 API 入口始终绕过该中继。 |
| helpers.getEmbeddingConfig() | 返回持久化嵌入路由 { url, model }。默认使用 NVIDIA 托管 API，学习者选择其它聊天 API 入口时不会随之改变。已发布的课程来源会与聊天路由使用相同的受限中继选择逻辑；自定义嵌入 API 入口仍保持直连。 |
| helpers.getKey() | 返回当前浏览器标签页保存在 sessionStorage 中的模型 bearer 密钥；未设置时返回 null。NVIDIA 密钥以 nvapi- 开头。模型调用会自动使用此标签页范围内的值，关闭标签页后该值即被丢弃。 |
| helpers.getModelApiBaseUrl() | 返回已保存的模型 API 基础 URL；没有有效的自定义值时返回课程默认值。 |
| helpers.setModelApiBaseUrl(url) | 验证并保存模型 API 基础 URL，然后清除本标签页缓存的模型配置。 |
| helpers.isDefaultModelApiBaseUrl(url) | 判断 URL 是否使用课程批准的 NVIDIA 模型路由。 |
| helpers.mountModelEndpointProbe(target, opts?) | 挂载可启动实例连接探测旁的只读模型 API 入口视图。 |
| Web 搜索 |  |
| helpers.webSearch(q, {maxResults}) | 无需密钥即可对课程资料目录（assets/materials_index.json）进行排序搜索。目录包含已缓存的 NVIDIA 术语表条目，以及从 Web 收录、按需访问的论文和博客。查询会与各条目的名称、标签和摘要进行匹配；任何页面都能运行，无需密钥或实验环境。每项结果都包含 tier：cached 表示课程附带全文，on_demand 表示通过 href 访问来源。返回 { results: [{title, body, href, tier, kind}], count, unreachable }。 |
| helpers.instantAnswer(q) | 当查询中明确包含某个术语时，返回一条 NVIDIA 术语表定义，例如 retrieval-augmented generation 或 deep agents。返回结构与 webSearch 相同，但只有查询与术语高度匹配时才返回一张精选卡片；自由问句不会返回结果。它是 webSearch 面向具体实体的精确查询版本。 |
| helpers.formatSearchResults(out) | 将 webSearch 或 instantAnswer 的结果转换为带编号的文本块，供 LLM 作为工具消息读取。 |
| 嵌入与相似度 |  |
| helpers.embed(text, {model, inputType}) | 向持久化嵌入路由 {cfg.url}/embeddings 发送 POST 请求。返回向量数组（numbers[]）。NVIDIA 嵌入模型要求将 inputType 设为 "query" 或 "passage"。 |
| helpers.cosineSim(a, b) | 计算两个向量的余弦相似度。越接近 1，匹配度越高。这是标准的检索基本操作。 |
| token 与上下文 |  |
| helpers.contextWindow(model) | helpers.contextWindow(model) 返回模型公布的上下文窗口大小，单位为 token。课程中的交互页面使用它显示上下文预算；未知模型默认按 131072 处理。 |
| helpers.estimateTokens(textOrMessages) | helpers.estimateTokens(textOrMessages) 粗略估算字符串或 {content} 消息数组中的 token 数量，约按每 4 个字符一个 token 计算。它适合运行前检查；权威计数以模型返回的 usage_metadata 为准。 |
| 原始 HTTP |  |
| helpers.fetch(url, opts) | 浏览器原生的 fetch，保持原样公开，使节点可以直接调用任意 HTTP API 入口。参数和返回的 Response 与平台 API 完全相同。它不会重试，也不会附加密钥：上游服务不稳定时请使用 helpers.fetchRetry；模型、搜索或嵌入调用则优先使用上方的专用辅助函数，由它们自动添加路由和密钥。 |
| helpers.fetchRetry(url, opts) | 与 helpers.fetch 类似，并可接受一个有界的可选第三参数，例如 { retries: 2, timeoutMs: 120000 }。遇到 HTTP 429 时会遵循 Retry-After，其它情况下则报告最终的网络或 HTTP 结果。 |
| 可启动实例终端 |  |
| helpers.terminal(cmd, {send, idleMs, totalMs, openMs, onChunk}) | 通过可启动实例的 /ws/terminal WebSocket 打开 PTY 并运行 cmd。使用 "bash" 进入虚拟机 shell，或使用 "openshell sandbox connect <agent>" 进入受内核 sandbox 保护的智能体。send 是依次输入 PTY 的 shell 命令行数组，每行都会附加 Enter。绑定浏览器的会话保持直连；粘贴的访问会话会先尝试直连，再尝试获准的提供商专用中继。设置 relayWebSocket: true 可明确选择该恢复路由。返回 { output, raw, frames, exitCode, completion, transport }；output 已移除 ANSI 控制码，exitCode 是 PTY 返回的退出状态，未收到时为 null，transport 表示成功打开的直连或获准中继路由。completion 区分 exit、idle、deadline 和 disconnect；只有收到退出状态才能确认命令结束。Stop 会取消操作。可启动实例 URL 从 OpenClaw 探测结果中读取。仅适用于可启动实例。 |
| helpers.courseShell(helpers, command) | 在已连接的 sandbox 中执行命令，并要求退出状态为零。传入当前单元格的辅助函数以支持取消。返回终端文本；请重新读取文件以验证内容。 |
| helpers.courseRead(helpers, path) | 从已连接的 sandbox 读取课程工作区文件。要求返回完整的带边界标记的响应，并解码 UTF-8 字节。传入当前单元格的辅助函数以支持取消操作。 |
| OpenShell 策略 |  |
| helpers.evalSandboxNetwork({binary,host,port,method,path}, policy?) | 静态评估候选连接与 OpenShell 网络策略，返回 {action, matched, reason}，不发送网络请求。默认使用课程内置策略快照。先用 policyGet 读取实时策略，再传入评估函数；命令失败本身不能证明是哪种机制拒绝了访问。 |
| helpers.evalSandboxFs(path, mode, policy?) | OpenShell 文件系统（Landlock）策略的静态实现。针对 path 的读取或写入返回 "allow" 或 "deny"。默认使用实时可启动实例的强化策略。 |
| helpers.sandboxExec(command, {agent}) | 通过 openshell sandbox exec 在实时 OpenShell sandbox 内运行 command，并返回内核实际允许或拒绝后的输出。未提供 agent 时会自动发现 sandbox 名称。可使用它对正在运行的 sandbox 验证 helpers.evalSandboxNetwork 或 evalSandboxFs 的预测。仅适用于可启动实例。 |
| helpers.policyGet(agent?) | 读取可启动实例的实时 OpenShell 策略。通过 operator 终端运行 openshell policy get <agent> --full 并解析 YAML 正文。返回 { agent, command, raw, status, policy, parseError }，其中包括实际运行的命令、原始返回文本、状态标头、解析后的策略对象，以及策略不可用时的明确解析错误；evalSandboxNetwork 和 evalSandboxFs 会读取该结构。仅适用于可启动实例。 |
| helpers.mountPolicyMap(target, opts?) | 根据提供的策略挂载交互式 OpenShell 信任边界图。 |
| 课程内容 |  |
| helpers.coursePage(id) | helpers.coursePage(id) 以 Markdown 形式返回一个课程页面的正文。id 是类似 "01b-react" 的文件 ID；可以使用 helpers.coursePages() 列出。该请求为同源请求，无需密钥。可将其接入 read_course_page 工具，使回答基于实际课程内容。 |
| helpers.coursePages() | helpers.coursePages() 以 [{ id, title }] 形式返回页面列表。它是模块菜单或 read_course_page 工具 enum 字段的唯一来源。 |
| helpers.mountFigures(rootSel?) | 将 rootSel 下的每个 [data-svg-src] 占位符替换为从相应路径获取的 SVG；默认范围是整个文档。SVG 会以内联方式注入，使 var(--gfx-*) 主题生效，并支持单击或按 Enter 打开适应屏幕的灯箱。页面加载时会自动挂载。 |
| helpers.openFigureLightbox(svg, trigger?) | 在支持键盘操作的共享灯箱中打开 SVG 副本。 |
| helpers.wireFigureZoom(host, svg?) | 使 SVG 可通过单击、Enter 或空格键打开共享灯箱。 |
| 交互页面 |  |
| helpers.mountChatUI(el, opts) | 在 el 中渲染可实时观察的聊天界面，包括控件、流式对话记录和输入框。opts 包含 { modules:[{id,title}], models:[{id,label}], intro, greeting, showGreetingWithHistory, memory, respond(text, ctx), onReset() }。恢复历史轮次后仍需显示当前上下文提示时，请设置 showGreetingWithHistory:true。设置 memory:true 后，组件会保留对话、显示默认开启的记忆开关，并通过 ctx.history 提供先前轮次；关闭记忆时该数组为空，因此同一个 respond 会表现为无状态函数。编辑按钮会将对话记录回退到相应轮次。respond 通过 ctx.view 流式输出：view.token(t) 显示以 Markdown 渲染的回答，view.reasoning(t) 显示可折叠的思考过程，view.tool(label, detail) 显示可展开的工具标签，view.usage({input, output}) 显示本轮 token 和累计上下文，另有 view.html(h) 与 view.error(msg)。ctx 包含 { module, modules, model, thread, turn, history, memory }；modules 是固定的页面 ID 数组，为空时自动选择。返回 { thread, reset(), ctx }。 |
| helpers.mountAgentChat(el, opts) | 基于 LangChain createReactAgent 的实时聊天界面。opts 包含 { models:[{id,label}], system, buildTools({tool,z,coursePage,coursePages,webSearch,formatSearchResults}), greeting, modules, recursionLimit, growLog, initialHistory, initialActivity, onUserMessage, onTurnSnapshot, onAssistantMessage, onHistoryChange, compactAtTokens, compactKeepMessages }。恢复的历史记录会初始化新的 checkpoint；压缩操作使用当前模型总结较早轮次、保留最近消息并切换到新 thread。设置 growLog:true 后会移除面板内部的滚动高度限制，使长对话随页面展开。此函数加载课程附带的 LangChain bundle，为每个模型构建一个智能体，通过 MemorySaver 支持多轮对话，流式显示 token 和工具标签，并处理缺少密钥的情况。它是 mountChatUI 的现成智能体版本。 |
| helpers.mountConsole(target, opts?) | 挂载带历史记录、建议、补全、取消和输出钩子的终端式控制台。 |
| helpers.mountOpenClawCli(target) | 挂载 OpenClaw 实时命令/聊天界面，无需将网关 RPC、会话标签页、自动补全和渲染支撑代码复制到学习者单元格中。 |
| helpers.mountKeyPanel(el) | 使用现有的 .key-panel CSS 类渲染内联 API 密钥设置面板。保存密钥后，面板会显示紧凑的“? 已保存”行和“更改”按钮。保存时会移除不可见 Unicode 字符、在线验证密钥，然后更新顶部栏中的 #key-status 状态标签。 |
| 图表字符串 |  |
| helpers.diagramSVG(spec) | 以 SVG 字符串形式返回使用课程主题的节点/边图，也就是 helpers.viz.diagram 的字符串版本，交互页面可通过 view.html(...) 渲染。spec 结构相同：{title?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral。 |
| helpers.ganttBarsSVG(workers, wallSeconds, title) | 以 SVG 字符串形式返回甘特式并发图，也就是 helpers.viz.ganttBars 的字符串版本，可由交互页面通过 view.html(...) 渲染。workers 是 {label, dt} 数组，时间单位为秒；图表会将各工作线程的条形及串行耗时之和与实际 wallSeconds 进行比较。 |
| OpenClaw 网关 |  |
| helpers.openclawBootstrapRequest(path) | 通过从模块 3a 标准化连接中选择的提供商读取 /api/agent 或 /healthz。对于 Pomerium，这些固定 API 入口会通过终端 WebSocket 从可启动实例的 loopback 读取；系统先尝试已登录的浏览器会话，再尝试获准的提供商专用中继。返回响应元数据和解析后的 JSON，不暴露任何访问凭据。 |
| helpers.openclawChat(message, {session, onToken, onTool, view}) | 通过 /cli/gateway WebSocket 向实时 OpenClaw 智能体发送一轮聊天并流式接收回复。可启动实例 URL 和 token 从 OpenClaw 探测结果（Kickstart 页面）中读取。传入 view（即 mountChatUI 的 ctx.view）后，它会完整驱动可观察的执行过程：回答文本、按执行顺序排列的每个工具或命令调用标签（包含参数和完整结果，并标记错误），以及网关报告的上下文 token 预算。也可以传入 onToken(delta) 和 onTool(name,{id,args}) 自行处理事件。网关不会传输推理通道，因此页面不显示推理内容。多轮对话应复用同一个 session。它是 chat()/createReactAgent 对应的网关辅助函数。 |
| helpers.courseTurn(state, helpers, session, message) | 通过此工作流已建立的网关连接发送一个轮次，等待已确认运行的最终聊天事件。传入当前单元格的辅助函数，以便使用本次运行的停止按钮，并记录事件和创建的会话。 |
| helpers.openclawLoopbackProbe(path, opts?) | 通过 Pomerium 可启动实例的终端读取获准的 OpenClaw 引导端点，而不暴露浏览器 cookie。 |
| helpers.openclawGatewayWsUrl(url, session?, relay?, enabled?, provider?) | 为 OpenClaw 网关生成直连或获准中继的 WebSocket URL。 |
| helpers.runOpenClawConnectionAudit(opts) | 依次测试可启动实例的元数据、网关、终端和健康路由，并返回脱敏证据。 |
| helpers.redactOpenClawDiagnostic(value) | 递归移除 OpenClaw 诊断数据中的凭据及含凭据的 URL。 |
| helpers.refreshOpenClawGatewayToken(opts?) | 从已验证的智能体元数据刷新网关 token，并仅保存在本标签页中。 |
| helpers.getOpenClawConnection() | 迁移旧存储后，返回规范化的可启动实例路由、提供商和标签页凭据。 |
| helpers.setOpenClawConnection(connection) | 验证并保存可启动实例路由，同时将凭据限制在本标签页。 |
| helpers.filterOpenClawRuntimeNoise(text) | 移除已知容器噪声，同时保留与学习相关的 OpenClaw 输出。 |
| helpers.filterOpenClawRuntimeValue(value) | 递归过滤数组和对象内字符串中的 OpenClaw 噪声。 |
| helpers.openclawMessageText(message) | 从字符串或内容块数组形式的网关消息中提取干净文本。 |
| helpers.openclawResultText(result) | 从 OpenClaw 工具结果及其结构化内容块中提取干净文本。 |
| 运行控制 |  |
| helpers.signal | 本次运行对应的 AbortSignal，已连接到停止按钮。helpers.delay、helpers.chat 和 chatStream 会自动使用它。将它传给 helpers.fetch 或您自己的 WebSocket 清理逻辑，确保学习者按下停止按钮后，长时间运行的任务能够真正取消。 |
| helpers.delay(ms) | 等待指定时间，同时允许学习者停止正在运行的单元格。CanvasFlow 和 RunCell 会自动将此辅助函数连接到停止按钮；只有等待过程属于其它生命周期时，才需要传入另一个 AbortSignal。 |
| 追踪与日志 |  |
| helpers.trace(name, attrs) | 向每个 CanvasFlow 独立的追踪存储中写入一个符合 OTel 结构的 span 事件。任何实际执行工作的步骤都应记录，而不仅限于 LLM 调用。后续节点可以读取 state.__trace，查看所有已写入事件。 |
| helpers.log(...args) | 向当前单元格的日志区域追加内容。普通值以文本形式追加，对象则渲染为带语法高亮的 JSON。CanvasFlow 和 RunCell 共用以下接口：log(...args)、log.h(title)、log.json(label?, value)、log.kv(object)、log.details(summary, body)、log.html(html)、log.svg(svgString)、log.draw(W, H, body, opts) 和 log.clear()。 |
| 可视化 · helpers.viz.* |  |
| helpers.viz.diagram(spec) | 根据数据规范自动生成适配主题的节点/边图。spec 为 {title?, caption?, nodes:[{id, label, kind, x, y, lines?}], edges:[{from, to, label?}]}；kind ∈ env|agent|tool|data|model|neutral；x 和 y 表示网格列与行。 |
| helpers.viz.lineChart(values, opts) | 为数值序列生成静态折线图。opts 为 {title?, xLabel?, yLabel?, min?, max?, width?}。SVG 的无障碍标签中包含数据点数值；学习者需要精确数据时，请另行返回源数组。 |
| helpers.viz.scoreBarChart(scored, opts) | 生成 1 到 5 分的评分条形图，并叠加阈值和平均值。scored 是 {score, label?} 数组；opts 为 {threshold, title, width}。 |
| helpers.viz.messageList(messages, title) | 用颜色区分的消息序列，其中 USER 为蓝色、ASSISTANT 为绿色、TOOL 为琥珀色。直接接收 OpenAI 格式的 messages 数组。 |
| helpers.viz.ganttBars(workers, wallSeconds, title) | 甘特式条形图，用于比较各工作线程耗时和总墙钟时间。 |
| helpers.viz.retrievalBars(scored, topK, title) | 检索结果的水平分数条形图，以绿色突出显示 top-k 条目，并调暗其它条目。 |
| helpers.viz.diffTable(spec, opts) | 生成前后对比表，包含按变化着色的差值、勾选标记、页脚说明，以及可选的 verdict({rows})；该函数返回 {ok, text}。spec.rows 条目可以是 {kind:"check", label, left, right}，也可以是 {kind:"num", label, left, right, betterWhen:"up"|"down", fmt?}。 |
| helpers.viz.chat(turns, opts?) | 以不同颜色的气泡显示聊天记录。turns 是 [role, content] 对的数组；role ∈ {user, assistant|ai, system, tool}。opts.maxChars 用于限制每轮显示的字符数。 |
| helpers.viz.sideBySide(leftLines, rightLines, opts?) | 并排显示两列文本。opts 为 {leftTitle, rightTitle, footer}。 |

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**

## 沙箱无法拦截的风险

读取检查不能证明写入权限。此外，有害流程可能组合各自获准的读取操作与对外通道。

不可信输入、私有数据和外部通信共同构成致命三要素。

- 私有数据是指智能体可以读取、但不应泄露的任何内容：工作区文件、电子邮件、token、记忆或内部记录。
- 不可信输入是指并非由操作员编写、但模型仍可能将其视为指令的外部内容，例如网页、议题、文档、工具结果或对等智能体的响应。
- 外部通信是指任何能够将字节传出的路径：HTTP、拉取请求、聊天、日志行、图像加载，甚至是用户可能点击的链接。

这些权限组合在一起时便会产生风险。策略可以正确地允许某个出站 API 入口，但该 API 入口仍是全双工的：请求向外发送，响应则作为更多输入返回。一旦恶意内容能够操纵模型，它就可以要求读取私有数据，再通过沙箱视为已获允许的通道将数据发出。网络允许列表批准的是目标地址，而不是获准连接中所传输字节的含义。在沙箱上方对其中任何一个环节实施管控，都能切断漏洞利用所需的路径。

*红色中心表示一条贯穿已获准能力的路径。恶意内容可以操纵某个运行时，使其读取受保护状态并使用获准的双向通道。*

请根据实际配置评估以下失败模式：

- 角色设定遭篡改。如果智能体可修改 SOUL.md，请检查所有权和写入权限。策略、由主机管理的文件保护，以及可供审查的历史记录，都有助于保护角色设定的变更。
- 控制平面权限。令牌范围与服务器配置决定可用的管理方法。读取成功并不代表获准更改角色设定、计划任务或对话。
- 输入注入。获准的通道可能传送恶意指令。网络限制不能证明输入内容可信；请分别评估输入处理方式及会造成实际影响的操作。
- 通过获准通道外泄。获准的 API 入口可能成为数据外泄的路径。策略只能证明该通道已获允许，无法判断其中传输的字节是否无害。
- 隐藏意图。单独获准的动作可能组合成有害的工作流。评估工具日志时，请检查这些动作共同产生的影响。
- 维护同伴。智能体对同伴的判定可能随社交语境改变。请控制语境的变化条件，比较它在不同情况下的判断。

### 根据故障模式选择控制措施

沙箱限制遭入侵的进程能够访问的范围。对于内核无法理解其含义的决策，仍需由应用和运维实践负责。

| 故障模式 | 沙箱发挥的作用 | 仍需在沙箱上层实施的控制 |
|---|---|---|
| 目标劫持或提示词注入 | 限制模型受到操纵后能够访问的文件、进程和目标地址 | 输入来源追踪、后果重大操作的审批，以及行为评测 |
| 工具滥用 | 限制工具运行时可使用的 OS 和网络范围 | 逐工具授权、参数验证、速率限制，以及不可逆调用的确认机制 |
| 身份或权限滥用 | 以非 root 身份启动进程，并阻断特定的权限提升路径 | 工作负载专用身份、最小化的 token 作用域、较短的有效期、轮换和审计 |
| 供应链攻击或意外代码执行 | 减少已安装代码可访问的文件、系统调用和出站通道 | 固定并验证依赖项、安装策略和完整性监控 |
| 记忆或上下文污染 | 当策略将指定文件设为只读时，可以保护这些文件 | 写入来源追踪、可审查的历史记录、信任标签，以及从已知良好状态恢复 |

这些类别与OWASP Top 10 for Agentic Applications 一致。请使用此表选择策略执行点，不要要求单一层识别所有类型的危害。

### 参考资料

- Simon Willison, The lethal trifecta (2025)。该文阐述了由私有数据、不可信内容和网络访问构成的攻击路径，也是步骤 3 中致命三要素图的依据。
- Greshake et al. (2023) Not what you've signed up for。这篇经典论文研究间接提示词注入：攻击通过模型所信任的检索内容或渲染内容传递。
- Saltzer and Schroeder, The Protection of Information in Computer Systems (1975)。该文首次提出最小权限这一名称；它也是默认拒绝式隔离背后的原则。
- seccomp 过滤器和 Landlock。这是 openshell 在机制 2 和机制 3 中使用的内核系统调用允许列表与文件系统能力原语。
- Open Policy Agent。CONNECT 代理使用此策略即数据引擎评估策略，管控每个出站连接。
- NeMo Guardrails。它在应用层补充内核隔离，可捕获内核无法识别的策略违规行为。
- OWASP 智能体式应用 Top 10。这是一个当前适用的分类体系，涵盖目标劫持、工具滥用、身份滥用、供应链入侵、意外代码执行和记忆投毒。

完整列表请参阅深入探索 · 参考资料 。

**AI 辅助内容 · 人工审核**

本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN ·资料来源EN .
课程原创文字、示例代码和原始图表采用
许可。注明名称的外部资料沿用各自条款；请参阅
。

浏览器会保存对话和课程偏好设置；发送消息时，所选 AI 服务会处理输入。删除本地会话不会删除服务端记录。请使用虚构、非机密的数据，并遵守所选服务的条款。

NVIDIA 隐私政策 ·隐私权利与请求 ·NVIDIA API 试用条款 ·GitHub 托管隐私说明