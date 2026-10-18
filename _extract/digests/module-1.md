# 模块 1 · 智能体基础（循环 / ReAct / 工具）

## 01a 智能体

- **一句话主旨**：智能体是"感知—推理—行动"这一持续循环的实体，循环骨架固定不变，只有中间的推理步骤（决策函数）可以被替换。
- **解决的问题**：如何把"推理能力有多强"和"行动能影响多大范围"这两个问题分开——先构建固定的循环框架，再单独替换推理环节，从一条 `if` 语句升级到调用语言模型。
- **关键概念**：
  - 智能体 —— 能够在任何有意义的层面上与环境交互的实体（人、恒温器、自动驾驶汽车皆属此类）。
  - 感知 —— 收集智能体能够获知的信息，是其余环节唯一接触现实的通道。
  - 推理 —— 将感知结果转化为决策；本课程用调用语言模型来完成这一步。
  - 行动 —— 改变环境；暴露给模型的代码被称为工具，调用工具就是以行动方式执行它。
  - `chat()` —— 课程提供的聊天补全封装函数，传入消息列表与模型名，返回助手消息及元数据。
  - `finish_reason` —— 循环的退出条件：`"stop"` 为最终答案、`"tool_calls"` 为请求执行函数、`"length"` 为 token 预算耗尽。
  - `reasoning_content` —— 部分模型与模式返回推理文本的字段，并非必然出现。

- **核心机制/步骤**：
  1. 一维轨道反射式智能体：`Setup` 建环境，`tick` 走一次循环，`run` 重复 `tick` 25 次。环境存 `state.env`（`leftWall: 0`、`rightWall: 9`、`position: 3`），智能体内部状态存 `state.agent`（`direction: +1/-1`）；`tick` 内 `PERCEIVE` 构造 `perception`（`position`、`atLeftWall`、`atRightWall`），`REASON` 用两条 `if` 改方向，`ACT` 执行 `state.env.position += action.move`；`run` 用 `helpers.viz.lineChart` 画位置轨迹。
  2. 保持循环不变，替换推理步骤：同一迷宫求解循环依次装入"始终向东"固定规则、`dfs(pos)`、BFS、A*，最后一节点的一行代码用于选择决策函数。
  3. LLM 版迷宫：先跑引擎节点导出 `state.runMaze`，再由可编辑节点传入 `DIRECTIVE`（系统消息核心）与选项 `model`、`directive`、`advanced`、`includeText`、`includeHistory`、`includeCoords`、`toolSpecInSystem`；控制器自动走走廊，只在岔路口调用模型，模型通过 `choose_direction()` 返回方向，控制器在移动前校验工具名与参数。
  4. 本地绘制循环四阶段：局部采样 → 局部感知（系统提示词 + 累积的 `messages[]` + 先前工具结果 + 新采样） → 局部行动（文本→文本的意图信号，理想为 `{ "move": "east" }` 类型化调用，实际执行靠 `doMove(...)`） → 局部影响。
- **重要结论或陷阱**：感知中的盲区无法由其它环节弥补；行动空间界定能力最外边界；各次 `chat()` 调用不共享状态，对话"记忆"就是代码维护并在每次调用时重新发送的 `messages[]`；Chat Completions API 由代码保存对话，Responses API 由服务器保存线程；模型调用本身不会执行移动，输入模式不保证参数安全，执行前必须校验。
- **交互式演示**：一维轨道反射循环（Setup / tick / run 25 ticks）；迷宫推理器四节点对比固定规则、DFS、BFS、A*；LLM 迷宫运行（引擎 + 可编辑智能体节点）；一次无状态聊天补全的真实调用；手动构造 `POST /v1/chat/completions` 原始 HTTP 请求；`chatStream()` 流式辅助函数；"动手试试 · 比较对话历史"。
- **承上启下**：以 Russell 和 Norvig《Artificial Intelligence: A Modern Approach》的智能体谱系为背景；文末指向"模块 1b：ReAct 循环"，并提到模块 3 的 OpenClaw 网关用另一套协议。

## 01b ReAct 循环

- **一句话主旨**：把语言模型放进那个不变的感知—行动循环，让模型在行动之间用文字推理，就得到 ReAct 模式；循环靠 `finish_reason` 一个字段决定下一步。
- **解决的问题**：通用智能体框架的核心循环到底由什么驱动、何时停止，以及循环变长后理解效果为何下降。
- **关键概念**：
  - ReAct —— Yao et al. (2022) 提出的结合推理与行动的模式，将简短推理轨迹与工具使用交替进行。
  - 工具 —— 运行框架可代模型执行的代码：一个有名称、描述、输入模式和返回值的函数。
  - 工具调用 —— 模型发出的结构化代码执行请求；运行框架解析、执行、追加结果，再调用模型。
  - 运行框架（路由器）—— 维护消息并执行工具，读取 `finish_reason` 决定处理工具请求还是返回答案。
  - 上下文退化 —— 矛盾、过时观察和不良约定积累在提示词历史中，导致下一次决策质量下降的趋势。
