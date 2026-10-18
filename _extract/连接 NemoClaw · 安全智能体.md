模块 3 · 课时 1 / 3

# 连接 NemoClaw 技术栈

模块 1 和模块 2 中，编排一直在浏览器内进行；一旦页面不再承载消息、中间结果或分支状态，工作流便会结束。模块 3 将相同的智能体模式迁移到本课程提供的本地 NemoClaw 运行时。

此部署主要包含以下功能组件：

- LLM API 入口。将提示词和工具结果转换为语义响应，但不保存智能体的会话状态。
- OpenClaw 运行框架。保留会话历史记录、基于文件的工作区和工具访问权限。
- OpenShell sandbox。限制运行中的智能体可以访问的范围。
- NemoClaw Blueprint。配置 OpenClaw 与 OpenShell，使二者协同工作。

您将在浏览器中比较新的持久 OpenClaw 网关与此前的无状态模型界面，并通过 websocket 传输从本课程页面连接到该会话。您将检查四条连接路径，以一次直接模型调用作为对照，通过网关发送会使用工具的智能体轮次，并验证sessionKey 能恢复客户端没有重新发送的历史记录。

*NemoClaw Blueprint 中的运行时角色，改编自 NVIDIA 的 NemoClaw for OpenClaw 工作流。*

**章节**

1. 连接本地运行时
2. 步骤 1 · 建立仅使用模型的对照
3. 步骤 2 · 通过网关操作智能体
4. 步骤 3 · 比较对话历史
5. 接下来
6. 动手试试 · 与您启动的实例对话

## 连接本地运行时

在此配置中：

- LLM 提供语义响应；
- OpenClaw 运行智能体循环、工具、记忆和工作区；
- OpenShell 执行 sandbox 和网络策略；
- NemoClaw 组装并运行整个技术栈。

1. 打开服务，等待 OpenClaw 显示为就绪。
2. 选择下方的测试连接。固定的基础 URL 就是本课程的来源。
3. 检查全部四条路由的结果，然后继续。

Jupyter 对同源请求完成身份验证后，GET /api/agent 会提供网关 token。无需复制浏览器 Cookie。
连接 NemoClaw
本课程通过这个经过身份验证的来源使用本地 NemoClaw 运行时。
本地同源传输。不需要额外的访问会话。
等待测试。

1. 智能体元数据 /api/agent 待处理 已隐去敏感信息的请求和响应
2. 网关 WebSocket /cli/gateway 待处理 已隐去敏感信息的请求和响应
3. 终端 WebSocket /ws/terminal 待处理 已隐去敏感信息的请求和响应
4. 健康状态 /healthz 待处理 已隐去敏感信息的请求和响应
选择恢复步骤前，先检查失败的路由、Services 状态和运行时日志。仅凭超时或 502 无法确定原因。如果网关仍不可用，请先查看下方的 Recover 单元格及其检查结果，再继续操作。

### 检查全部四条连接路由

连接检查与展示的代码共用一个同源连接。运行可编辑单元，依次测试智能体元数据、网关、终端和运行状况，然后检查已隐藏敏感信息的结果。
常规流程请使用上方的探测 UI。此单元会重新运行相同的四项检查，并返回经过脱敏处理的请求和响应。

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

**JS javascript · 可编辑 · 18 行**
在您运行前为空

## 步骤 1 · 建立仅使用模型的对照

上述本地运行时检查证明运行中的技术栈可以访问。在发送智能体轮次前，先通过模块 1 和模块 2 使用的模型路由发起一次直接 Chat Completions 请求。这个对照不涉及 OpenClaw 会话或网关工具，因此步骤 2 可以清楚展示运行框架增加的能力。它不会检查或重新配置本地运行时内的模型。

### 确认直接模型连接

设置卡片会镜像课程主页或模块 1a 中保存的课程模型路由。只有直接探测失败时才需要更改。课程模型路由与本地运行时连接各自使用独立的凭据和状态。

**高级请求处理60 s 超时 · 不重试**

重试涵盖流式传输开始前的网络错误、HTTP 429 和临时 5xx 响应。
探测当前模型 API 入口
仅使用模型的直接对照。可在上方更改已保存的课程路由；此操作不会读取、写入或配置 NemoClaw 本地运行时中的任何值。
需要某个值？请选择该字段旁的 ?，查看其来源和回退值。

