模块 1 · 课时 2 / 3

# ReAct 循环

基于语言模型构建的智能体同样会反复感知环境、进行推理并采取行动。模型会在行动之间用文字进行推理，这也是这一模式名称的由来。Yao et al. (2022) 将这种结合推理与行动的模式称为ReAct 。他们发现，将简短的推理轨迹与工具使用交替进行，在许多任务上比预先规划全部步骤或不经推理直接行动更可靠。

工具 是运行框架可代模型执行的代码：一个具有名称、描述、输入模式和返回值的函数。工具调用 是模型发出的结构化代码执行请求。运行框架解析该请求、执行函数、追加结果，然后再次调用模型。

大多数通用智能体框架都以这一循环为基础，LangChain 的createReactAgent 也是如此。本模块的后续内容将逐步构建这一循环。

**章节**

1. 决定循环下一步操作的唯一字段
2. LLM 智能体的组成部分
3. 使用一个工具从头构建循环
4. 上下文退化：循环越长，为何理解效果越差
5. 将相同的循环应用到本课程
6. 继续学习之前

*循环本身没有变化。以语言模型执行推理步骤时，智能体读取工具结果，并通过调用工具采取行动。*

## 决定循环下一步操作的唯一字段

每个 Chat Completions 响应都包含finish_reason ，用于说明模型停止生成的原因。在智能体循环中，将它与响应内容和工具请求一起检查，决定执行工具、返回回答还是处理错误。在了解各个值之前，先发出两次调用并比较回复。
比较两个问题、提供的工具和实际回复。模型可能直接回答或表示无法回答，而不请求工具。

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

**JS javascript · 可编辑 · 52 行**
在您运行前为空

第一次调用不提供工具。第二次调用向模型提供工具并询问当前时间。是否请求使用时钟工具仍由模型决定。比较显示的问题、回复和finish_reason 。如果两次都返回"stop" ，请检查第二条回复：模型承认无法查询时间，还是给出了未经验证的回答？更换模型或问题后重新运行。工具请求只是指明需要代码执行的工作；此预览不会执行工具。

- "stop" 表示模型已生成最终答案，循环可以将 content 返回给用户。
- "tool_calls" 表示模型要求代码运行指定函数，追加结果后再回调模型。
- "length" 表示答案尚未生成完毕，token 预算就已耗尽。
- "content_filter" 表示安全分类器停止了输出。

在现代 ReAct 中，一个简短的路由逻辑会读取该字段。如果模型请求使用工具，路由逻辑就会运行函数、追加结果并再次调用模型。如果模型已经停止，路由逻辑就会返回答案。

模型读取工具结果后，可以修改原先的计划。每当工具返回意料之外的结果时，该结果都会进入下一轮推理，模型可以重新评估当前状况，再决定下一步操作。

**梳理模型、记忆、工具和路由？**

## LLM 智能体的组成部分

仔细观察智能体，您会看到Lilian Weng 在 2023 年提出的 组成结构。语言模型位于中心，周围是记忆 、规划 、工具 以及触达外部世界的行动 。

在下方的工具循环中，这些职责分配如下：

- 记忆是 messages[] 数组。
- 规划发生在模型根据提供的上下文，选择下一次响应或工具请求时。
- 工具是运行框架公开的函数。
- 行动是运行框架执行的工具调用。

运行框架负责维护消息并执行工具。其路由器读取finish_reason ，决定是处理工具请求，还是返回答案。

*改编自 Lilian Weng (2023)：模型是智能体的核心控制器，记忆、规划、工具和行动围绕它连接起来。*
可以单独替换模型、工具或路由；只要各模块仍遵守其它模块所依赖的契约，循环的其余部分就能继续运行。

如果这个循环出现故障，请检查组件之间传递的值，确认是否存在以下情况：

- 模型返回了错误的 finish_reason；
- messages 数组中缺少一轮消息；
- 工具执行器返回了意外的值；
- 或者路由误读了信号。

## 使用一个工具从头构建循环

接下来尝试从头创建一个简单循环。只需要一个名为get_current_time 的工具、一条系统提示词和一个while 循环。先用“现在 UTC 时间是多少？”运行它，再看看您还能提出哪些问题：

*思考、行动、观察、重复。一旦 finish_reason 为 "stop"，当前轮次立即结束。*
设置提示词并注册一个工具，然后观察循环如何调用模型、执行请求、追加观察结果并停止。

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

```
// Save the system prompt that frames the agent loop.
state.systemPrompt = "问题需要当前时间时，请使用 get_current_time。"
  + "训练数据无法提供实时时钟读数。请根据工具结果回答。";
state.userPrompt = "现在的 UTC 时间是几点？请使用 get_current_time 读取时钟。";
// state.userPrompt   = "What is the capital of France?";
// Next compare: a meeting tomorrow at 10am in France also requires a timezone assumption.
return state.userPrompt;
​
```

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

```
// Define the tool schema the model can choose from next.
state.TOOLS = [{
  type: "function",
  function: {
    name: "get_current_time",
    description: "以“YYYY-MM-DD HH:MM:SS UTC”格式返回当前 UTC 时间。",
    parameters: { type: "object", properties: {}, required: [] },
  },
}];
state.execTool = (name) =>
  name === "get_current_time"
    ? new Date().toISOString().slice(0, 19).replace("T", " ") + " UTC"
    : `（未找到工具“${name}”）`;
​
return state.execTool("get_current_time");
​
```

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

