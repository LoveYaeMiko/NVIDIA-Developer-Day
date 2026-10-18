# 模块 3 · NemoClaw 设置（连接 / OpenClaw / 持续运行）

## 03a 连接 NemoClaw 技术栈

- **一句话主旨**：把模块 1、2 中"页面一关就结束"的浏览器内编排，迁到本课程提供的本地 NemoClaw 持久运行时，并用四条路由、一次纯模型对照和一串 sessionKey 证明运行框架多做了什么。
- **解决的问题**：浏览器不再承载消息、中间结果或分支状态时工作流即结束。本课时建立同源连接，并区分"直接模型调用"与"经网关驱动持久智能体"两层。
- **关键概念**：
  - LLM API 入口 —— 把提示词和工具结果转成语义响应，但不保存会话状态。
  - OpenClaw 运行框架 —— 保留会话历史、基于文件的工作区和工具访问权限。
  - OpenShell sandbox —— 限制运行中智能体可访问的范围。
  - NemoClaw Blueprint —— 配置 OpenClaw 与 OpenShell 协同工作。
  - 网关 —— 浏览器客户端与运行中智能体之间传输 JSON-RPC 事件的 WebSocket。
  - 四条连接路由 —— `/api/agent`、`/cli/gateway`、`/ws/terminal`、`/healthz`。
  - 对照实验 —— 先用一次直接 Chat Completions 建立"仅使用模型"的基线。
  - sessionKey —— 客户端唯一发送的会话标识，网关据此在服务端解析完整会话。
  - operator.admin —— 网关 token 的作用域，与 Control UI 权限相同。
- **核心机制/步骤**：
  1. 打开服务，等 OpenClaw 显示就绪；选"测试连接"，固定基础 URL 就是本课程来源（本地同源传输，无需额外访问会话）。
  2. Jupyter 对同源请求完成身份验证后，`GET /api/agent` 在 `agent.dashboardUrl` 返回网关 token，无需复制 Cookie；token 留空由探测工具自动填充。
  3. 依次检查四条路由：`/api/agent`、`/cli/gateway`、`/ws/terminal`、`/healthz`，结果已脱敏。
  4. 步骤 1：走 `/api/llm/v1` 发一次直接 Chat Completions（`nvidia/nemotron-3.5-lightning-30b-a3b`、`nvidia/nemotron-3-embed-1b`，60 s 超时、不重试）；可选延迟测试记录 TTFT 与完成时间。
  5. 步骤 2：用 operator.admin 对 `/cli/gateway` 做质询/响应握手并保存 `call()`；调用 `models.list`、`cron.list`；用新 sessionKey 流式 `chat.send` 至 `run-end`；`cron.add` 调度无需在场的任务。
  6. 步骤 3：提供一个事实 → 不重发代码要求回忆 → `sessions.reset` 后再回忆 → `sessions.delete` 只移除本流程会话。
  7. 诊断三件套：健康检查（读 toolSearch 并跑一条命令）、Recover（仅当 `tools.toolSearch` 已启用时用 `config.patch` 关闭）、日志 `logs.tail`。
- **重要结论或陷阱**：
  - 仅凭超时或 502 无法确定原因，先看失败路由、Services 状态与运行时日志。
  - `toolSearch=true` 会让模型在桥接器（`tool_search_code`）上反复循环而不调用 `exec`，表现为无返回、停滞、超时；正常路径直接用 `exec`。
  - 网关不转发推理过程：⚙️ 行是工具调用，✓/✗ 是结果，这是最细粒度的信息。
  - 重置会话清掉对话历史，但工作区文件保留；会话键可有别名，如短键与规范形式 `agent:<agent-id>:<key>`。
  - 能读本地运行时环境的人就能读到该 token，而读取者即拥有全部上述权限的 operator——模块 4 会把这一便利机制变成核心安全问题。