**可选 · 比较直接模型调用延迟**

可选的性能测试会从目录获取符合条件的模型，向每个模型流式发送一条简短提示，并记录到第一个非空内容块、第一段回答及完成所需的时间。这些是直接调用 API 的测量结果，不包含 OpenClaw 网关额外执行的规划、工具或会话处理。
请先运行这个简短的发现请求。它会列出与可编辑前缀匹配的模型；由于修改该筛选条件正是本练习的内容，代码将保持可见。

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

**JS javascript · 可编辑 · 34 行**
在您运行前为空

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

**JS javascript · 可编辑 · 124 行**
在您运行前为空

## 步骤 2 · 通过网关操作智能体

步骤 1 建立了仅使用模型的对照：一次 Chat CompletionsPOST 携带模型、消息和调用方授权信息。OpenClaw 会在本地运行时内调用已配置的模型，但本页面通过另一个接口操作正在运行的智能体。

该图比较的是不同层使用的接口，而不是一条请求路径：

*不同层的三个接口：一次独立的模型 HTTP 请求与响应、运行时内部的 MCP 工具集成，以及连接 OpenClaw 网关的实时 WebSocket。*

- REST（表述性状态转移）。步骤 1 的直接模型对照使用一次独立的 HTTP 请求与响应。API 仍然可以识别调用之间由服务器端保存的状态。
- Model Context Protocol (MCP)。在智能体运行时内部，MCP 对工具和上下文的发现与调用进行标准化。它不承载此浏览器的网关流量。
- OpenClaw 网关。下方练习与 Control UI 使用同一个 /cli/gateway WebSocket。它在浏览器客户端与正在运行的智能体之间传输 JSON-RPC 事件。

### 授权网关

经过身份验证的课程会话可以访问本地运行时。网关 token 可授权对/cli/gateway 的 JSON-RPC 调用。

Jupyter 对同源请求完成身份验证后，GET /api/agent 会在agent.dashboardUrl 中返回网关 token。请将 token 字段留空，由探测工具自动填充。

该 token 具有operator.admin 作用域，与 Control UI 拥有相同的权限。借助它，可以：

- models.list 会列出运行时提供的所有模型。
- cron.add 会调度无需您在场即可运行的任务。
- 带有 chat.send 的 sessionKey 会将消息直接送入正在运行的智能体循环。

*chat.send 请求会驱动网关内的循环，会话键让下一次调用能延续记忆。*

### 更改运行时设置前先检查

受支持的 NemoClaw 本地运行时通常会报告tools.toolSearch=false 。自定义配置仍可将其启用，因此运行状况检查会先读取实时值，之后 Recover 才会进行任何更改：

- 症状：您请求执行命令后没有收到任何返回，运行过程停滞，随后超时。
- 原因：toolSearch 允许模型通过为桥接器编写代码（tool_search_code · “运行桥接代码”）来访问工具，导致模型在该桥接器上反复循环，而不调用 exec。
- 恢复：运行运行状况检查。如果 toolSearch 已开启且 exec 探测失败，Recover 可以通过 config.patch 将其关闭。清除会话和重启仍需您主动选择。

*正常路径会直接使用 exec。只有实时检查发现 toolSearch 已启用时，Recover 才会更改该设置。*
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

下方三个单元格依次连接网关、列出模型和计划任务，再发送一轮聊天并显示运行轨迹。请逐行阅读轨迹：

- 每个 ⚙️ 行都表示一次工具调用及其输入参数。
- 每个 ✓/✗ 行都表示该工具的结果。
- 网关不会转发模型的推理过程，因此该输入/输出跟踪记录是您能够查看到的最详细逐步信息。如果运行过程停滞且没有返回结果，请改用上方的 📜 日志单元持续查看运行时日志。

如果聊天失败或达到时限，请检查执行跟踪并运行 Health check。只有当这些结果表明存在配置或会话问题时，才使用 Recover。
此处将 Control UI 使用的同一个 /cli/gateway WebSocket 完整展开，依次展示质询/响应握手、一次 JSON-RPC 方法调用，以及一轮流式聊天。

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