**结果流式输出 · 日志 · 返回值尚未运行**
当模型请求时钟时，循环会向
中加入以下四项：

- 系统提示词（第 0 轮），
- 用户的问题（第 1 轮），
- 一条带有 tool_calls 字段的 assistant 消息（第 2 轮，即请求），
- 以及一条保存函数返回值的 tool 角色消息（第 3 轮）。
下一次模型调用会收到这些消息，包括时钟结果。检查模型的响应，确认它是作答还是再次请求工具。这个不断增长的数组就是该智能体拥有的全部“记忆”。保存并重新加载该数组可以保留所提供的对话历史；外部事实和模型行为仍可能发生变化。

**需要上下文退化的证据和缓解措施？**

## 上下文退化：循环越长，为何理解效果越差

上下文退化 是指矛盾、过时的观察结果和不良约定不断积累在提示词历史中，最终导致模型下一次决策质量下降的趋势。这种影响还与信息所在的位置有关：Liu et al. (2023) 的研究表明，模型可能无法充分利用埋藏在长上下文中部的信息。重要信号距离当前轮次越远，循环就越容易忽略它或产生与之矛盾的结果。

*根据 Liu et al. (2023)的研究重绘。随着循环不断追加轮次，您所需的答案会逐渐移入模型表现较弱的上下文中部。*

常见的缓解方法会让每次决策尽量靠近其所需的证据：

- 在循环积累观察结果之前先制定计划；
- 委派子任务，让每个子智能体在较短的上下文中工作；
- 或者在早期轮次成为负担之前对其进行总结。

## 将相同的循环应用到本课程

上面的循环硬编码了一个很小的工具。LangChain 的createReactAgent 对相同机制进行了泛化，可支持更多工具、标准接口和可观测性集成。下面的智能体只使用一个工具，read_course_page ，它可以将本课程任意页面以 markdown 格式提供给智能体。模型会根据问题决定读取哪些页面，请亲自试一试。

运行单元格打开聊天面板，然后提问“时钟循环如何决定何时停止？” 您可以不选择页面，让智能体自行决定读取哪些课程页面。若要自行选择上下文，请在第一条消息前打开模型与上下文选项 ，在页面 下选择标题。标题的提示信息会显示源 ID，例如01b-react 。如果之后更改页面选择，请点击新建对话 。展开来源标签，将回答与智能体实际读取的内容进行比较。
使用 read_course_page 和 MemorySaver 构建 LangChain 聊天智能体。编辑智能体、工具或提示词，然后重新运行。

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

**JS javascript · 可编辑 · 122 行**
在您运行前为空

## 继续学习之前

返回时钟循环画布 ，修改输入以进行这些比较。

1. 即使模型不需要使用工具，也强制它进行工具调用。尝试提出一个工具确实无法回答的问题（“法国的首都是哪里？”），并观察第 1 步中的 finish_reason。它的值是 "stop" 还是 "tool_calls"？现在编辑系统提示词，要求模型必须先进行工具调用再回答（“您必须始终调用 get_current_time 一次，然后再回答。”）。模型是否遵从了要求？如果模型根据训练数据对另一个答案方向很有信心，这一现象说明系统提示词对模型的引导作用有多强？
2. 统计需要工具的问题所用的步骤。“距离 17:00 UTC 还有多少分钟？”需要读取时钟并进行计算。运行几次，看看模型调用 get_current_time 一次、两次还是三次。为什么模型会重复调用已获取结果的工具？您会如何修改系统提示词来减少重复调用？

**这些比较能帮助我理解什么？**

第一组比较区分提示词指令和程序强制执行的控制流。先比较所请求的工具与finish_reason ，再判断指令是否得到遵循。仅有请求并不能证明时钟已运行。

第二组比较关注每次额外工具调用是否提供了有用证据。检查时钟结果及其在messages 中的顺序。如果顺序不清楚，请先返回时钟循环画布并展开跟踪记录，再修改提示词。不同运行的结果可能不同，请依据自己的跟踪记录解释结果。

**从一手资料追溯这些机制？**

### 参考资料

- Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models (2022)。提出了最初的思考、行动与观察交替模式；上图根据该论文重绘。
- Wei et al., Chain-of-Thought Prompting (2022)。这是 ReAct 中的“推理”部分，即模型在行动前进行斟酌时，在 reasoning_content 内部执行的过程。
- Lilian Weng，LLM Powered Autonomous Agents (2023)。上图采用了该文的分解方式：语言模型充当智能体的核心控制器，外围是记忆、规划和工具使用能力。
- Xu et al., ReWOO: Decoupling Reasoning from Observations (2023)。该方法有意与 ReAct 形成对比：模型预先写出完整计划，再由独立的执行器运行；各步骤之间无需再次查询模型。对比二者可以看出响应式重新规划与预先确定执行方案之间的权衡。
- Schick et al., Toolformer (2023)。1c 的参考资料中还会再次介绍；此处可通过该论文回顾 ReAct 循环所利用的底层机制。

完整列表请参阅深入探索 · 参考资料 。

**AI 辅助内容 · 人工审核**

本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN ·资料来源EN .
课程原创文字、示例代码和原始图表采用
许可。注明名称的外部资料沿用各自条款；请参阅
。

浏览器会保存对话和课程偏好设置；发送消息时，所选 AI 服务会处理输入。删除本地会话不会删除服务端记录。请使用虚构、非机密的数据，并遵守所选服务的条款。

NVIDIA 隐私政策 ·隐私权利与请求 ·NVIDIA API 试用条款 ·GitHub 托管隐私说明