- **交互式演示**：四条路由探测 UI；"获取匹配的模型"与"测量每个模型的 TTFT"两单元；网关协议分步解析（🔌 打开连接、📋 `models.list`/`cron.list`、💬 流式 `chat.send`）；重置前后比较的四节点流程；"动手试试"打开同一个 `/cli/gateway` 与实例聊天，可用 `exec` 跑 `whoami`、`pwd`。
- **承上启下**：3b 介绍影响每轮交互的工作区文件，3c 加技能与定时触发器，模块 4 测试 OpenShell 如何限制这些持久指令能发起的操作。

## 03b OpenClaw 智能体

- **一句话主旨**：OpenClaw 把模型和工具同服务端会话、文件支持的工作区结合，每轮都把工作区文件读进当前上下文，无需独立的 Python 编排程序。
- **解决的问题**：3a 只证明能连上；本课时回答"上下文由什么构成、自述能否核实、消息指令与文件谁起作用"。
- **关键概念**：
  - 工作区视角 —— `.openclaw/workspace/` 下每个文件为提示词提供不同部分，映射固定，编辑前即可预判会改哪项行为。
  - 两层记忆 —— `memory/` 下按日期命名的原始笔记，加上整理后的长期 `MEMORY.md`（默认纳入主会话，共享或群组提示词省略它；此选择不限制文件访问）。
  - operator 终端 —— 位于智能体 sandbox 外部的主机 shell，即 operator 与智能体之间的边界。
  - 两个权限层面 —— 终端以边界之上的操作员身份运行；智能体与之同机，但在更严格的 OpenShell 策略下运行。
- **核心机制/步骤**：
  1. 工作区文件：`SOUL.md`（角色、边界、语气、价值观）、`AGENTS.md`（操作指令和规则）、`IDENTITY.md`（名称、生物设定、风格、表情符号）、`USER.md`（用户身份和偏好）、`TOOLS.md`（各工具使用说明）、`HEARTBEAT.md`（周期性自主任务清单）、`memory/`（如 `2026-06-11.md`）、`MEMORY.md`、`skills/`。
  2. 步骤 1：一个轮次内要求 OpenClaw 列出工作区文件并说明用途；回答只反映框架纳入提示的内容加工具读取的内容。
  3. 步骤 1b：`helpers.terminal("bash")` 打开主机 VM shell 跑 `openshell sandbox list`；`helpers.terminal("openshell sandbox connect <agent>")` 进入沙盒；经 `/ws/terminal` 读取 `SOUL.md`、当日记忆与 `MEMORY.md`（命令列表可编辑）。`<agent>` 来自 `GET /api/agent`。
  4. 步骤 2：两个新会话提同一审查问题，第二个明确"以审计员的角度审查：找出缺失的证据，并在建议执行前提出问题"；只改消息指令，不动 `SOUL.md`、不换角色。
  5. 步骤 3：让智能体在 `MEMORY.md` 追加带唯一标签的偏好 → 先经操作界面确认参考码 → 新会话读取比对，取不到参考码即报错。
- **重要结论或陷阱**：
  - 仅凭"文件已改"或"声称已保存"不能确定回答用了什么，必须把自述与操作员读回的内容对照并检查工具事件。
  - 课程开放的是实例网关，而非内部 `/v1/chat/completions` 路由；失败或停滞先看 Health check 证据。
  - 能改写工作区上下文的智能体可影响后续运行，需检查当前策略是否允许访问主机文件系统、更广泛的网络或相邻智能体工作区。
- **交互式演示**：健康检查 / 恢复 / 运行时日志三节点；"让 OpenClaw 描述其工作区"并可"从 operator 平面验证工作区"；operator 终端读实时工作区；两条审查对比；"保存并验证偏好设置"与"从新对话读取"；"动手试试"可描述工作区、读取文件（如 `SOUL.md`）或运行命令。
- **承上启下**：3c 加技能与触发器，模块 4 直接测试边界：一个被刻意赋予过高权限的智能体会尝试越过它。
- **参考资料**：NVIDIA《How to Build a Safer Autonomous Agent using OpenClaw》；Anthropic Claude Skills（文件即上下文）；Claude Code；MemGPT（显式记忆层次）；MCP；Landlock LSM；seccomp。