任何能够读取本地运行时环境的人都能读取该 token，而 token 的读取者就是拥有上述所有权限的 operator。模块 4 将把这个便利机制转化为核心安全问题。

## 步骤 3 · 比较对话历史

提供一组新代码，不重复发送代码就让智能体回忆，然后重置该会话并再次询问。重置会移除对话历史，但共享工作区中的文件会保留。这些提示会要求智能体不要将代码写入文件。解读结果前，请先检查事件。

清理操作只会移除此流程创建的会话 ID。单独重新运行回忆步骤，即可再次询问，而不会重新提供代码。

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
if (!state.memorySession) throw new Error("请先在对话中提供一个事实");
const courseTurn = helpers.courseTurn;
​
state.out = await courseTurn(state, helpers, state.memorySession, "我之前给了你什么代码？如果记录中没有，请回答不知道。不要读取文件。");
helpers.log({recalled: state.out.includes(state.memoryFact)});
```

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

```
if (!state.memorySession) throw new Error("请先在对话中提供一个事实");
await state.call("sessions.reset", {key:state.memorySession});
const courseTurn = helpers.courseTurn;
​
state.out = await courseTurn(state, helpers, state.memorySession, "我之前给了你什么代码？如果记录中没有，请回答不知道。不要读取文件。");
helpers.log({recalledAfterReset:state.out.includes(state.memoryFact)});
```

**结果流式输出 · 日志 · 返回值尚未运行**

**JS async (state, helpers) => { … }**

```
const owned = [...(state.courseOwnedSessions || [])];
for (const key of owned) {
  await state.call("sessions.delete", {key});
  state.courseOwnedSessions = state.courseOwnedSessions.filter(item => item !== key);
}
helpers.log({removed:owned});
```

**结果流式输出 · 日志 · 返回值尚未运行**
网关在每次调用前，根据这个字符串在服务器端解析完整会话，因此客户端无需发送对话记录。不同的会话 ID 用于区分对话。网关也可能接受指向同一对话的别名，例如短键及其规范形式
。

## 接下来

模块 3b 将介绍影响 OpenClaw 每轮交互的文件。模块 3c 将添加技能和定时触发器，随后模块 4 将测试 OpenShell 如何限制这些持久指令可以发起的操作。

### 参考资料

- OpenAI Chat Completions API。模型 API 入口所使用的传输格式，包括本页面显示的 finish_reason 字段。
- NVIDIA build.nvidia.com。课程代理服务所使用的模型 API。提供商凭据保留在课程主机上。
- Anthropic， Claude Code（文档）。下一页将编辑这种“以目录作为会话”的模式，从而改变 OpenClaw 的特性。
- Park et al., Generative Agents (2023)。该论文将服务端记忆与身份确立为持久的运行时结构， session-key 标头正是对这一模型的实现。

完整列表请参阅深入探索 · 参考资料 。

## 动手试试 · 与您启动的实例对话

上方探测显示绿色后，此交互组件会打开同一个/cli/gateway WebSocket，让您与实时运行的 OpenClaw 智能体聊天。它会以流式方式显示回复；智能体每次准备使用工具时，界面都会显示一个标签。您在此看到的每条回复都通过该实时网关连接返回。

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

**JS javascript · 可编辑 · 20 行**
结果呈现在下方。编辑配置后，点击“运行”。

**模型与上下文选项**
连接上方探测代码中的本地运行时，然后打个招呼，或要求智能体使用 exec 运行 whoami 和 pwd。
前提条件：连接上方探测代码中的本地运行时。保存其 URL 和 token 后，此面板会立即解锁。

**AI 辅助内容 · 人工审核**

本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN ·资料来源EN .
课程原创文字、示例代码和原始图表采用
许可。注明名称的外部资料沿用各自条款；请参阅
。

浏览器会保存对话和课程偏好设置；发送消息时，所选 AI 服务会处理输入。删除本地会话不会删除服务端记录。请使用虚构、非机密的数据，并遵守所选服务的条款。

NVIDIA 隐私政策 ·隐私权利与请求 ·NVIDIA API 试用条款 ·GitHub 托管隐私说明