# Codex Harness 超级 Skill — 架构设计

> 版本: 1.0.0
> 更新时间: 2026-08-24
> 状态: 阶段 1-4 完成

## 概述

Codex Harness 是一个超级 Skill，让 Hermes Agent 吸收 OpenAI Codex 的能力，从而得到超级增强和进化。

## 核心架构

### 1. 压缩系统 (compression/)

管理对话上下文窗口，当上下文超过 Token 预算时自动触发压缩。

**核心组件:**
- CompressionStrategy — 压缩策略基类
- LocalCompression — 本地 LLM 压缩
- RemoteCompression — 远程 API 压缩
- TokenBudgetCompression — Token 预算压缩
- ModelFallbackCompression — 模型回退压缩
- CompressionManager — 压缩管理器

### 2. 补丁系统 (patch/)

安全地应用代码补丁到文件系统。

**核心组件:**
- PatchAction — 补丁动作类型
- FileChange — 文件变更
- PatchParser — 补丁解析器
- PatchSafetyChecker — 安全检查器
- PatchApplicator — 补丁应用器
- PatchManager — 补丁管理器

### 3. 命令规范化 (canonicalization/)

将命令参数标准化，用于审批缓存匹配。

**核心组件:**
- parse_shell_lc_plain_commands — 解析 shell 命令
- extract_bash_command — 提取 bash 命令
- canonicalize_command_for_approval — 命令规范化
- ApprovalCache — 审批缓存

### 4. 安全检查 (safety/)

评估各种操作的安全性。

**核心组件:**
- SafetyLevel — 安全级别
- SafetyCheck — 安全检查结果
- CommandSafetyChecker — 命令安全检查
- FileSafetyChecker — 文件安全检查
- NetworkSafetyChecker — 网络安全检查
- PatchSafetyChecker — 补丁安全检查
- SafetyManager — 安全管理器

### 5. 记忆提取 (rollout/)

从会话历史中提取结构化记忆。

**核心组件:**
- MemoryType — 记忆类型
- MemoryEntry — 记忆条目
- RolloutExtractor — 记忆提取器
- QualityFilter — 质量过滤器
- MemoryConsolidator — 记忆合并器

### 6. Agent 通信 (communication/)

提供代理间通信能力。

**核心组件:**
- MessageType — 消息类型
- AgentMessage — 代理消息
- MessageBus — 消息总线
- AgentRegistry — 代理注册表
- CommunicationManager — 通信管理器
- TaskCoordinator — 任务协调器

### 7. AGENTS.md 配置 (agents_md/)

解析和管理 AGENTS.md 配置文件。

**核心组件:**
- AgentsMdParser — 解析器
- ConfigExtractor — 配置提取器
- ConfigApplicator — 配置应用器
- AgentsMdConfigManager — 配置管理器

### 8. 连接器 (connectors/)

提供外部应用连接器能力。

**核心组件:**
- Connector — 连接器基类
- ConnectorRegistry — 连接器注册表
- ConnectorManager — 连接器管理器
- ConnectorDiscovery — 连接器发现
- AppBranding — 应用品牌

### 9. 事件映射 (event_mapping/)

定义事件类型和映射规则。

**核心组件:**
- EventType — 事件类型
- Event — 事件
- MappingRule — 映射规则
- EventMapper — 事件映射器

### 10. 函数工具 (function_tool/)

定义和管理函数工具。

**核心组件:**
- ToolDefinition — 工具定义
- FunctionTool — 函数工具基类
- ToolRegistry — 工具注册表
- ToolManager — 工具管理器

### 11. Hook 运行时 (hook_runtime/)

管理 Hook 生命周期和执行。

**核心组件:**
- HookEvent — Hook 事件
- Hook — Hook 基类
- HookRuntime — Hook 运行时

### 12. MCP 协议 (mcp/)

实现 Model Context Protocol。

