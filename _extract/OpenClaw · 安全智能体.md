模块 3 · 课时 2 / 3

# OpenClaw 智能体

模块 3a 将浏览器连接到了持久运行时。OpenClaw 是该 NemoClaw 技术栈中的智能体框架 ：它将模型和工具与服务器端会话及文件支持的工作区结合起来。

NemoClaw 提供 Blueprint，将此智能体运行框架与 OpenShell 及部署策略整合。每轮都由 OpenClaw 驱动，并将工作区文件读入当前上下文，无需独立的 Python 编排程序。您将检查这些文件、比较两种消息指令，并从新对话验证文件中的记忆。

*工作区文件提供上下文。编辑后，将下一条回答与保存的文件进行比较。*

**章节**

1. 从智能体视角看工作区
2. 步骤 1 · 让智能体描述自己
3. 步骤 1b · 自行读取工作区
4. 步骤 2 · 比较消息指令
5. 步骤 3 · 智能体编辑自己的上下文
6. 动手试试 · 与实时智能体对话

## 从智能体视角看工作区

该文件夹中的每个文件都会为提示词提供不同部分的内容。这种映射关系是固定的，因此在编辑之前，您就能预判会改变哪项行为。
.openclaw/workspace/

记忆分为两层 。智能体工作时会将原始笔记追加到memory/ 下以日期命名的文件，再把应保留的内容整理到长期记忆MEMORY.md 。默认情况下，MEMORY.md 会纳入主会话的上下文，并从共享或群组提示词中省略。这项上下文选择并不限制文件访问。稍后您将直接从运行中的 sandbox 读取这两种记忆。
询问智能体的提示词包含哪些内容，再在步骤 1b 中将回答与实时工作区对照：

- 当前生效的角色规则，
- 工具列表中的工具，
- 或它记得哪些与您有关的信息。

## 步骤 1 · 让智能体描述自己

下方单元会在一个轮次中，要求 OpenClaw 列出工作区文件并说明各文件的用途。回答反映执行框架纳入提示的内容，以及工具读取的内容。编辑文件后，请将新报告与操作员读回的内容进行比较。

*将智能体对上下文的描述与工作区读回的内容进行比较。仅凭文件已更改，无法确定回答使用了哪些内容。*

与快速入门使用相同的运行时。 这些单元复用 3a 中连接的本地运行时。课程开放的是实例网关，而非内部/v1/chat/completions 路由。如果单元失败或停滞，请先运行 Health check 并检查其证据，再选择恢复操作。本地部署可以使用NemoClaw 设置指南 和相同的网关契约。
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
运行一轮，然后将回答与步骤 1b 中的实时工作区进行比较。

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

**JS javascript · 可编辑 · 107 行**
在您运行前为空

**从 operator 平面验证工作区？**

## 步骤 1b · 自行读取工作区

步骤 1 要求智能体描述 自己的文件，但您不必完全相信它的说法。到目前为止，您唯一的通道是将消息传递给智能体的网关。

本地运行时还提供 operator 终端，也就是位于智能体 sandbox外部 的主机 shell。helpers.terminal() 辅助函数可通过两个入口，直接从本页打开该 shell：

- helpers.terminal("bash") 打开主机的 VM shell，可以在其中运行 openshell sandbox list。
- helpers.terminal("openshell sandbox connect <agent>") 会让您进入智能体运行的沙盒内部，工作区就位于其中。

OpenShell 是容纳智能体的内核级沙盒。目前，可以将它视为 operator 与智能体之间的边界；模块 4 将完整定义并直接测试该边界。连接命令中的智能体名称来自GET /api/agent ，即快速入门页面用于发现本地运行时的同一调用。

下面的单元会连接到沙盒，并从运行中的实例读取三个文件： SOUL.md、每日记忆文件以及整理后的 MEMORY.md。可以随意编辑命令列表并重新运行，以探索任何感兴趣的内容。
打开 本地运行时 的 /ws/terminal WebSocket，无需调用模型即可读取沙箱配置。编辑命令列表以进一步探索。

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

**JS javascript · 可编辑 · 19 行**
在您运行前为空
第一层是终端，它以 sandbox 边界之上的操作员身份运行，可以检查该操作员账户获准访问的文件并列出其 sandbox。智能体位于第二层。它与终端共用同一台机器，但在模块 4 所测试的、更严格的 OpenShell 策略下运行。