## 03c 持续运行的智能体

- **一句话主旨**：心跳、cron 与子智能体让智能体无人值守地开工，技能提供可复用指令；每次运行仍走同一智能体循环与 OpenShell 沙箱。
- **解决问题**：3b 中智能体只在收到消息时运行；本课时说明如何让它按计时器运行，并用证据文件证明写入来自计划任务而非聊天消息。
- **关键概念**：
  - 三个描述参数 —— 会话（继承谁的上下文）、指令（文件或计划消息的要求）、触发器（何时开始）。
  - 技能 —— 复用调用方会话，指令在 `workspace/skills/<name>/SKILL.md`。
  - 心跳 —— 主会话 + `HEARTBEAT.md` + 网关计时器（默认约 30 分钟），仅概念。
  - Cron —— 隔离会话（每次触发新建）+ `payload.message` + 单次计划时间。
  - 子智能体 —— 新建会话、父智能体持句柄，仅概念。
  - 操作手册 —— 随 `SKILL.md` 提供的配套文件，含参考码。
- **核心机制/步骤**：
  1. 安装练习目录：含带 `name`/`description` 前置元数据的 `SKILL.md` 与随附操作手册，重新读取即验证两个文件。
  2. 新对话明确读取技能：指定 `SKILL.md` 路径，处理"checkout-service 已连续 12 分钟返回 502 错误"，报告参考码并给建议，且"不要执行更改，也不要联系任何人"；缺参考码即报错。
  3. 判断是否遵守指令前检查工具事件与建议——这只证明明确指定时可用，不能证明技能会被自动选择。
  4. 步骤 2：调度作业在网关上而非 REST 路由后，故用同一 Control UI WebSocket 通过 `cron.list`、`cron.add`、`cron.remove` 管理；单元装唯一命名任务、最多等三分钟确认执行、验证参考码，再移除自建任务（失败或停止时也移除），清理失败则留任务 ID 重试移除。
  5. cron 按自身计时器触发，课程为演示建隔离会话；若连续性更重要，也可绑定主会话、独立会话、当前会话或指定名称会话。
- **重要结论或陷阱**：
  - 成功的执行记录加内容匹配的新文件，才证明写入由计划任务触发且未发送新消息。
  - 计划指令无论你是否观察都会触发；隔离会话不沿用先前历史，但共享文件仍可能影响后续运行。
  - 任何能写指令、排任务的框架都可能让受入侵指令在对话结束后继续存在；模块 4 区分应用层控制与沙箱控制。
  - 不能因功能同名就认定风险控制相同；Hermes 安全指南介绍配对码与用户允许列表，无匹配规则时采用 `default: deny`。
- **交互式演示**：健康检查 / 恢复 / 运行时日志；"安装并验证练习文件"与"使用已安装的技能"；"计划、验证与清理"与"重试移除创建的任务"。
- **后续应用方向**：Hermes 提供同类能力（可复用技能、持久化记忆、计划任务、消息网关），但实现与默认设置不同，应比较安全边界而非功能名；另有 Voyager、LangGraph Persistence、Anthropic Agent Skills 与 OpenClaw Automation & Tasks 可参考。
- **承上启下**：模块 4a 把文件系统与网络策略同命令证据比较，配置的强制执行机制才决定允许哪些操作。

## 模块级要点

### 三条主线/递进关系

1. **03a 建通道与基线**：迁到本地运行时，四条路由证明连通，纯模型调用做对照，sessionKey 证明记忆在服务端——"连得上、分得清"。
2. **03b 打开黑盒**：进入智能体视角，看清工作区每个文件喂给提示词的哪部分，并用 operator 终端从沙盒外核实自述——"说得对不等于做对了"。
3. **03c 脱离人工**：从消息驱动升级为触发驱动（心跳、cron、子智能体），技能提供可复用指令，用执行记录加参考码区分计划触发与聊天触发。
4. 三者收束到模块 4：能改写上下文、能调度任务的持久智能体，其可发起的操作由 OpenShell 的文件系统、进程与网络策略限制。

