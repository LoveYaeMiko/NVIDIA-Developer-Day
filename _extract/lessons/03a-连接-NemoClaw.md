模块 3 · 课时 1 / 3

# 连接 NemoClaw 技术栈

模块 1 和模块 2 中，编排一直在浏览器内进行；一旦页面不再承载消息、中间结果或分支状态，工作流便会结束。模块 3 将相同的智能体模式迁移到本课程提供的本地 NemoClaw 运行时。

此部署主要包含以下功能组件：

- LLM API 入口。将提示词和工具结果转换为语义响应，但不保存智能体的会话状态。
- OpenClaw 运行框架。保留会话历史记录、基于文件的工作区和工具访问权限。
- OpenShell sandbox。限制运行中的智能体可以访问的范围。
- NemoClaw Blueprint。配置 OpenClaw 与 OpenShell，使二者协同工作。

您将在浏览器中比较新的持久 OpenClaw 网关与此前的无状态模型界面，并通过 websocket 传输从本课程页面连接到该会话。您将检查四条连接路径，以一次直接模型调用作为对照，通过网关发送会使用工具的智能体轮次，并验证sessionKey能恢复客户端没有重新发送的历史记录。

*NemoClaw Blueprint 中的运行时角色，改编自 NVIDIA 的 NemoClaw for OpenClaw 工作流。*

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

Jupyter 对同源请求完成身份验证后，GET /api/agent会提供网关 token。无需复制浏览器 Cookie。

连接 NemoClaw

本课程通过这个经过身份验证的来源使用本地 NemoClaw 运行时。

本地同源传输。不需要额外的访问会话。

等待测试。

1. 智能体元数据 /api/agent 待处理 已隐去敏感信息的请求和响应
2. 网关 WebSocket /cli/gateway 待处理 已隐去敏感信息的请求和响应
3. 终端 WebSocket /ws/terminal 待处理 已隐去敏感信息的请求和响应
4. 健康状态 /healthz 待处理 已隐去敏感信息的请求和响应

如果 NemoClaw 检查超时或返回 502。

选择恢复步骤前，先检查失败的路由、Services 状态和运行时日志。仅凭超时或 502 无法确定原因。如果网关仍不可用，请先查看下方的 Recover 单元格及其检查结果，再继续操作。

### 检查全部四条连接路由

连接检查与展示的代码共用一个同源连接。运行可编辑单元，依次测试智能体元数据、网关、终端和运行状况，然后检查已隐藏敏感信息的结果。

以可编辑代码形式查看全部四项连接检查

JS

javascript · 可编辑 · 可重新运行

常规流程请使用上方的探测 UI。此单元会重新运行相同的四项检查，并返回经过脱敏处理的请求和响应。

**▸ 辅助函数位于此单元格的作用域内。点击行可查看其源代码**

**▸ JS javascript · 可编辑 · 18 行**

## 步骤 1 · 建立仅使用模型的对照

上述本地运行时检查证明运行中的技术栈可以访问。在发送智能体轮次前，先通过模块 1 和模块 2 使用的模型路由发起一次直接 Chat Completions 请求。这个对照不涉及 OpenClaw 会话或网关工具，因此步骤 2 可以清楚展示运行框架增加的能力。它不会检查或重新配置本地运行时内的模型。

### 确认直接模型连接

设置卡片会镜像课程主页或模块 1a 中保存的课程模型路由。只有直接探测失败时才需要更改。课程模型路由与本地运行时连接各自使用独立的凭据和状态。

课程模型中继已就绪 凭据保留在课程主机上。

已连接

对话/api/llm/v1

nvidia/nemotron-3.5-lightning-30b-a3b

嵌入/api/llm/v1

nvidia/nemotron-3-embed-1b

**▸ 高级请求处理60 s 超时 · 不重试**

重试涵盖流式传输开始前的网络错误、HTTP 429 和临时 5xx 响应。

探测当前模型 API 入口

仅使用模型的直接对照。可在上方更改已保存的课程路由；此操作不会读取、写入或配置 NemoClaw 本地运行时中的任何值。

需要某个值？请选择该字段旁的 ?，查看其来源和回退值。

**▸ 可选 · 比较直接模型调用延迟**

可选的性能测试会从目录获取符合条件的模型，向每个模型流式发送一条简短提示，并记录到第一个非空内容块、第一段回答及完成所需的时间。这些是直接调用 API 的测量结果，不包含 OpenClaw 网关额外执行的规划、工具或会话处理。

获取匹配的模型

JS

javascript · 可编辑 · 可重新运行

请先运行这个简短的发现请求。它会列出与可编辑前缀匹配的模型；由于修改该筛选条件正是本练习的内容，代码将保持可见。

**▸ 辅助函数位于此单元格的作用域内。点击行可查看其源代码**

**▸ JS javascript · 可编辑 · 34 行**

测量每个模型的 TTFT

JS

javascript · 可编辑 · 可重新运行

