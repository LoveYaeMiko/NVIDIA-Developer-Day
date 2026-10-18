# 模块 2 · 高级模式（工作流 / 索引智能体 / 深度智能体）

## 02a 工作流智能体

- **一句话主旨**：工作流智能体由执行框架控制工作流，工作流含模型调用、确定性代码步骤、工具调用与专家循环；框架在每个边界决定上下文跨越、分叉与结果传递。
- **解决的问题**：单个 ReAct 循环只适合一次性任务；若下一步须在工具结果返回前确定、子任务可并行并共享结果、或路由按规则而非最近观察决定，就用工作流（如账单核验与账户历史各走分支再汇总证据）。
- **关键概念**：ReAct——每步先读观察再选行动；ReWOO（无观察推理）——工具运行前一次 LLM 调用写完整计划、执行器并行跑完、第二次调用综合；固定枚举——封闭标签列表，越界须拒绝或严格重试；路由——分流后交给一个专用智能体；分发/扇出——同一共享输入同时发给多个专家；工厂——角色、提示词、工具、调用方式参数化。
- **核心机制/步骤**：①ReWOO：Planner（`PLAN_SCHEMA`+`response_format:json_schema` 生成 3–5 个 queries）→ 执行器（纯 JS，`Promise.all` 并发 `helpers.webSearch(q,{maxResults:3})`，无 LLM 调用）→ 综合器（按 `[search N]` 引用）。②路由：`TRIAGE_SCHEMA` 出 `{category,priority,summary}`，枚举 network/hardware/software/account 与 high/medium/low；纯 JS 用 `SPECIALISTS`+`Object.hasOwn` 选提示词。③分发：一次 `helpers.webSearch(...,{maxResults:4})` 共享，`Promise.all` 调度三专家。④工厂：`createSpecialist({role,systemPrompt,tools})`→`run(input,helpers)`，校验 `finish_reason` 为 `stop`/`tool_calls`。
- **重要结论或陷阱**：边界增加延迟与路由逻辑、引入新的消息格式错误来源、把时间线变成分叉轨迹，拆分前先测延迟与质量；`Promise.all` 任一分支被拒即整体被拒；以"目标中途变更即抛错"防陈旧综合；工厂只返回工具请求不执行。
- **交互式演示**：改 `state.goal` 的 ReWOO 术语表并行研究（含工作流图）、工单四枚举路由、共享搜索+三专家并发与甘特图、工厂建算术辅导员与翻译员、动手尝试实时分流路由。
- **承上启下**：B 部分把思路用于语料库，C 部分由 planner 在全新上下文调度子智能体并持久化到虚拟文件系统。

## 02b 索引智能体（RAG）

- **一句话主旨**：索引智能体通过开发者定义的工作流把工作流理念用于外部知识：预先嵌入并索引语料库，检索匹配段落，依据范围受限的上下文包生成答案。
- **解决的问题**：检索须返回回答问题所需的证据，数据结构决定搜索方式；阶梯为仅靠模型作答 → 传统 RAG 每次生成前固定检索 → 智能体控制检索（检索作为工具）；推理 API 不能改权重，故用预训练模型走两阶段：离线建索引、实时请求。
- **关键概念**：上下文包——工作流中传递的一组完整有界上下文，先定数据包再选数据库；MCP——发现和调用外部上下文来源的一种边界，何时检索仍归运行时；检索原语——非结构化文本用稠密向量+交叉编码器重排序，层次文档用带父节点指针的树索引，结构化表格用语义层，图用图遍历（Cypher、GraphQL）；嵌入——定长数值向量，由 `helpers.embed` 生成；top-K 余弦——逐段 `helpers.cosineSim` 排序取前 K；小文本块+父文档——小块嵌入检索、命中返回 FULL 父文档；GraphRAG——LLM 建图、检测社区并摘要，查询时汇总，是 MapReduce 而非相似度查找。
- **核心机制/步骤**：四步：嵌入查询、搜 top-K、拼进提示词、据段落作答。链路：语料库 → 建索引（`helpers.embed(corpus,{model:"nvidia/nemotron-3-embed-1b",inputType:"passage"})`，存 `{text,vector}`）→ 查询以 `inputType:"query"` 嵌入、`cosineSim` 评分排序、`slice(0,3)`；父文档拆句为块保留 `parent`；再封装 `retrieve(question, k)` 工具五步（建内存索引、JSON 模式、模型决定、Top-K 追加、LLM #2 作答）。
- **重要结论或陷阱**：`input_type` 互换会改分数、降低质量却不报错；索引是嵌入缓存，须固定模型 ID（`nvidia/nemotron-3-embed-1b`），防换模型、悄悄升级、混用 ID；Top-K 必返 K 个即使分数都低；换 FAISS+BM25+重排序前验证失败行为。
- **交互式演示**：检查一个嵌入、构建内存向量索引、检索子块返回父文档、把检索公开为工具、Top-K 与 GraphRAG 对比、实时检索（仅问题实时嵌入）。
- **承上启下**：2c 转向答案分散、规模超出单次对话容量的问题。

## 02c 深度智能体