### 术语表（中文术语 —— 英文/代码标识符）

- 智能体元数据路由 —— `GET /api/agent`（token 在 `agent.dashboardUrl`）
- 网关 WebSocket —— `/cli/gateway`
- 终端 WebSocket —— `/ws/terminal`
- 健康状态 —— `/healthz`
- 模型路由 —— `/api/llm/v1`
- 网关令牌作用域 —— `operator.admin`
- 会话键 —— `sessionKey`，规范形式 `agent:<agent-id>:<key>`
- 流式聊天 —— `chat.send`（至 `run-end`）
- 列出模型 / 计划任务 —— `models.list`、`cron.list`
- 计划任务增删 —— `cron.add`、`cron.remove`
- 重置 / 删除会话 —— `sessions.reset`、`sessions.delete`
- 配置补丁 —— `config.patch`
- 运行时日志 —— `logs.tail`
- 工具搜索开关 —— `tools.toolSearch`（默认 `false`）、`tool_search_code`
- 操作员终端辅助函数 —— `helpers.terminal()`
- 沙盒列举 / 进入 —— `openshell sandbox list`、`openshell sandbox connect <agent>`
- 工作区根目录 —— `.openclaw/workspace/`
- 工作区文件 —— `SOUL.md`、`AGENTS.md`、`IDENTITY.md`、`USER.md`、`TOOLS.md`、`HEARTBEAT.md`、`MEMORY.md`
- 记忆与技能目录 —— `memory/`、`skills/`、`workspace/skills/<name>/SKILL.md`
- 计划消息正文 —— `payload.message`
- 协议 —— REST、Model Context Protocol (MCP)、JSON-RPC、WebSocket
- 课程模型 —— `nvidia/nemotron-3.5-lightning-30b-a3b`、`nvidia/nemotron-3-embed-1b`
- 运行辅助 —— `helpers.courseTurn`、`helpers.randomId()`、`helpers.log()`、`state.call()`
- 默认拒绝策略 —— `default: deny`

### 原文明确提到的练习题/动手实践要点

1. **03a 连接检查**：运行可编辑单元依次测试四条路由并检查脱敏结果。
2. **03a 模型发现与延迟**：先跑"获取匹配的模型"列出前缀匹配的模型（改筛选条件即练习内容），再"测量每个模型的 TTFT"。
3. **03a 重置对比**：给一组新代码（要求不写文件）→ 不重发要求回忆 → `sessions.reset` 后重问 → 只清理本流程会话。
4. **03a 与实例对话**：探测绿后用同一 `/cli/gateway` 聊天，要求用 `exec` 跑 `whoami`、`pwd`。
5. **03b 自述对照**：问它的提示词包含哪些内容（角色规则、工具列表、记得关于你的信息），再用实时工作区核对。
6. **03b operator 读回**：`openshell sandbox list` 与 `openshell sandbox connect <agent>`，读 `SOUL.md`、当日记忆与 `MEMORY.md`。
7. **03b 指令对比**：两个新会话同一审查问题，第二个加"以审计员的角度审查"要求。
8. **03b 跨会话记忆**：在 `MEMORY.md` 追加唯一标签偏好，操作界面确认参考码后从新对话读取。
9. **03b 动手试试**：让智能体描述工作区、读文件或运行命令；编辑文件后开新会话检查它用了哪些内容。
10. **03c 安装并读取技能**：安装 `SKILL.md` 与操作手册，处理 502 事件并报告参考码。
11. **03c 观察计划写入**：装单次 cron 任务，等三分钟确认执行、验证参考码并清理任务。
12. **03c 在对话中触发技能**：给智能体 `SKILL.md` 路径处理新事件；若要测自动选择就省略路径。