**▸ 辅助函数位于此单元格的作用域内。点击行可查看其源代码**

**▸ JS javascript · 可编辑 · 124 行**

## 步骤 2 · 通过网关操作智能体

步骤 1 建立了仅使用模型的对照：一次 Chat CompletionsPOST携带模型、消息和调用方授权信息。OpenClaw 会在本地运行时内调用已配置的模型，但本页面通过另一个接口操作正在运行的智能体。

该图比较的是不同层使用的接口，而不是一条请求路径：

*不同层的三个接口：一次独立的模型 HTTP 请求与响应、运行时内部的 MCP 工具集成，以及连接 OpenClaw 网关的实时 WebSocket。*

- REST（表述性状态转移）。步骤 1 的直接模型对照使用一次独立的 HTTP 请求与响应。API 仍然可以识别调用之间由服务器端保存的状态。
- Model Context Protocol (MCP)。在智能体运行时内部，MCP 对工具和上下文的发现与调用进行标准化。它不承载此浏览器的网关流量。
- OpenClaw 网关。下方练习与 Control UI 使用同一个 /cli/gateway WebSocket。它在浏览器客户端与正在运行的智能体之间传输 JSON-RPC 事件。

### 授权网关

经过身份验证的课程会话可以访问本地运行时。网关 token 可授权对/cli/gateway的 JSON-RPC 调用。

Jupyter 对同源请求完成身份验证后，GET /api/agent会在agent.dashboardUrl中返回网关 token。请将 token 字段留空，由探测工具自动填充。

该 token 具有operator.admin作用域，与 Control UI 拥有相同的权限。借助它，可以：

- models.list 会列出运行时提供的所有模型。
- cron.add 会调度无需您在场即可运行的任务。
- 带有 chat.send 的 sessionKey 会将消息直接送入正在运行的智能体循环。

*chat.send 请求会驱动网关内的循环，会话键让下一次调用能延续记忆。*

### 更改运行时设置前先检查

受支持的 NemoClaw 本地运行时通常会报告tools.toolSearch=false。自定义配置仍可将其启用，因此运行状况检查会先读取实时值，之后 Recover 才会进行任何更改：

- 症状：您请求执行命令后没有收到任何返回，运行过程停滞，随后超时。
- 原因：toolSearch 允许模型通过为桥接器编写代码（tool_search_code · “运行桥接代码”）来访问工具，导致模型在该桥接器上反复循环，而不调用 exec。
- 恢复：运行运行状况检查。如果 toolSearch 已开启且 exec 探测失败，Recover 可以通过 config.patch 将其关闭。清除会话和重启仍需您主动选择。

*正常路径会直接使用 exec。只有实时检查发现 toolSearch 已启用时，Recover 才会更改该设置。*

检测并恢复 · 先做健康检查，再逐级重置

共享 OpenClaw 运行框架的健康检查、条件修复和日志。健康检查会运行命令并读取 toolSearch。仅当 toolSearch 已启用时，恢复操作才会更改它；清除会话和重启是独立的可选操作。运行时日志会在执行停滞时持续读取日志。

**▸ 辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

🩺

健康检查

检查环境状态、toolSearch、卡住的审批以及一条简单命令。HEALTHY 表示无需修复；DEGRADED 会指出接下来要检查的内容。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

🛠

恢复

仅当实时配置已启用 tools.toolSearch 时才将其禁用。默认不清除会话、不重启，因此对健康的可启动实例运行此单元格不会造成破坏性更改。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

📜

运行时日志

持续读取网关/智能体日志（logs.tail），包括模型调用、工具分派、错误和卡顿。当运行停滞但健康检查为绿色时，这是最深入的诊断视图；网关本身不会公开推理过程。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

下方三个单元格依次连接网关、列出模型和计划任务，再发送一轮聊天并显示运行轨迹。请逐行阅读轨迹：

- 每个 ⚙️ 行都表示一次工具调用及其输入参数。
- 每个 ✓/✗ 行都表示该工具的结果。
- 网关不会转发模型的推理过程，因此该输入/输出跟踪记录是您能够查看到的最详细逐步信息。如果运行过程停滞且没有返回结果，请改用上方的 📜 日志单元持续查看运行时日志。

如果聊天失败或达到时限，请检查执行跟踪并运行 Health check。只有当这些结果表明存在配置或会话问题时，才使用 Recover。

网关 · WebSocket 协议分步解析

此处将 Control UI 使用的同一个 /cli/gateway WebSocket 完整展开，依次展示质询/响应握手、一次 JSON-RPC 方法调用，以及一轮流式聊天。

**▸ 辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

🔌

打开网关连接

使用 operator.admin 对 /cli/gateway WebSocket 进行身份验证，并存储 call() 辅助函数，供后续节点复用该连接。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

📋

调用 models.list 和 cron.list

通过已打开的连接进行两次 JSON-RPC 调用：models.list 列出运行时提供的所有模型，cron.list 则报告当前的计划任务。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

