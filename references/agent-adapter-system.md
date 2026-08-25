# Agent 适配器系统深度文档

> 对应: agent_adapter/
> 版本: 1.0.0

## 概述

Agent 适配器系统提供通用 Agent 适配器接口，支持多种 Agent 框架。

## 支持的 Agent

| Agent | 版本 | 能力 | 状态 |
|-------|------|------|------|
| Hermes | 0.20.0 | 8 | ✅ |
| OpenClaw | 1.0.0 | 7 | ✅ |
| LangChain | 0.1.0 | 6 | ✅ |
| AutoGPT | 0.1.0 | 6 | ✅ |
| MetaGPT | 0.1.0 | 5 | ✅ |
| CrewAI | 0.1.0 | 5 | ✅ |
| BabyAGI | 0.1.0 | 5 | ✅ |
| AgentGPT | 0.1.0 | 5 | ✅ |

## 核心接口

### MemoryInterface (记忆接口)

```python
class MemoryInterface(ABC):
    def store(key, value) -> bool
    def retrieve(key) -> Any
    def search(query) -> List
    def delete(key) -> bool
    def list_keys() -> List
```

### ContextInterface (上下文接口)

```python
class ContextInterface(ABC):
    def get_messages() -> List
    def add_message(role, content) -> bool
    def get_token_count() -> int
    def clear() -> bool
    def get_last_message() -> Dict
```

### ToolInterface (工具接口)

```python
class ToolInterface(ABC):
    def list_tools() -> List
    def execute(tool_name, args) -> Any
    def register_tool(name, tool) -> bool
    def unregister_tool(name) -> bool
    def get_tool_info(name) -> Dict
```

### ConfigInterface (配置接口)

```python
class ConfigInterface(ABC):
    def get(key, default) -> Any
    def set(key, value) -> bool
    def get_all() -> Dict
    def delete(key) -> bool
    def has(key) -> bool
```

### AgentAdapter (Agent 适配器基类)

```python
class AgentAdapter(ABC):
    def get_name() -> str
    def get_version() -> str
    def get_capabilities() -> List
    def get_memory() -> MemoryInterface
    def get_context() -> ContextInterface
    def get_tools() -> ToolInterface
    def get_config() -> ConfigInterface
    def get_stats() -> Dict
    def is_compatible(required_capabilities) -> bool
```

## 使用方式

### 基本使用

```python
from agent_adapter import get_global_adapter_manager

# 获取管理器
manager = get_global_adapter_manager()

# 列出适配器
adapters = manager.list_adapters()
print(f'适配器: {adapters}')

# 获取当前适配器
current = manager.get_current_adapter()
print(f'当前: {current.get_name()}')

# 检查兼容性
compatible = manager.check_compatibility('hermes', ['terminal', 'memory'])
print(f'兼容: {compatible}')
```

### 获取适配器

```python
from agent_adapter import get_global_adapter_manager

manager = get_global_adapter_manager()

# 获取特定适配器
hermes = manager.get_adapter('hermes')
openclaw = manager.get_adapter('openclaw')

# 使用记忆接口
memory = hermes.get_memory()
memory.store('key', 'value')
value = memory.retrieve('key')

# 使用上下文接口
context = hermes.get_context()
context.add_message('user', 'Hello')
messages = context.get_messages()

# 使用工具接口
tools = hermes.get_tools()
tools.register_tool('echo', lambda x: x)
result = tools.execute('echo', {'x': 'Hello'})

# 使用配置接口
config = hermes.get_config()
config.set('key', 'value')
value = config.get('key')
```

### 兼容性检查

```python
from agent_adapter import get_global_adapter_manager

manager = get_global_adapter_manager()

# 检查兼容性
compatible = manager.check_compatibility('hermes', ['terminal', 'memory'])
if compatible:
    print('Hermes 兼容 terminal 和 memory')
else:
    print('Hermes 不兼容')
```

## 各 Agent 能力对比

| 能力 | Hermes | OpenClaw | LangChain | AutoGPT | MetaGPT | CrewAI | BabyAGI | AgentGPT |
|------|--------|----------|-----------|---------|---------|--------|---------|----------|
| terminal | ✅ | ✅ | | | | | | |
| file_read | ✅ | ✅ | | | | | | |
| file_write | ✅ | ✅ | | | | | | |
| memory | ✅ | ✅ | ✅ | ✅ | | | ✅ | ✅ |
| skill | ✅ | | | | | | | |
| cron | ✅ | | | | | | | |
| delegate | ✅ | | | | | | | |
| browser | ✅ | | | | | | | |
| tool_calling | | ✅ | ✅ | ✅ | ✅ | ✅ | | ✅ |
| planning | | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| reasoning | | ✅ | | ✅ | | | ✅ | |
| chain | | | ✅ | | | | | |
| agent | | | ✅ | | | | | |
| retrieval | | | ✅ | | | | | |
| autonomous | | | | ✅ | | | | ✅ |
| web_search | | | | ✅ | | | | |
| multi_agent | | | | | ✅ | | | |
| role_playing | | | | | ✅ | | | |
| code_generation | | | | | ✅ | | | |
| crew | | | | | | ✅ | | |
| agent_collaboration | | | | | | ✅ | | |
| task_delegation | | | | | | ✅ | | |
| task_creation | | | | | | | ✅ | |
| task_prioritization | | | | | | | ✅ | |
| task_execution | | | | | | | ✅ | |
| goal_oriented | | | | | | | | ✅ |

## 文件结构

```
agent_adapter/
├── __init__.py           # 模块初始化
├── interface.py          # 接口定义
├── registry.py           # 适配器注册表
├── manager.py            # 适配器管理器
└── adapters/
    ├── __init__.py       # 适配器集合
    ├── hermes.py         # Hermes 适配器
    ├── openclaw.py       # OpenClaw 适配器
    ├── langchain.py      # LangChain 适配器
    ├── autogpt.py        # AutoGPT 适配器
    ├── metagpt.py        # MetaGPT 适配器
    ├── crewai.py         # CrewAI 适配器
    ├── babyagi.py        # BabyAGI 适配器
    └── agentgpt.py       # AgentGPT 适配器
```