**核心组件:**
- McpMessage — MCP 消息
- McpTool — MCP 工具
- McpResource — MCP 资源
- McpServer — MCP 服务器基类
- McpClient — MCP 客户端

### 13. Shell 集成 (shell/)

提供 Shell 命令执行和管理能力。

**核心组件:**
- ShellType — Shell 类型
- ShellResult — 执行结果
- ShellSession — Shell 会话
- ShellManager — Shell 管理器

### 14. 技能系统 (skills/)

提供技能加载和执行能力。

**核心组件:**
- SkillDefinition — 技能定义
- Skill — 技能基类
- SkillRegistry — 技能注册表
- SkillManager — 技能管理器

### 15. 线程管理器 (thread_manager/)

管理并发线程和任务。

**核心组件:**
- ThreadTask — 线程任务
- ThreadPool — 线程池
- ThreadManager — 线程管理器

### 16. 引导系统 (elicitation/)

提供用户交互引导能力。

**核心组件:**
- ElicitationType — 引导类型
- ConfirmationElicitation — 确认引导
- ChoiceElicitation — 选择引导
- ElicitationManager — 引导管理器

### 17. 实时系统 (realtime/)

提供实时事件流能力。

**核心组件:**
- RealtimeEventType — 实时事件类型
- RealtimeEvent — 实时事件
- RealtimeChannel — 实时通道
- RealtimeManager — 实时管理器

### 18. 响应系统 (responses/)

提供响应格式化能力。

**核心组件:**
- ResponseType — 响应类型
- Response — 响应
- ResponseBuilder — 响应构建器
- ResponseManager — 响应管理器

### 19. Turn 管理 (turn/)

管理对话 Turn。

**核心组件:**
- TurnStatus — Turn 状态
- Turn — Turn
- TurnManager — Turn 管理器

### 20. Web 搜索 (web_search/)

提供 Web 搜索能力。

**核心组件:**
- SearchResult — 搜索结果
- SearchProvider — 搜索提供者基类
- WebSearchManager — Web 搜索管理器

## 与 Hermes 的集成

### 集成方式

1. **作为独立模块**: 所有模块都是独立的 Python 模块
2. **供 orchestrator.py 调用**: 编排器使用各模块进行工具编排
3. **供 guardian.py 调用**: Guardian 使用安全管理器进行安全检查
4. **供 agent 参考**: SKILL.md 指导 agent 如何使用各模块

### 不会冲突的原因

- 所有模块都是**独立的 Python 模块**
- 它们**不修改** Hermes 的核心工具
- 它们**不拦截** Hermes 的操作
- 它们只是**提供能力**，由 agent 决定是否使用

## 文件结构

```
scripts/
├── compression/          # 压缩系统
├── patch/                # 补丁系统
├── canonicalization/     # 命令规范化
├── safety/               # 安全检查
├── rollout/              # 记忆提取
├── communication/        # Agent 通信
├── agents_md/            # AGENTS.md 配置
├── connectors/           # 连接器
├── event_mapping/        # 事件映射
├── function_tool/        # 函数工具
├── hook_runtime/         # Hook 运行时
├── mcp/                  # MCP 协议
├── shell/                # Shell 集成
├── skills/               # 技能系统
├── thread_manager/       # 线程管理器
├── elicitation/          # 引导系统
├── realtime/             # 实时系统
├── responses/            # 响应系统
├── turn/                 # Turn 管理
├── web_search/           # Web 搜索
├── core.py               # 共享基础库
├── orchestrator.py       # 工具编排器
├── guardian.py           # Guardian 安全
├── context_manager.py    # 上下文管理
├── parallel_executor.py  # 并行执行器
├── hook_engine.py        # Hook 引擎
├── agent_registry.py     # 代理注册表
├── memory_pipeline.py    # 记忆管线
└── config_manager.py     # 配置管理器
```

## 统计

| 项目 | 数量 |
|------|------|
| 模块数 | 20 |
| 文件数 | 64 |
| 总行数 | 13,475 |
| 测试通过率 | 100% |