- **一句话主旨**：深度研究智能体把同一思路用于证据规模超出单次对话容量的问题：运行时 planner 选出相互独立的分支，只向工作智能体提供原始问题、分配的任务与所需工具，同级历史不传入，最后由一个阶段综合保留的证据。
- **解决的问题**：单个 ReAct 循环把所有指令与观察留在同一段历史中，早期证据与每项新工具结果争夺注意力：溢出（超出上下文窗口）、上下文退化（相关证据权重不足，Liu et al.）、干扰（一个分支的推理分散下一分支）。
- **关键概念**：工作流边界——索引工作流由开发者定义、接收有界检索资料包；深度研究工作流由 planner 运行时创建分支，两者都可安放 ReAct 循环；规划/调研/保存/综合——拆出独立任务使范围先可检查、子智能体在全新上下文接一项任务、结果写入共享虚拟文件系统使证据在上下文结束后留存、编排器读证据生成可追溯答案；循环转图——`createReactAgent({llm,tools})` 把 ReAct 循环变成显式模型节点与工具节点，图可独立运行或作更大工作流的节点；子智能体——只拿到自己的任务和已保存文件列表。
- **核心机制/步骤**：①`ChatOpenAI` 封装任一同源 OpenAI 兼容入口，从 `helpers.getConfig()` 读 URL 与凭据，`invoke()` 返回 `AIMessage`，`.stream()` 逐步生成，二者都符合 `Runnable`。②用 `tool(fn,{name,description,schema:z.object({})})` 声明 `get_current_time`，编译图后 `agent.invoke()`，以 `helpers.viz.messageList` 呈现轨迹。③`state.vfs = {}` 作内存文件系统，`createWriteFile(dispatch)` 产出 `write_file`（带 dispatch 守卫）、`read_file`、`list_files`；再规划类型化子任务、运行任务范围内的智能体、整合草稿、显示工作流。
- **重要结论或陷阱**：全新上下文不是沙盒——上下文隔离分离分支推理，沙盒限制对操作系统的访问；第三个示例依模型知识撰稿，工作智能体无检索工具或来源，文件存的是草稿而非独立核实的证据，文件名不是独立来源；`deepagents` 包封装类似模式。
- **交互式演示**：深度研究制品（240 行：提出研究问题、多分支并行且各自流式传入可聚焦面板、带引用综合）；连接当前模型；构建 ReAct 图（声明类型化时间工具、编译、检查轨迹）；以保存的草稿构建工作流（共享草稿工具、类型化子任务、运行工作智能体、整合草稿）。
- **承上启下**：本页收尾模块 2，下一节为模块 3a 快速入门；参考资料含 Liu et al.《Lost in the Middle》、LangChain 深度智能体、NVIDIA AI-Q、Kosmos。

## 模块级要点

- **三条主线/递进关系**：02a 确立"执行框架控制边界、数据流与扇出"的骨架（ReWOO 先规划后并发执行、固定枚举路由、共享输入分发、工厂声明专家）；02b 把同一组合思路从"其它智能体"转向"语料库"，让知识层成为通过查询接口封装数据的智能体（上下文包 → 检索原语 → 嵌入 → top-K 余弦 → 小文本块+父文档 → 包成工具 → GraphRAG）；02c 把边界推到超出单次对话容量，控制流从循环升级为图。三者共同点：开发者先定义上下文包与边界，模型只负责边界内该由模型决定的部分。
- **术语表**：
  - 工作流智能体 —— workflow agent；推理与行动 —— ReAct；无观察推理 —— ReWOO
  - 分流 / 路由 —— triage / routing；固定枚举 —— fixed enum（`enum:["network","hardware","software","account"]`）
  - 分发（扇出）—— fan-out；工厂 —— factory（`createSpecialist({role,systemPrompt,tools})`）
  - 术语表搜索 —— `helpers.webSearch`；流式对话 —— `helpers.chatStream`
  - 上下文包 —— context packet；嵌入 —— embedding（`helpers.embed`，`nvidia/nemotron-3-embed-1b`）
  - 余弦相似度 —— `helpers.cosineSim`；top-K —— top-K；父文档 / 文本块 —— parent document / chunk
  - 检索工具 —— `retrieve(question, k)`；社区摘要 —— community summary；全局问题 —— global question
  - 智能体图 —— `createReactAgent({llm,tools})`；虚拟文件系统 —— `state.vfs`（`write_file` / `read_file` / `list_files`）
- **"继续学习之前"练习题要点**：
  - 02a-1：ReWOO 的 planner 看不到工具结果，若后续查询需用前一项结果中的事实就会失效，应切换回 ReAct。
  - 02a-2：枚举之外的类别应拒绝或在更严格指令下重试而非猜测；仅靠 JSON schema 不够，还需应用端验证（如 `Object.hasOwn`）。
  - 02a-3：工厂已参数化角色、系统提示词、工具与调用方式，第五个参数宜为"输入含义模糊时如何守住领域边界"。
  - 02b-1：`input_type` 的非对称性让问题嵌入与能回答它的段落嵌入对齐，提供纯对称余弦方法没有的能力。
  - 02b-2：增删改语料或更换嵌入模型/配置需完整重建索引；新问题只需生成一个新的查询嵌入。
  - 02b-3：Top-K 总会返回 K 个段落即使分数都低，入提示词前应检查相关度得分这一信号。
  - 02c-1：每个子智能体只含原始问题、自己的任务与所需工具，排除其它分支的历史与推理。
  - 02c-2：保存结果使证据在工作智能体上下文结束后仍留存，避免对话记录膨胀带来的溢出与干扰。
  - 02c-3：上下文隔离分离分支推理、防上下文退化与干扰；沙盒限制对操作系统的访问（原文未给出沙盒对应的具体故障类型）。