- **核心机制/步骤**：
  1. 两次调用对比：第一次不提供工具，第二次提供时钟工具并问当前时间，比较 `finish_reason` 的 `"stop"` / `"tool_calls"` / `"length"` / `"content_filter"` 四个取值。
  2. 从头构建循环：`state.systemPrompt` + `state.userPrompt`；`state.TOOLS` 注册 `get_current_time`（`type: "function"`、`parameters: { type:"object", properties:{}, required:[] }`）；`state.execTool` 执行并返回 `new Date().toISOString()` 格式文本；`while` 循环跑到 `finish_reason === 'stop'`。
  3. 消息数组增长：依次为系统提示词（第 0 轮）、用户问题（第 1 轮）、带 `tool_calls` 字段的 assistant 消息（第 2 轮）、`tool` 角色保存函数返回值的消息（第 3 轮）。
  4. 课程化：用 `read_course_page` 工具 + `MemorySaver` 构建 LangChain `createReactAgent` 聊天面板。
- **重要结论或陷阱**：错误常出在组件之间传递的值——`finish_reason` 错误、`messages` 数组缺一轮、工具执行器返回意外值、路由误读信号；模块彼此独立，可单独替换模型、工具或路由。上下文退化与位置有关（Liu et al. 2023：埋在长上下文中间的信息可能用不上），缓解办法是先制定计划、委派子任务让子智能体在短上下文工作、或在早期轮次成为负担前总结。
- **交互式演示**：`finish_reason` 预览单元（52 行，两次调用对比）；"从头构建完整的 ReAct 循环"三节点（用户输入 / 工具规范 / ReAct 循环）；`createReactAgent` + 实时聊天面板（122 行，可展开来源标签核对实际读取内容）。
- **承上启下**：前一课时为"模块 1a：智能体"，后接"模块 1c：规模化工具使用"；参考资料含 Yao et al. (2022)、Wei et al. Chain-of-Thought、Lilian Weng (2023)、Xu et al. ReWOO、Schick et al. Toolformer（1c 还会再次介绍）。

## 01c 工具的规模化应用

- **一句话主旨**：工具调用的往返约定不变，变的是工具界面——从本地函数扩展到搜索后端、子智能体和 MCP 服务器。
- **解决的问题**：当工具数量变多、每个工具背后能力更强时，模型如何在多个工具间选择、后端如何替换、如何用单一模式封装整个子智能体、如何从独立进程发现工具。
- **关键概念**：
  - 输入模式 —— 描述提供给模型的参数名称、类型及必填字段；不执行工具，也不保证参数安全。
  - `description` —— 说明工具适用场景的字段，是任何使用工具的智能体中影响最显著的提示词工程界面之一。
  - `tool_choice` —— 约束调用的参数，可设为 `"required"` 或特定工具名称。
  - 子智能体作为工具 —— 把专注特定任务的智能体封装在单一模式之后，外层工作流只分派任务，不暴露其全部内部能力。
  - MCP —— Model Context Protocol，为客户端提供发现并调用其它进程所提供工具的标准方法。
- **核心机制/步骤**：
  1. 双工具路由：`state.question` 取自 `EXAMPLES`；`calculate`（仅算术，`parameters.properties.expression`）与 `explain_concept`（仅概念，`properties.concept`）；`helpers.chatStream({ messages, tools:[state.toolA, state.toolB], max_tokens: 8196 })` 后读 `s.tool_calls[0].function.name` 与 `JSON.parse(tc.function.arguments)`。
  2. `glossary_search` 真实往返：`state.SEARCH_SCHEMA`（`required: ["query"]`）→ 调用 #1 带 `tool_choice` 强制搜索 → 校验 `finish_reason` 属于 `["stop","tool_calls"]`、`tool_calls.length === 1`、`tc.id` 有效、`name === "glossary_search"`、`query` 为非空字符串 → `glossaryMCP.request("tools/call", { name, arguments:{ query, limit: 4 } })` → 取 `content[0].text` 与 `structuredContent` 的 `{ results, count, source }` → push assistant 与 `tool` 消息 → 调用 #2 只依据结果作答，并正则清掉 `<tool_call>` 残留。
  3. 换后端：`mountRunCell` 脚本保持模式与循环不变，仅把执行器从"简短说明索引"换成"缓存术语表页面全文"。
  4. 智能体作工具：`state.customers` 六行数据进入子智能体上下文；`state.queryCustomerDB` 用一次 `helpers.chatStream` 回答；主智能体只看到 `query_customer_db`（`required: ["question"]`）。
  5. MCP：`state.mcpServer = window.glossaryMCP`；`tools/list` 把每个 `inputSchema` 映射为 `{ type:"function", function:{ name, description, parameters: t.inputSchema } }`；`tools/call` 分派每个 `tool_call`，逐项校验 id 唯一性、`tc.type === "function"`、必填参数齐全、`string`/`integer` 类型匹配。