## 步骤 2 · 比较消息指令

在两个新会话中提出相同的审查问题。第二个请求会明确要求执行审计人员的证据检查。检查两条提示并比较回答。这会改变消息中的指令，不会修改 SOUL.md，也不会切换到其他角色配置文件。

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

```
if (!state.question) throw new Error("请先运行常规审查");
const courseTurn = helpers.courseTurn;
​
state.out = await courseTurn(state, helpers, "quick-3b-review-" + helpers.randomId(),
  "以审计员的角度审查：找出缺失的证据，并在建议执行前提出问题。" + state.question);
helpers.log("比较请求和回答。只有消息指令发生变化；SOUL.md 未被修改。");
```

**结果流式输出 · 日志 · 返回值尚未运行**

## 步骤 3 · 智能体编辑自己的上下文

让智能体在 MEMORY.md 中追加一项带唯一标签的偏好设置。先通过操作界面读取文件，确认保存的参考码，再在新对话中让智能体读取。仅声称已保存并不足以作为证据。追加的笔记会保留供您检查。

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

```
if (!state.memoryVerified) throw new Error("请先验证文件写入");
const courseTurn = helpers.courseTurn;
​
state.out = await courseTurn(state, helpers, "quick-3b-read-" + helpers.randomId(),
  "读取 MEMORY.md，报告以下标签对应的审查偏好和参考码：" + state.memoryLabel + ".");
if (!state.out.includes(state.memoryReference)) throw new Error("新会话的回答未获取已保存的参考码");
helpers.log("已从新对话中获取经过磁盘验证的参考码。请检查工具事件。");
```

**结果流式输出 · 日志 · 返回值尚未运行**
能够改写工作区上下文的智能体可以影响后续运行。配置的文件系统和网络规则决定了它还能访问哪些资源。请检查当前策略是否允许访问：

- 主机文件系统，
- 更广泛的网络，
- 或相邻智能体的工作区。

下一模块将直接测试这条边界：一个被刻意赋予过高权限的智能体会尝试越过它。

### 参考资料

- NVIDIA, How to Build a Safer Autonomous Agent using OpenClaw。本课程有关 OpenClaw、OpenShell 及此处所用沙盒化智能体架构的配套参考资料。
- Anthropic, Claude Skills (docs)。OpenClaw 使用的“文件即上下文”模式：运行时将一个 Markdown 文件纳入系统提示词后，该文件便会成为可调用的智能体能力。
- Claude Code。生产级 CLI 智能体；可作为实时参考，了解工作区目录、持久记忆和工具界面如何大规模协同工作。
- Packer et al., MemGPT: Towards LLMs as Operating Systems (2023)。本页 MEMORY.md 写入与回忆循环所依据的显式记忆层次结构。
- Model Context Protocol (MCP)。CLI 智能体用于在运行时发现工具而不采用硬编码注册的跨厂商通信格式。
- Landlock LSM。智能体写入自身上下文时，用于限制影响范围的内核文件系统沙盒原语。
- seccomp (man 2)。模块 4 将介绍的内核沙盒系统调用过滤层。

完整列表请参阅深入探索 · 参考资料 。

## 动手试试 · 与实时智能体对话

使用聊天界面检查一个工作区文件。将回答与操作界面读取的内容对比，并检查工具调用。您可以让智能体：

- 描述其工作区，
- 读取文件，
- 或运行命令。

编辑文件后，启动新会话，并检查智能体使用了哪些内容。

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

**JS javascript · 可编辑 · 14 行**
结果呈现在下方。编辑配置后，点击“运行”。

**模型与上下文选项**
与实时智能体对话（请先在快速入门页面连接）。可以让它使用 exec 检查工作区，或读取 SOUL.md。
前提条件：请先在模块 3a 中连接本地运行时，并提供该实例的 URL 和 token。

**AI 辅助内容 · 人工审核**

本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN ·资料来源EN .
课程原创文字、示例代码和原始图表采用
许可。注明名称的外部资料沿用各自条款；请参阅
。

浏览器会保存对话和课程偏好设置；发送消息时，所选 AI 服务会处理输入。删除本地会话不会删除服务端记录。请使用虚构、非机密的数据，并遵守所选服务的条款。

NVIDIA 隐私政策 ·隐私权利与请求 ·NVIDIA API 试用条款 ·GitHub 托管隐私说明