💬

发送聊天消息（流式传输）

使用新的 sessionKey 流式执行 chat.send，直至收到 run-end。注释掉的提示词提供了更简单的替代方案。

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

任何能够读取本地运行时环境的人都能读取该 token，而 token 的读取者就是拥有上述所有权限的 operator。模块 4 将把这个便利机制转化为核心安全问题。

## 步骤 3 · 比较对话历史

提供一组新代码，不重复发送代码就让智能体回忆，然后重置该会话并再次询问。重置会移除对话历史，但共享工作区中的文件会保留。这些提示会要求智能体不要将代码写入文件。解读结果前，请先检查事件。

清理操作只会移除此流程创建的会话 ID。单独重新运行回忆步骤，即可再次询问，而不会重新提供代码。

比较重置前后的对话历史

**▸ 辅助函数每个节点内的作用域均包含： state, helpers 点击行可检查并编辑其源代码**

●

提供一条新信息

**▸ JS async (state, helpers) => { … }**

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

●

回忆之前的信息，不重新提供

**▸ JS async (state, helpers) => { … }**

```
if (!state.memorySession) throw new Error("请先在对话中提供一个事实");
const courseTurn = helpers.courseTurn;
state.out = await courseTurn(state, helpers, state.memorySession, "我之前给了你什么代码？如果记录中没有，请回答不知道。不要读取文件。");
helpers.log({recalled: state.out.includes(state.memoryFact)});
```

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

●

重置后再次回忆

**▸ JS async (state, helpers) => { … }**

```
if (!state.memorySession) throw new Error("请先在对话中提供一个事实");
await state.call("sessions.reset", {key:state.memorySession});
const courseTurn = helpers.courseTurn;
state.out = await courseTurn(state, helpers, state.memorySession, "我之前给了你什么代码？如果记录中没有，请回答不知道。不要读取文件。");
helpers.log({recalledAfterReset:state.out.includes(state.memoryFact)});
```

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

●

只移除此流程的会话

**▸ JS async (state, helpers) => { … }**

```
const owned = [...(state.courseOwnedSessions || [])];
for (const key of owned) {
  await state.call("sessions.delete", {key});
  state.courseOwnedSessions = state.courseOwnedSessions.filter(item => item !== key);
}
helpers.log({removed:owned});
```

**▸ 结果流式输出 · 日志 · 返回值尚未运行**

客户端只发送会话键来标识对话。

网关在每次调用前，根据这个字符串在服务器端解析完整会话，因此客户端无需发送对话记录。不同的会话 ID 用于区分对话。网关也可能接受指向同一对话的别名，例如短键及其规范形式

agent:<agent-id>:<key>

## 接下来

模块 3b 将介绍影响 OpenClaw 每轮交互的文件。模块 3c 将添加技能和定时触发器，随后模块 4 将测试 OpenShell 如何限制这些持久指令可以发起的操作。

### 参考资料

- OpenAI Chat Completions API。模型 API 入口所使用的传输格式，包括本页面显示的 finish_reason 字段。
- NVIDIA build.nvidia.com。课程代理服务所使用的模型 API。提供商凭据保留在课程主机上。
- Anthropic， Claude Code（文档）。下一页将编辑这种“以目录作为会话”的模式，从而改变 OpenClaw 的特性。
- Park et al., Generative Agents (2023)。该论文将服务端记忆与身份确立为持久的运行时结构， session-key 标头正是对这一模型的实现。

完整列表请参阅深入探索 · 参考资料。

## 动手试试 · 与您启动的实例对话

上方探测显示绿色后，此交互组件会打开同一个/cli/gatewayWebSocket，让您与实时运行的 OpenClaw 智能体聊天。它会以流式方式显示回复；智能体每次准备使用工具时，界面都会显示一个标签。您在此看到的每条回复都通过该实时网关连接返回。

“动手试试”练习代码

JS

javascript · 可编辑 · 可重新运行

**▸ 辅助函数位于此单元格的作用域内。点击行可查看其源代码**

**▸ JS javascript · 可编辑 · 20 行**

结果呈现在下方。编辑配置后，点击“运行”。

**▸ 模型与上下文选项**

连接上方探测代码中的本地运行时，然后打个招呼，或要求智能体使用 exec 运行 whoami 和 pwd。

前提条件：连接上方探测代码中的本地运行时。保存其 URL 和 token 后，此面板会立即解锁。

← 模块 2c：深度智能体

模块 3b：OpenClaw →

**▸ AI 辅助内容 · 人工审核**

本课程包含 AI 辅助编辑，并经过人工编辑审核。发布内容仍须遵守 NVIDIA 内容管控要求。技术图表和外部媒体的来源及许可记录见图片来源EN·资料来源EN.

Apache-2.0

来源说明EN

NVIDIA 隐私政策·隐私权利与请求·NVIDIA API 试用条款·GitHub 托管隐私说明