- **重要结论或陷阱**：工具名应描述一种能力（`nvidia_glossary_api` 一旦换后端就要改所有提示词，`glossary_search` 则不必）；模型只能看到约定，不知后端是谁，但不同后端判定匹配的方式不同，准确性可能变化；子智能体模式实现的是上下文分离，并未实施数据访问控制，其错误或遗漏会成为外层模型依据；`tools/list` 响应应视为不可信输入，须验证身份、向用户显示能力、授予最小权限、把凭据绑定到对应受众，远程连接与 OAuth 发现要拒绝私有地址和链路本地地址并验证每次重定向（SSRF 控制）。
- **交互式演示**：两工具路由可视化（问题 / 工具 A / 工具 B / LLM 调用四节点）；`glossary_search` 六节点完整往返（含术语表浏览器与 `webSearch`/`instantAnswer` 源码）；同一工具更换全文后端（41 行）；子智能体六节点（数据 / 子智能体 / 工具规范 / 用户问题 / 主智能体 / 分派回答）；MCP 五节点发现与分派；"动手实践"接 `calculate` 与 `glossary_search` 的 `createReactAgent`（37 行）。
- **承上启下**：开篇回指"模块 1b"的工具往返；结尾指向"模块 2a：工作流"，说明模块 2 保留此工具约定并改变外层结构。

## 模块级要点

- **三条主线/递进关系**：
  1. **骨架固定、推理可换（01a）**：先证明感知—推理—行动循环与决策函数解耦，从一条 `if` 换到 DFS/BFS/A*，再换到 `chat()`。
  2. **用 `finish_reason` 驱动循环（01b）**：把"何时继续、何时停止"压缩成一个字段，用 `messages[]` 承担全部记忆，从而把 01a 的循环变成标准 ReAct 循环。
  3. **工具界面的规模化（01c）**：往返约定不动，只扩展模式来源与执行器——多工具、换后端、子智能体、MCP；并在每一层能力边界上补上校验与信任判断。

- **术语表**：
  - 智能体 —— agent
  - 感知 / 推理 / 行动 —— perceive / reason / act
  - 工具 —— tool（`type: "function"`、`function.name`、`function.parameters`）
  - 工具调用 —— `tool_calls`、`tool_call_id`
  - 结束原因 —— `finish_reason`（`"stop"`、`"tool_calls"`、`"length"`、`"content_filter"`）
  - 推理文本 —— `reasoning_content`
  - 消息数组 —— `messages[]`（按系统 / 用户 / 助手 / 工具等角色组织）
  - 聊天封装 / 流式封装 —— `chat()`、`chatStream()`
  - 助手结果字段 —— `content`
  - 运行框架 / 路由器 —— runtime、router
  - 工具选择约束 —— `tool_choice`
  - 输入模式 —— `inputSchema`、`parameters`
  - 环境与智能体状态 —— `state.env`、`state.agent`
  - 迷宫控制器 —— `state.runMaze`、`choose_direction`、`DIRECTIVE`、`doMove(...)`
  - 工具名 —— `get_current_time`、`calculate`、`explain_concept`、`glossary_search`、`glossary_lookup`、`read_course_page`、`query_customer_db`
  - 术语服务 —— `glossaryMCP`、`webSearch`、`instantAnswer`
  - 协议与接口 —— MCP、JSON-RPC、`tools/list`、`tools/call`、Chat Completions API、Responses API
  - 框架与组件 —— `createReactAgent`、`MemorySaver`
  - 上下文问题 —— 上下文退化（context degradation）
  - 安全概念 —— 最小权限范围、SSRF、可信边界

- **"继续学习之前"练习题要点**：
  - 01a-1：设 `includeHistory:false` 用同配置重跑，比较分支顺序、岔路口决策与耗时，注意控制器始终保留已访问单元格与返回路径。
  - 01a-2：删掉 `DIRECTIVE` 中"优先未探索分支而非已访问单元格"那行后重跑并重复多次，看差异是否持续出现。
  - 01a-3：依次换 `model:"direct"`、`"reasoning"`、`"omni"`，检查各请求的模型、token 预算、温度与推理设置，勿把全部差异归因于模型身份。
  - 01b-1：对工具答不了的问题（"法国的首都是哪里？"）观察 `finish_reason` 是 `"stop"` 还是 `"tool_calls"`，再在系统提示词中强制先调用 `get_current_time`，检验提示词指令的引导强度。
  - 01b-2："距离 17:00 UTC 还有多少分钟？"需读时钟并计算，观察模型调用 `get_current_time` 一次、两次还是三次，并思考如何改提示词减少重复调用。
  - 01c-1：模型传入的参数未通过验证时当前循环会崩溃，思考如何妥善处理且不让模型误以为调用已成功。
  - 01c-2：子智能体对主智能体不透明，除答案外还应返回哪些信息以便下一轮判断是否可信。
  - 01c-3：`tool_choice` 可设为 `"required"` 或特定工具名，思考何时应强制执行工具调用及其风险。
  - 01c-4：接入远程 MCP 服务器前应验证身份、能力范围、token 受众与网络目标，并指出哪一项若未经校验会成为 SSRF 路径。
